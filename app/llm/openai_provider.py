import json
from typing import Any

from openai import APIError, AsyncOpenAI

from app.llm.base import LLMProvider


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str) -> None:
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    async def generate(self, prompt: str, json_schema: dict[str, Any]) -> str:
        instructions = (
            "Return only one valid JSON object. Do not include markdown fences or commentary. "
            "The JSON must satisfy this schema exactly:\n"
            f"{json.dumps(json_schema, ensure_ascii=False)}"
        )
        try:
            response = await self.client.responses.create(
                model=self.model,
                instructions=instructions,
                input=prompt,
            )
        except APIError as exc:
            raise RuntimeError("Generation provider unavailable") from exc
        return response.output_text
