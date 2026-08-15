import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.llm.mock_provider import MockProvider
from app.services.agent import StructuredOutputAgent
from app.services.validation_logger import ValidationLogger


async def main() -> None:
    invalid = '{"name":"Jane","email":"bad","skills":"Python","years_experience":4}'
    corrected = json.dumps(
        {
            "name": "Jane",
            "email": "jane@example.com",
            "skills": ["Python"],
            "years_experience": 4,
        }
    )
    agent = StructuredOutputAgent(
        MockProvider([invalid, corrected]),
        ValidationLogger(Path("logs/demo_failures.jsonl")),
    )
    result = await agent.run(
        prompt="Extract candidate details.",
        schema_name="candidate",
        max_retries=2,
    )
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())
