from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.llm.factory import build_provider
from app.services.agent import StructuredOutputAgent
from app.services.validation_logger import ValidationLogger


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging()
    provider = build_provider(settings)
    app.state.agent = StructuredOutputAgent(
        provider=provider,
        validation_logger=ValidationLogger(settings.validation_log_path),
        request_timeout_seconds=settings.request_timeout_seconds,
    )
    yield


settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description=(
        "Reliability layer for LLM applications that validates structured output with "
        "Pydantic, retries malformed responses, and logs validation failures."
    ),
    lifespan=lifespan,
)
app.include_router(router)
