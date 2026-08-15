import logging
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
    def __init__(self, provider: LLMProvider, validation_logger: ValidationLogger) -> None:
        self.provider = provider
        self.validation_logger = validation_logger

    async def run(
        self,
        *,
        prompt: str,
        schema_name: str,
        max_retries: int,
    ) -> GenerateResponse:
        schema_model: type[BaseModel] = get_schema(schema_name)
        json_schema = schema_model.model_json_schema()
        failures: list[ValidationFailure] = []
        current_prompt = prompt
        last_raw_output: str | None = None

        for attempt in range(1, max_retries + 2):
            raw_output = await self.provider.generate(current_prompt, json_schema)
            last_raw_output = raw_output

            try:
                parsed = parse_json_object(raw_output)
                validated = schema_model.model_validate(parsed)
                return GenerateResponse(
                    success=True,
                    schema_name=schema_name,
                    attempts=attempt,
                    validation_failures=failures,
                    data=validated.model_dump(mode="json"),
                )
            except JSONParseError as exc:
                details: list[dict[str, Any]] = [{"message": str(exc)}]
                error_type = "json_parse_error"
            except ValidationError as exc:
                details = exc.errors(include_url=False)
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
            raw_output=last_raw_output,
        )
