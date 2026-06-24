"""Application configuration, loaded from environment variables.

Centralizes every setting so nothing is hardcoded (see ADR-0003: providers and
models are configurable). Import the singleton `settings` everywhere.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed view over the environment. See `.env.example` for the full list."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # App
    environment: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"

    # Datastores
    database_url: str = "postgresql+psycopg://forge:forge@localhost:5432/forgeai"
    redis_url: str = "redis://localhost:6379/0"
    qdrant_url: str = "http://localhost:6333"
    ollama_url: str = "http://localhost:11434"

    # Auth
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440
    access_token_minutes: int = 15  # short-lived access token
    refresh_token_days: int = 30  # long-lived refresh token

    # GitHub integration (Personal Access Token for the MVP)
    github_token: str = ""
    github_api_url: str = "https://api.github.com"

    # Model routing (Ollama, local)
    model_planner: str = "qwen3:8b"
    model_coder: str = "deepseek-coder"
    model_research: str = "llama3.1:8b"
    model_embed: str = "nomic-embed-text"


@lru_cache
def get_settings() -> Settings:
    """Return the cached settings singleton."""
    return Settings()


settings = get_settings()
