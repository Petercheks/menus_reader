import io
from pathlib import Path

import pytest
from PIL import Image

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES_DIR


@pytest.fixture
def small_jpeg_bytes() -> bytes:
    image = Image.new("RGB", (200, 100), color=(255, 0, 0))
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=85)
    return buffer.getvalue()


@pytest.fixture
def large_jpeg_bytes() -> bytes:
    image = Image.new("RGB", (4000, 3000), color=(0, 128, 255))
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=85)
    return buffer.getvalue()


@pytest.fixture
def png_bytes() -> bytes:
    image = Image.new("RGBA", (300, 200), color=(0, 200, 0, 255))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture
def real_menu_paths(fixtures_dir: Path) -> list[Path]:
    return sorted(fixtures_dir.glob("*.png"))
