"""Configuration for the Pedagogical Article Writer.

Uses pydantic-settings for type-safe configuration with environment variable loading.
Settings are validated at startup and cached via lru_cache.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    """Application configuration loaded from environment variables.

    All settings can be overridden via .env file or environment variables.
    Variable names are case-insensitive (REASONING_MODEL = reasoning_model).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # API keys
    brave_search_api_key: str | None = None

    # Model configuration 
    reasoning_model: str| None = None
    writing_model: str | None = None

    # OpenRouter configuration
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_api_key: str | None = None


@lru_cache
def get_config() -> AppConfig:
    """Get cached application configuration.

    Uses lru_cache to ensure settings are only loaded once.
    Call get_config.cache_clear() to reload in tests.
    """
    return AppConfig()


# Convenience export
config = get_config()
