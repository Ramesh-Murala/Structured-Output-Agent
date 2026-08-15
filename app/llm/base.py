from abc import ABC, abstractmethod
from typing import Any


class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, json_schema: dict[str, Any]) -> str:
        """Return the model's raw text response."""
