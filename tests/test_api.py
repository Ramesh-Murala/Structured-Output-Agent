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
