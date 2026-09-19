import asyncio
import logging
from time import perf_counter
from typing import Any

from pydantic import BaseModel, ValidationError

from app.llm.base import LLMProvider
from app.schemas.api import GenerateResponse, ValidationFailure
from app.schemas.registry import get_schema
from app.services.json_parser import JSONParseError, parse_json_object
from app.services.retry_prompt import build_retry_prompt
from app.services.validation_logger import ValidationLogger

logger = logging.getLogger(__name__)


class StructuredOutputAgent:
    def __init__(
        self, provider: LLMProvider, validation_logger: ValidationLogger,
        request_timeout_seconds: float = 30.0,
    ) -> None:
        if request_timeout_seconds <= 0:
            raise ValueError("request_timeout_seconds must be positive")
        self.request_timeout_seconds = request_timeout_seconds
        self.provider = provider
        self.validation_logger = validation_logger

    async def run(
        self,
        *,
        prompt: str,
        schema_name: str,
        max_retries: int,
    ) -> GenerateResponse:
        if not 0 <= max_retries <= 10:
            raise ValueError("max_retries must be between 0 and 10")
        started = perf_counter()
        schema_model: type[BaseModel] = get_schema(schema_name)
        json_schema = schema_model.model_json_schema()
        failures: list[ValidationFailure] = []
        current_prompt = prompt

        for attempt in range(1, max_retries + 2):
            remaining = self.request_timeout_seconds - (perf_counter() - started)
            if remaining <= 0:
                raise TimeoutError("Generation deadline exceeded")
            async with asyncio.timeout(remaining):
                raw_output = await self.provider.generate(current_prompt, json_schema)

            try:
                parsed = parse_json_object(raw_output)
                validated = schema_model.model_validate(parsed)
                return GenerateResponse(
                    success=True,
                    schema_name=schema_name,
                    attempts=attempt,
                    validation_failures=failures,
                    data=validated.model_dump(mode="json"),
                    latency_ms=round((perf_counter() - started) * 1000, 3),
                )
            except JSONParseError as exc:
                details: list[dict[str, Any]] = [{"message": str(exc)}]
                error_type = "json_parse_error"
            except ValidationError as exc:
                details = exc.errors(include_url=False, include_input=False, include_context=False)
                error_type = "pydantic_validation_error"

            logger.warning(
                "Validation failed | schema=%s attempt=%s type=%s",
                schema_name,
                attempt,
                error_type,
            )
            self.validation_logger.log_failure(
                schema_name=schema_name,
                attempt=attempt,
                raw_output=raw_output,
                error_type=error_type,
                details=details,
            )
            failures.append(
                ValidationFailure(
                    attempt=attempt,
                    error_type=error_type,
                    details=details,
                )
            )

            if attempt <= max_retries:
                current_prompt = build_retry_prompt(
                    original_prompt=prompt,
                    raw_output=raw_output,
                    errors=details,
                )

        return GenerateResponse(
            success=False,
            schema_name=schema_name,
            attempts=max_retries + 1,
            validation_failures=failures,
            data=None,
            latency_ms=round((perf_counter() - started) * 1000, 3),
        )
