from app.core.config import Settings
from app.llm.base import LLMProvider
from app.llm.mock_provider import MockProvider
from app.llm.unconfigured_provider import UnconfiguredProvider


def build_provider(settings: Settings) -> LLMProvider:
    if settings.llm_provider == "mock":
        return MockProvider()

    if not settings.openai_api_key:
        return UnconfiguredProvider(
            "OPENAI_API_KEY is required when LLM_PROVIDER=openai. "
            "Copy .env.example to .env and add your API key."
        )

    # Lazy import keeps tests and health checks independent of the optional SDK at runtime.
    from app.llm.openai_provider import OpenAIProvider

    return OpenAIProvider(
        api_key=settings.openai_api_key,
        model=settings.openai_model,
    )
