from typing import Any, Literal

from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=20_000)
    schema_name: Literal["candidate", "support_ticket", "product"]
    max_retries: int | None = Field(default=None, ge=0, le=10)


class ValidationFailure(BaseModel):
    attempt: int
    error_type: str
    details: list[dict[str, Any]]


class GenerateResponse(BaseModel):
    success: bool
    schema_name: str
    attempts: int
    validation_failures: list[ValidationFailure]
    data: dict[str, Any] | None
    raw_output: str | None = None  # Deprecated: retained as null for response compatibility.
    latency_ms: float = Field(default=0, ge=0)


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    service: str
