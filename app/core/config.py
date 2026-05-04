from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ProviderName = Literal["openai", "anthropic", "gemini"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    default_provider: ProviderName = "openai"

    api_key: str | None = None

    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-2024-08-06"

    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-4-5"

    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.0-flash"

    max_image_mb: int = Field(default=10, gt=0, le=50)
    max_image_dimension: int = Field(default=2048, gt=0, le=8192)
    request_timeout_seconds: int = Field(default=120, gt=0)

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    def has_provider_key(self, provider: ProviderName) -> bool:
        keys: dict[ProviderName, str | None] = {
            "openai": self.openai_api_key,
            "anthropic": self.anthropic_api_key,
            "gemini": self.gemini_api_key,
        }
        return bool(keys.get(provider))

    def configured_providers(self) -> list[ProviderName]:
        return [p for p in ("openai", "anthropic", "gemini") if self.has_provider_key(p)]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
