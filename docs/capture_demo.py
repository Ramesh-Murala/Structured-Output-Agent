import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
DEST = Path(__file__).parent / "assets"
DEST.mkdir(exist_ok=True)
import tempfile

from fastapi.testclient import TestClient

from app.llm.mock_provider import MockProvider
from app.main import app
from app.services.agent import StructuredOutputAgent
from app.services.validation_logger import ValidationLogger

request = {
    "prompt": "Extract John Smith, john@example.com, Python, FastAPI, Docker, AWS, five years experience.",
    "schema_name": "candidate",
    "max_retries": 2,
}
with tempfile.TemporaryDirectory() as tmp, TestClient(app) as client:
    app.state.agent = StructuredOutputAgent(
        provider=MockProvider(), validation_logger=ValidationLogger(Path(tmp) / "failures.jsonl")
    )
    result = client.post("/v1/generate", json=request)
    assert result.status_code == 200 and result.json()["success"]
    response = result.json()

(DEST / "request.json").write_text(json.dumps(request, indent=2) + "\n")
(DEST / "response.json").write_text(json.dumps(response, indent=2) + "\n")
print(json.dumps(response, indent=2))
