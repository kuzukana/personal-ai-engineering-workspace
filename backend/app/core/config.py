from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = Field(default="development")
    backend_host: str = Field(default="0.0.0.0")
    backend_port: int = Field(default=8000)
    frontend_origin: str = Field(default="http://localhost:3000")
    database_url: str = Field(
        default="postgresql+asyncpg://workspace:workspace@localhost:5432/workspace"
    )
    redis_url: str = Field(default="redis://localhost:6379/0")

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


@lru_cache
def get_settings() -> Settings:
    return Settings()
