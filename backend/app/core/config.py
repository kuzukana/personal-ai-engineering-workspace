from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = Field(default="development")
    backend_host: str = Field(default="127.0.0.1")
    backend_port: int = Field(default=8000)
    frontend_origin: str = Field(default="http://localhost:3000")
    database_url: str = Field(
        default="postgresql+asyncpg://workspace:workspace@localhost:5432/workspace"
    )
    redis_url: str = Field(default="redis://localhost:6379/0")

    embedding_provider: Literal["mock", "http"] = "mock"
    embedding_base_url: str | None = None
    embedding_api_key: str | None = None
    embedding_model: str | None = None
    embedding_dimensions: int = Field(default=256, ge=1, le=4096)

    research_context_window: int = Field(default=32768, ge=1024)
    research_max_output_tokens: int = Field(default=2048, ge=1)

    openai_api_key: str | None = None
    openai_model: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"

    anthropic_api_key: str | None = None
    anthropic_model: str | None = None

    deepseek_api_key: str | None = None
    deepseek_model: str | None = None
    deepseek_base_url: str | None = None

    kimi_api_key: str | None = None
    kimi_model: str | None = None
    kimi_base_url: str | None = None

    brave_search_api_key: str | None = None
    github_token: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
