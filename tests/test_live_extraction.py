from pathlib import Path

import pytest

from app.core.config import ProviderName, get_settings
from app.models.menu import ExtractedMenu
from app.providers.factory import get_provider
from app.services.extraction import MenuExtractionService

pytestmark = pytest.mark.live


def _available_providers() -> list[ProviderName]:
    get_settings.cache_clear()
    return get_settings().configured_providers()


@pytest.mark.parametrize("provider", _available_providers())
async def test_extract_real_menu(provider: ProviderName, real_menu_paths: list[Path]) -> None:
    if not real_menu_paths:
        pytest.skip("No hay imagenes reales en tests/fixtures")

    extractor = get_provider(provider)
    service = MenuExtractionService(extractor)

    sample = real_menu_paths[0]
    content = sample.read_bytes()
    result = await service.extract_from_bytes(content, "image/png")

    assert isinstance(result, ExtractedMenu)
    assert (
        len(result.categories) > 0
        or len(result.promotions) > 0
        or result.metadata.restaurant_name is not None
    ), f"El proveedor {provider} no extrajo informacion util de {sample.name}"


@pytest.mark.parametrize("provider", _available_providers())
async def test_extract_all_real_menus(provider: ProviderName, real_menu_paths: list[Path]) -> None:
    if not real_menu_paths:
        pytest.skip("No hay imagenes reales en tests/fixtures")

    extractor = get_provider(provider)
    service = MenuExtractionService(extractor)

    for path in real_menu_paths:
        content = path.read_bytes()
        result = await service.extract_from_bytes(content, "image/png")
        assert isinstance(result, ExtractedMenu), f"{provider} fallo en {path.name}"
