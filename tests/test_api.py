import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.llm.mock_provider import MockProvider
from app.main import app
from app.services.agent import StructuredOutputAgent
from app.services.validation_logger import ValidationLogger


def test_health_endpoint(tmp_path: Path) -> None:
    output = json.dumps(
        {
            "name": "Jane Doe",
            "email": "jane@example.com",
            "skills": ["Python"],
            "years_experience": 3,
        }
    )
    with TestClient(app) as client:
        app.state.agent = StructuredOutputAgent(
            provider=MockProvider([output]),
            validation_logger=ValidationLogger(tmp_path / "failures.jsonl"),
        )
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_generation_endpoint_returns_validated_data(tmp_path: Path) -> None:
    with TestClient(app) as client:
        app.state.agent = StructuredOutputAgent(provider=MockProvider(),
            validation_logger=ValidationLogger(tmp_path / "failures.jsonl"))
        response = client.post("/v1/generate", json={"prompt": "extract", "schema_name": "candidate"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] and data["attempts"] == 2
    assert data["latency_ms"] >= 0


def test_invalid_schema_is_rejected():
    with TestClient(app) as client:
        response = client.post("/v1/generate", json={"prompt": "extract", "schema_name": "unknown"})
    assert response.status_code == 422


def test_provider_error_response_hides_internal_details(tmp_path: Path) -> None:
    class BrokenProvider:
        async def generate(self, prompt, json_schema):
            raise RuntimeError("private upstream diagnostic")
    with TestClient(app) as client:
        app.state.agent = StructuredOutputAgent(provider=BrokenProvider(),
            validation_logger=ValidationLogger(tmp_path / "failures.jsonl"))
        response = client.post("/v1/generate", json={"prompt": "extract", "schema_name": "candidate"})
    assert response.status_code == 503
    assert "private" not in response.text


def test_provider_timeout_response(tmp_path: Path) -> None:
    class TimedOutProvider:
        async def generate(self, prompt, json_schema):
            raise TimeoutError()
    with TestClient(app) as client:
        app.state.agent = StructuredOutputAgent(provider=TimedOutProvider(),
            validation_logger=ValidationLogger(tmp_path / "failures.jsonl"))
        response = client.post("/v1/generate", json={"prompt": "extract", "schema_name": "candidate"})
    assert response.status_code == 504
