import io
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.core.config import get_settings
from app.main import app
from app.models.menu import Currency, ExtractedMenu, MenuMetadata, Promotion


@pytest.fixture(autouse=True)
def configure_env(monkeypatch: pytest.MonkeyPatch) -> None:
    get_settings.cache_clear()
    monkeypatch.setenv("DEFAULT_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic")
    monkeypatch.setenv("GEMINI_API_KEY", "")
    yield
    get_settings.cache_clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def fake_menu() -> ExtractedMenu:
    return ExtractedMenu(
        metadata=MenuMetadata(restaurant_name="Test Resto"),
        categories=[],
        promotions=[
            Promotion(
                name="Combo",
                includes=["1 Pizza", "1 Refresco"],
                price=10.0,
                currency=Currency.USD,
            )
        ],
    )


@pytest.fixture
def jpeg_upload() -> bytes:
    image = Image.new("RGB", (200, 100), color=(0, 0, 255))
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=85)
    return buffer.getvalue()


def test_health_returns_configured_providers(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "openai" in body["configured_providers"]
    assert "anthropic" in body["configured_providers"]
    assert "gemini" not in body["configured_providers"]


def test_extract_endpoint_uses_provider(
    client: TestClient, fake_menu: ExtractedMenu, jpeg_upload: bytes
) -> None:
    with patch("app.providers.factory._cached") as cached:
        provider = AsyncMock()
        provider.name = "openai"
        provider.extract = AsyncMock(return_value=fake_menu)
        cached.return_value = provider

        response = client.post(
            "/api/v1/extract",
            files={"file": ("menu.jpg", jpeg_upload, "image/jpeg")},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["metadata"]["restaurant_name"] == "Test Resto"
    assert body["promotions"][0]["price"] == 10.0


def test_extract_rejects_empty_file(client: TestClient) -> None:
    response = client.post(
        "/api/v1/extract",
        files={"file": ("empty.jpg", b"", "image/jpeg")},
    )
    assert response.status_code == 400


def test_extract_rejects_unconfigured_provider(client: TestClient, jpeg_upload: bytes) -> None:
    response = client.post(
        "/api/v1/extract?provider=gemini",
        files={"file": ("menu.jpg", jpeg_upload, "image/jpeg")},
    )
    assert response.status_code == 503


def test_extract_rejects_unknown_provider(client: TestClient, jpeg_upload: bytes) -> None:
    response = client.post(
        "/api/v1/extract?provider=foobar",
        files={"file": ("menu.jpg", jpeg_upload, "image/jpeg")},
    )
    assert response.status_code == 400


def test_batch_extract_returns_multiple(
    client: TestClient, fake_menu: ExtractedMenu, jpeg_upload: bytes
) -> None:
    with patch("app.providers.factory._cached") as cached:
        provider = AsyncMock()
        provider.name = "openai"
        provider.extract = AsyncMock(return_value=fake_menu)
        cached.return_value = provider

        response = client.post(
            "/api/v1/extract/batch",
            files=[
                ("files", ("a.jpg", jpeg_upload, "image/jpeg")),
                ("files", ("b.jpg", jpeg_upload, "image/jpeg")),
            ],
        )

    assert response.status_code == 200
    body = response.json()
    assert len(body["results"]) == 2
