from typing import List, Type, TypeVar, Annotated
import os
import logging
import traceback
import re
import json
import uuid
from fastapi import Depends
from pydantic import BaseModel
from backend.models.tool_schema import ToolSchema
from openai import AzureOpenAI

from dotenv import load_dotenv
from pathlib import Path

# Explicitly load the .env file from the project root
env_path = Path(__file__).resolve().parents[2] / ".env"
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
    _model: str = os.getenv("UNC_OPENAI_MODEL", "gpt-4o-mini")

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
            try:
                # Remove common markdown fences
                cleaned = re.sub(r"```(?:json)?", "", sanitized, flags=re.I).strip()
                # Extract the first {...} block
                m = re.search(r"(\{.*\})", cleaned, flags=re.S)
                if m:
                    try:
                        obj = json.loads(m.group(1))
                        parsed = response_model.model_validate(obj)
                        # Log that we recovered a parse and return the parsed model
                        logger.info("Recovered JSON from LLM output (log_id=%s)", log_id)
                        return parsed
                    except Exception:
                        # fall through to logging below
                        pass
            except Exception:
                # ignore best-effort extraction errors
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