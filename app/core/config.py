from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Structured Output Agent"
    app_env: Literal["development", "test", "production"] = "development"
    log_level: str = "INFO"
    max_retries: int = Field(default=2, ge=0, le=10)

    llm_provider: Literal["openai", "mock"] = "openai"
    openai_api_key: str | None = None
    openai_model: str = "gpt-5-mini"

    validation_log_path: Path = Path("logs/validation_failures.jsonl")


@lru_cache
def get_settings() -> Settings:
    return Settings()
