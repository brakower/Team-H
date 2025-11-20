from typing import List, Type, TypeVar, Annotated
import os
import logging
import traceback
import re
import json
import uuid
from fastapi import Depends
from pydantic import BaseModel
from models.tool_schema import ToolSchema
from openai import AzureOpenAI

from dotenv import load_dotenv
from pathlib import Path

# Explicitly load the .env file from the project root
env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=env_path)

API_KEY = os.getenv("UNC_OPENAI_API_KEY")
API_VERSION = os.getenv("UNC_OPENAI_API_VERSION", "2024-10-21")
API_ENDPOINT = os.getenv("UNC_OPENAI_API_ENDPOINT", "https://azureaiapi.cloud.unc.edu")

T = TypeVar("T", bound=BaseModel)


def openai_client():
    """Provide a reusable Azure OpenAI client."""
    return AzureOpenAI(
        api_version=API_VERSION,
        azure_endpoint=API_ENDPOINT,
        api_key=API_KEY,
    )


class OpenAIService:
    _model: str = os.getenv("UNC_OPENAI_MODEL", "gpt-5")

    def __init__(self, client: Annotated[AzureOpenAI, Depends(openai_client)]):
        self._client = client

    def prompt(
        self,
        available_tools: List[ToolSchema],
        system_prompt: str,
        user_prompt: str,
        response_model: Type[T],
    ) -> T:
        """Send a prompt to Azure OpenAI and parse JSON response into the given model."""
        print(f"API-----> {API_KEY, API_ENDPOINT}")
        try:
            completion = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )

            content = completion.choices[0].message.content
            parsed = response_model.model_validate_json(content)
            return parsed

        except Exception as e:
            # Print traceback for immediate debugging (preserve previous behavior),
            # then proceed with lightweight logging and best-effort extraction.
            traceback.print_exc()

            # Lightweight logging for debugging LLM parsing failures.
            # Generate a short correlation id to find the log entry.
            log_id = uuid.uuid4().hex[:8]
            logger = logging.getLogger(__name__)

            # Try to capture the raw content if available; fall back to empty string.
            raw = None
            try:
                raw = completion.choices[0].message.content
            except Exception:
                raw = ""

            # Sanitise and truncate the raw output for safe logging.
            sanitized = (raw or "").replace("\n", " ").strip()
            truncated = sanitized[:2000]

            # First, try a best-effort extraction of JSON if the model returned extra text.
            def _extract_first_json_object(text: str) -> str | None:
                """Find the first balanced JSON object in text and return it as a substring.

                This scans from the first '{' and finds the matching closing '}' taking
                string quoting and escapes into account. Returns None if no balanced
                object is found.
                """
                if not text:
                    return None
                # remove common markdown fences
                t = re.sub(r"```(?:json)?", "", text, flags=re.I).strip()
                # find first '{'
                start = t.find('{')
                if start == -1:
                    return None
                i = start
                depth = 0
                in_string = False
                escape = False
                while i < len(t):
                    ch = t[i]
                    if escape:
                        escape = False
                    elif ch == '\\':
                        escape = True
                    elif ch == '"':
                        in_string = not in_string
                    elif not in_string:
                        if ch == '{':
                            depth += 1
                        elif ch == '}':
                            depth -= 1
                            if depth == 0:
                                return t[start:i+1]
                    i += 1
                return None

            try:
                # Find all balanced JSON-like candidates (objects or arrays) in the text.
                def _find_all_balanced_json(text: str) -> list:
                    results = []
                    if not text:
                        return results
                    t = text
                    i = 0
                    while i < len(t):
                        if t[i] not in '{[':
                            i += 1
                            continue
                        start = i
                        open_char = t[i]
                        close_char = '}' if open_char == '{' else ']'
                        depth = 0
                        in_string = False
                        escape = False
                        j = i
                        while j < len(t):
                            ch = t[j]
                            if escape:
                                escape = False
                            elif ch == '\\':
                                escape = True
                            elif ch == '"':
                                in_string = not in_string
                            elif not in_string:
                                if ch == open_char:
                                    depth += 1
                                elif ch == close_char:
                                    depth -= 1
                                    if depth == 0:
                                        results.append(t[start:j+1])
                                        i = j
                                        break
                            j += 1
                        i += 1
                    return results

                candidates = _find_all_balanced_json(sanitized)
                # If nothing was found, fall back to the single-object extractor
                if not candidates:
                    first = _extract_first_json_object(sanitized)
                    if first:
                        candidates = [first]

                # Heuristics: prefer candidates that contain keys likely in the response model
                preferred_keys = [b'tool', b'tool_input', b'summary', b'breakdown', b'total_score']

                def _score_candidate_bytes(s: str) -> int:
                    sb = s.encode('utf-8', errors='ignore')
                    score = 0
                    for k in preferred_keys:
                        if k in sb:
                            score += 1
                    return score

                # Sort candidates by heuristic score (higher first)
                candidates = sorted(candidates, key=lambda c: -_score_candidate_bytes(c))

                for candidate in candidates:
                    obj = None
                    # Try strict JSON first
                    try:
                        obj = json.loads(candidate)
                    except Exception:
                        # Attempt to fix common JSON issues: trailing commas
                        try:
                            fixed = re.sub(r",\s*(?=[}\]])", "", candidate)
                            obj = json.loads(fixed)
                        except Exception:
                            obj = None
                    # single-quote fallback
                    if obj is None:
                        try:
                            obj = json.loads(candidate.replace("'", '"'))
                        except Exception:
                            obj = None
                    # backslash fixes
                    if obj is None:
                        try:
                            backslash_fixed = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', candidate)
                            try:
                                obj = json.loads(backslash_fixed)
                            except Exception:
                                try:
                                    obj = json.loads(backslash_fixed.replace("'", '"'))
                                except Exception:
                                    obj = None
                        except Exception:
                            obj = None

                    if obj is not None:
                        try:
                            parsed = response_model.model_validate(obj)
                            logger.info("Recovered JSON from LLM output (log_id=%s)", log_id)
                            return parsed
                        except Exception:
                            # not a valid model instance, try next candidate
                            continue
            except Exception:
                # ignore extraction errors and continue to final logging
                pass

            # Log warning with correlation id and truncated raw content for debugging.
            logger.warning(
                "LLM parse failed (log_id=%s). Raw output (truncated 1000 chars): %s",
                log_id,
                truncated,
            )

            # Raise a clearer error including the log id so it's easy to find the raw content.
            raise RuntimeError(
                f"Failed to parse LLM response into {response_model.__name__} (log_id={log_id})"
            ) from e