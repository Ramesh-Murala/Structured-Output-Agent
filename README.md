# Structured Output Agent

A production-style reliability layer for LLM applications that **enforces Pydantic schemas, validates model output, retries malformed responses, and logs validation failures for observability**.

## Why this project exists

LLMs are probabilistic. Production APIs are not.

A model can return malformed JSON, wrong field types, invalid enum values, missing fields, or data that violates business constraints. Structured Output Agent wraps an LLM call with deterministic application-level validation and retry behavior so downstream systems receive predictable data.

## Core capabilities

- Pydantic v2 schema enforcement
- JSON parsing and top-level object checks
- Automatic retry after parse or validation failures
- Validation errors fed back into the retry prompt
- JSONL failure logging for debugging and observability
- Configurable retry budget
- FastAPI REST API with OpenAPI/Swagger docs
- Provider abstraction with OpenAI and deterministic mock providers
- Unit tests for valid, malformed, recoverable, and exhausted-retry cases
- Docker and Docker Compose support

## Architecture

```text
Client
  |
  v
FastAPI /v1/generate
  |
  v
Schema Registry -----> Pydantic JSON Schema
  |                         |
  |                         v
  +--------------------> LLM Provider
                            |
                            v
                       Raw model text
                            |
                            v
                       JSON parser
                            |
                            v
                     Pydantic validator
                       /          \
                    valid        invalid
                     |              |
                     v              v
                API response   failure logger
                                    |
                                    v
                              retry prompt
                                    |
                                    +----> LLM
```

## Project structure

```text
structured-output-agent/
├── app/
│   ├── api/routes.py
│   ├── core/config.py
│   ├── core/logging.py
│   ├── llm/base.py
│   ├── llm/factory.py
│   ├── llm/mock_provider.py
│   ├── llm/openai_provider.py
│   ├── schemas/api.py
│   ├── schemas/domain.py
│   ├── schemas/registry.py
│   ├── services/agent.py
│   ├── services/json_parser.py
│   ├── services/retry_prompt.py
│   ├── services/validation_logger.py
│   └── main.py
├── examples/
├── logs/
├── scripts/
├── tests/
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── pyproject.toml
├── requirements.txt
└── requirements-dev.txt
```

## Quick start

### 1. Create a virtual environment

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements-dev.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Add your OpenAI API key to `.env`:

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-5-mini
MAX_RETRIES=2
```

### 4. Start the API

```bash
uvicorn app.main:app --reload
```

Open Swagger UI at:

```text
http://127.0.0.1:8000/docs
```

## API usage

### Health check

```bash
curl http://127.0.0.1:8000/health
```

### Generate validated candidate data

```bash
curl -X POST http://127.0.0.1:8000/v1/generate \
  -H "Content-Type: application/json" \
  -d @examples/candidate_request.json
```

Example successful response:

```json
{
  "success": true,
  "schema_name": "candidate",
  "attempts": 2,
  "validation_failures": [
    {
      "attempt": 1,
      "error_type": "pydantic_validation_error",
      "details": []
    }
  ],
  "data": {
    "name": "Jane Doe",
    "email": "jane@example.com",
    "skills": ["Python", "FastAPI"],
    "years_experience": 4.0
  },
  "raw_output": null
}
```

## Included schemas

### Candidate

```json
{
  "name": "Jane Doe",
  "email": "jane@example.com",
  "skills": ["Python", "FastAPI"],
  "years_experience": 4.0
}
```

### Support ticket

```json
{
  "category": "technical",
  "priority": "high",
  "summary": "User is unable to access the account.",
  "requires_human": true,
  "sentiment": "negative"
}
```

### Product

```json
{
  "name": "Wireless Keyboard",
  "price": 89.99,
  "currency": "USD",
  "in_stock": true,
  "product_url": "https://example.com/keyboard"
}
```

## Retry behavior

For every generation attempt, the agent performs two checks:

1. Parse the response as a JSON object.
2. Validate the parsed object against the selected Pydantic model.

If either check fails, the agent records the failure and constructs a new prompt containing the previous response and structured validation errors. It repeats the process until the response validates or the retry budget is exhausted.

## Validation logs

Failures are written as JSON Lines to:

```text
logs/validation_failures.jsonl
```

Example record:

```json
{
  "timestamp": "2026-08-14T22:00:00+00:00",
  "schema_name": "candidate",
  "attempt": 1,
  "error_type": "pydantic_validation_error",
  "details": [{"type": "value_error", "loc": ["email"]}],
  "raw_output": "{...}"
}
```

The log file is intentionally excluded from Git while the `logs/` directory is retained.

## Run the deterministic demo

The demo intentionally produces an invalid first response and a valid second response, proving that retry logic works without calling an external API.

```bash
python scripts/demo.py
```

## Tests

```bash
pytest -q
```

The test suite covers:

- valid output on the first attempt
- malformed JSON
- Pydantic validation failure
- retry and successful correction
- retry exhaustion
- health endpoint

## Linting

```bash
ruff check .
```

## Docker

```bash
docker compose up --build
```

Then open:

```text
http://127.0.0.1:8000/docs
```

## Adding a new schema

Create a Pydantic model in `app/schemas/domain.py`:

```python
class Invoice(BaseModel):
    invoice_id: str
    amount: float
    paid: bool
```

Then register it in `app/schemas/registry.py` and add the schema name to the API request model.

## Design decisions

**Why validate outside the LLM provider?** Provider-native structured output is useful, but application-level validation remains valuable for portability, business constraints, testing, and defense in depth.

**Why log raw invalid output?** It makes failure patterns diagnosable. In a real production environment, sensitive data should be redacted before persistence.

**Why JSONL?** It is simple, append-only, grep-friendly, and easy to ingest later into CloudWatch, ELK, Datadog, or another observability pipeline.

**Why a provider abstraction?** Validation and retry logic should not depend on a specific model vendor.

## Production improvements

Potential next iterations:

- provider-native strict JSON-schema output
- exponential backoff for transient API failures
- async concurrency limits
- token, latency, and retry metrics
- Prometheus/OpenTelemetry instrumentation
- PII redaction before failure logging
- persistent storage for evaluation runs
- dynamic user-supplied JSON Schema support
- authentication and rate limiting
- evaluation harness comparing raw LLM output with validated output
- CI workflow for linting and tests

## Security notes

- Never commit `.env` or API keys.
- Avoid logging sensitive production prompts or outputs without redaction.
- Add authentication before exposing this API publicly.
- Apply rate limits and request-size limits in production.

## Tech stack

- Python 3.11+
- Pydantic v2
- FastAPI
- OpenAI Python SDK
- pytest
- Ruff
- Docker

## License

MIT
