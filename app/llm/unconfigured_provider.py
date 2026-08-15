from typing import Any

from app.llm.base import LLMProvider


class UnconfiguredProvider(LLMProvider):
    def __init__(self, message: str) -> None:
        self.message = message

    async def generate(self, prompt: str, json_schema: dict[str, Any]) -> str:
        del prompt, json_schema
        raise RuntimeError(self.message)
