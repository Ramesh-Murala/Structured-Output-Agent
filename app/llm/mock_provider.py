import json
from collections.abc import Iterable
from typing import Any

from app.llm.base import LLMProvider


class MockProvider(LLMProvider):
    """Deterministic provider used in unit tests and local demos."""

    def __init__(self, outputs: Iterable[str] | None = None) -> None:
        self.outputs = iter(
            outputs
            or [
                # First response: intentionally invalid
                json.dumps(
                    {
                        "name": "John Smith",
                        "email": "NOT-A-VALID-EMAIL",
                        "skills": "Python",
                        "years_experience": "five",
                    }
                ),
                # Second response: corrected
                json.dumps(
                    {
                        "name": "John Smith",
                        "email": "john@example.com",
                        "skills": ["Python", "FastAPI", "Docker", "AWS"],
                        "years_experience": 5.0,
                    }
                ),
            ]
        )

    async def generate(self, prompt: str, json_schema: dict[str, Any]) -> str:
        del prompt, json_schema

        try:
            return next(self.outputs)
        except StopIteration as exc:
            raise RuntimeError(
                "MockProvider ran out of configured outputs"
            ) from exc