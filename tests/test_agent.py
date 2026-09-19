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
    assert result.raw_output is None


@pytest.mark.asyncio
async def test_failure_log_does_not_persist_personal_data(tmp_path: Path) -> None:
    output = json.dumps({"name": "Sensitive Person", "email": "private-invalid-address",
                         "skills": ["Python"], "years_experience": -1})
    path = tmp_path / "failures.jsonl"
    agent = StructuredOutputAgent(provider=MockProvider([output]), validation_logger=ValidationLogger(path))
    result = await agent.run(prompt="extract", schema_name="candidate", max_retries=0)
    log = path.read_text()
    assert "Sensitive Person" not in log
    assert "private-invalid-address" not in log
    assert "raw_output" not in log
    assert result.raw_output is None
    assert all("input" not in detail for detail in result.validation_failures[0].details)


@pytest.mark.asyncio
async def test_generation_deadline_cancels_slow_provider(tmp_path: Path) -> None:
    import asyncio

    class SlowProvider:
        async def generate(self, prompt, json_schema):
            await asyncio.sleep(10)
            return "{}"

    agent = StructuredOutputAgent(provider=SlowProvider(),
                                 validation_logger=ValidationLogger(tmp_path / "failures.jsonl"),
                                 request_timeout_seconds=0.01)
    with pytest.raises(TimeoutError):
        await agent.run(prompt="extract", schema_name="candidate", max_retries=2)


@pytest.mark.asyncio
async def test_provider_error_is_not_retried_as_validation_failure(tmp_path: Path) -> None:
    class BrokenProvider:
        calls = 0
        async def generate(self, prompt, json_schema):
            self.calls += 1
            raise RuntimeError("unavailable")

    provider = BrokenProvider()
    agent = StructuredOutputAgent(provider=provider, validation_logger=ValidationLogger(tmp_path / "failures.jsonl"))
    with pytest.raises(RuntimeError):
        await agent.run(prompt="extract", schema_name="candidate", max_retries=2)
    assert provider.calls == 1
