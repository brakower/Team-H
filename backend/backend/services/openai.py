from typing import List, Type, TypeVar, Annotated
import os
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
            import traceback
            traceback.print_exc()
            raise