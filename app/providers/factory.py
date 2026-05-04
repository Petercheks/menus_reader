from functools import cache

from app.core.config import ProviderName, get_settings
from app.core.exceptions import ProviderNotConfiguredError, UnknownProviderError
from app.providers.anthropic_provider import AnthropicProvider
from app.providers.base import MenuExtractor
from app.providers.gemini_provider import GeminiProvider
from app.providers.openai_provider import OpenAIProvider

VALID_PROVIDERS: frozenset[ProviderName] = frozenset({"openai", "anthropic", "gemini"})


def _build(provider: ProviderName) -> MenuExtractor:
    settings = get_settings()
    if not settings.has_provider_key(provider):
        raise ProviderNotConfiguredError(provider)
    match provider:
        case "openai":
            return OpenAIProvider(
                api_key=settings.openai_api_key or "",
                model=settings.openai_model,
            )
        case "anthropic":
            return AnthropicProvider(
                api_key=settings.anthropic_api_key or "",
                model=settings.anthropic_model,
            )
        case "gemini":
            return GeminiProvider(
                api_key=settings.gemini_api_key or "",
                model=settings.gemini_model,
            )


@cache
def _cached(provider: ProviderName) -> MenuExtractor:
    return _build(provider)


def resolve_provider_name(requested: str | None) -> ProviderName:
    settings = get_settings()
    name = (requested or settings.default_provider).lower()
    if name not in VALID_PROVIDERS:
        raise UnknownProviderError(name)
    return name


def get_provider(requested: str | None = None) -> MenuExtractor:
    name = resolve_provider_name(requested)
    return _cached(name)
