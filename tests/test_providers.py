from unittest.mock import AsyncMock, MagicMock

import pytest
from anthropic.types import ToolUseBlock

from app.core.exceptions import InvalidExtractionResultError, ProviderCallError
from app.models.menu import Currency, ExtractedMenu, MenuMetadata
from app.providers.anthropic_provider import AnthropicProvider
from app.providers.base import MenuExtractor
from app.providers.gemini_provider import GeminiProvider
from app.providers.openai_provider import OpenAIProvider
from app.services.image_processing import ProcessedImage


@pytest.fixture
def fake_image() -> ProcessedImage:
    return ProcessedImage(data=b"fake-bytes", mime_type="image/jpeg", width=100, height=80)


@pytest.fixture
def sample_menu() -> ExtractedMenu:
    return ExtractedMenu(
        metadata=MenuMetadata(restaurant_name="Test", payment_methods=["Pago Movil"]),
        categories=[],
        promotions=[],
        notes="ok",
    )


@pytest.fixture
def sample_menu_dict(sample_menu: ExtractedMenu) -> dict:
    return sample_menu.model_dump()


def test_providers_implement_protocol() -> None:
    assert isinstance(OpenAIProvider("k", "m"), MenuExtractor)
    assert isinstance(AnthropicProvider("k", "m"), MenuExtractor)
    assert isinstance(GeminiProvider("k", "m"), MenuExtractor)


async def test_openai_provider_returns_parsed(
    fake_image: ProcessedImage, sample_menu: ExtractedMenu
) -> None:
    provider = OpenAIProvider("test-key", "gpt-4o-2024-08-06")
    fake_response = MagicMock()
    fake_response.output_parsed = sample_menu
    provider._client.responses.parse = AsyncMock(return_value=fake_response)

    result = await provider.extract(fake_image)
    assert result is sample_menu
    provider._client.responses.parse.assert_awaited_once()


async def test_openai_provider_raises_when_no_parsed(fake_image: ProcessedImage) -> None:
    provider = OpenAIProvider("test-key", "gpt-4o-2024-08-06")
    fake_response = MagicMock()
    fake_response.output_parsed = None
    fake_response.output_text = "model refused"
    provider._client.responses.parse = AsyncMock(return_value=fake_response)

    with pytest.raises(InvalidExtractionResultError):
        await provider.extract(fake_image)


async def test_anthropic_provider_returns_validated(
    fake_image: ProcessedImage, sample_menu_dict: dict
) -> None:
    provider = AnthropicProvider("test-key", "claude-sonnet-4-5")
    tool_block = ToolUseBlock(
        id="1",
        type="tool_use",
        name="submit_menu_extraction",
        input=sample_menu_dict,
    )
    fake_response = MagicMock(content=[tool_block])
    provider._client.messages.create = AsyncMock(return_value=fake_response)

    result = await provider.extract(fake_image)
    assert result.metadata.restaurant_name == "Test"


async def test_anthropic_provider_raises_when_missing_tool_use(
    fake_image: ProcessedImage,
) -> None:
    provider = AnthropicProvider("test-key", "claude-sonnet-4-5")
    fake_response = MagicMock(content=[])
    provider._client.messages.create = AsyncMock(return_value=fake_response)

    with pytest.raises(InvalidExtractionResultError):
        await provider.extract(fake_image)


async def test_gemini_provider_returns_parsed(
    fake_image: ProcessedImage, sample_menu: ExtractedMenu
) -> None:
    provider = GeminiProvider("test-key", "gemini-2.0-flash")
    fake_response = MagicMock(parsed=sample_menu, text=None)
    provider._client.aio.models.generate_content = AsyncMock(return_value=fake_response)

    result = await provider.extract(fake_image)
    assert result is sample_menu


async def test_gemini_provider_falls_back_to_text(
    fake_image: ProcessedImage, sample_menu: ExtractedMenu
) -> None:
    provider = GeminiProvider("test-key", "gemini-2.0-flash")
    fake_response = MagicMock(parsed=None, text=sample_menu.model_dump_json())
    provider._client.aio.models.generate_content = AsyncMock(return_value=fake_response)

    result = await provider.extract(fake_image)
    assert result.metadata.restaurant_name == "Test"


def test_provider_factory_resolution(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.core.config import get_settings
    from app.providers.factory import resolve_provider_name

    get_settings.cache_clear()
    monkeypatch.setenv("DEFAULT_PROVIDER", "anthropic")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "anthropic-key")
    monkeypatch.setenv("GEMINI_API_KEY", "")

    assert resolve_provider_name(None) == "anthropic"
    assert resolve_provider_name("OpenAI") == "openai"

    get_settings.cache_clear()


def test_extraction_service_propagates_errors(fake_image: ProcessedImage) -> None:
    from app.services.extraction import MenuExtractionService

    failing = MagicMock()
    failing.name = "openai"
    failing.extract = AsyncMock(side_effect=ProviderCallError("openai", "boom"))
    service = MenuExtractionService(failing)

    import asyncio

    with pytest.raises(ProviderCallError):
        asyncio.run(service._extract_with_retry(fake_image))


def test_currency_enum_used_in_extracted_menu() -> None:
    schema = ExtractedMenu.model_json_schema()
    raw = repr(schema)
    assert "USD" in raw
    assert "VES" in raw
    assert Currency.UNKNOWN.value in raw
