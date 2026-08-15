import json
from pathlib import Path

import pytest

from app.llm.mock_provider import MockProvider
from app.services.agent import StructuredOutputAgent
from app.services.validation_logger import ValidationLogger


@pytest.mark.asyncio
async def test_valid_output_succeeds_first_attempt(tmp_path: Path) -> None:
    output = json.dumps(
        {
            "name": "Jane Doe",
            "email": "jane@example.com",
            "skills": ["Python", "FastAPI"],
            "years_experience": 4.0,
        }
    )
    agent = StructuredOutputAgent(
        provider=MockProvider([output]),
        validation_logger=ValidationLogger(tmp_path / "failures.jsonl"),
    )

    result = await agent.run(prompt="extract", schema_name="candidate", max_retries=2)

    assert result.success is True
    assert result.attempts == 1
    assert result.validation_failures == []
    assert result.data["email"] == "jane@example.com"


@pytest.mark.asyncio
async def test_invalid_output_is_retried_and_corrected(tmp_path: Path) -> None:
    bad = json.dumps(
        {
            "name": "Jane Doe",
            "email": "not-an-email",
            "skills": "Python",
            "years_experience": -1,
        }
    )
    good = json.dumps(
        {
            "name": "Jane Doe",
            "email": "jane@example.com",
            "skills": ["Python"],
            "years_experience": 4,
        }
    )
    log_path = tmp_path / "failures.jsonl"
    agent = StructuredOutputAgent(
        provider=MockProvider([bad, good]),
        validation_logger=ValidationLogger(log_path),
    )

    result = await agent.run(prompt="extract", schema_name="candidate", max_retries=2)

    assert result.success is True
    assert result.attempts == 2
    assert len(result.validation_failures) == 1
    assert result.validation_failures[0].error_type == "pydantic_validation_error"
    assert log_path.exists()
    assert len(log_path.read_text(encoding="utf-8").splitlines()) == 1


@pytest.mark.asyncio
async def test_parse_error_then_retry(tmp_path: Path) -> None:
    good = json.dumps(
        {
            "category": "technical",
            "priority": "high",
            "summary": "Customer cannot sign in to the dashboard.",
            "requires_human": True,
            "sentiment": "negative",
        }
    )
    agent = StructuredOutputAgent(
        provider=MockProvider(["not-json", good]),
        validation_logger=ValidationLogger(tmp_path / "failures.jsonl"),
    )

    result = await agent.run(prompt="classify", schema_name="support_ticket", max_retries=1)

    assert result.success is True
    assert result.attempts == 2
    assert result.validation_failures[0].error_type == "json_parse_error"


@pytest.mark.asyncio
async def test_returns_failure_after_retries_exhausted(tmp_path: Path) -> None:
    agent = StructuredOutputAgent(
        provider=MockProvider(["bad", "still bad"]),
        validation_logger=ValidationLogger(tmp_path / "failures.jsonl"),
    )

    result = await agent.run(prompt="extract", schema_name="candidate", max_retries=1)

    assert result.success is False
    assert result.attempts == 2
    assert len(result.validation_failures) == 2
    assert result.data is None
    assert result.raw_output == "still bad"
