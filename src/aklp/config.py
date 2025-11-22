"""Configuration management for AKLP CLI Agent."""

from functools import lru_cache

from pydantic import Field, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    llm_service_url: HttpUrl = Field(
        default="http://localhost:8001",
        description="Base URL for LLM analysis service",
    )
    note_service_url: HttpUrl = Field(
        default="http://localhost:8002",
        description="Base URL for Note service (aklp-note)",
    )
    task_service_url: HttpUrl = Field(
        default="http://localhost:8003",
        description="Base URL for Task service (aklp-task)",
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings.

    Returns:
        Settings: Application configuration instance
    """
    return Settings()
