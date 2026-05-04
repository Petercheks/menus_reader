import io
from pathlib import Path

import pytest
from PIL import Image

from app.core.exceptions import InvalidImageError
from app.services.image_processing import (
    ALLOWED_MIME_TYPES,
    ProcessedImage,
    process_image,
)


def test_processed_image_data_url(small_jpeg_bytes: bytes) -> None:
    image = process_image(small_jpeg_bytes, "image/jpeg")
    assert image.mime_type == "image/jpeg"
    assert image.width == 200
    assert image.height == 100
    assert image.data_url.startswith("data:image/jpeg;base64,")
    assert len(image.base64_data) > 0


def test_process_image_resizes_large(large_jpeg_bytes: bytes) -> None:
    image = process_image(large_jpeg_bytes, "image/jpeg")
    assert max(image.width, image.height) <= 2048
    reopened = Image.open(io.BytesIO(image.data))
    reopened.load()
    assert max(reopened.size) <= 2048


def test_process_image_keeps_small(small_jpeg_bytes: bytes) -> None:
    image = process_image(small_jpeg_bytes, "image/jpeg")
    assert image.data == small_jpeg_bytes


def test_process_image_accepts_png(png_bytes: bytes) -> None:
    image = process_image(png_bytes, "image/png")
    assert image.mime_type == "image/png"
    assert image.width == 300


def test_process_image_infers_mime_when_missing(small_jpeg_bytes: bytes) -> None:
    image = process_image(small_jpeg_bytes, None)
    assert image.mime_type in ALLOWED_MIME_TYPES


def test_process_image_rejects_unsupported_mime(small_jpeg_bytes: bytes) -> None:
    with pytest.raises(InvalidImageError):
        process_image(small_jpeg_bytes, "image/tiff")


def test_process_image_rejects_invalid_bytes() -> None:
    with pytest.raises(InvalidImageError):
        process_image(b"not an image at all", "image/jpeg")


def test_process_image_rejects_empty() -> None:
    with pytest.raises(InvalidImageError):
        process_image(b"", "image/jpeg")


def test_processed_image_is_immutable(small_jpeg_bytes: bytes) -> None:
    image = process_image(small_jpeg_bytes, "image/jpeg")
    assert isinstance(image, ProcessedImage)
    with pytest.raises((AttributeError, TypeError)):
        image.width = 999


def test_real_menu_fixtures_load(real_menu_paths: list[Path]) -> None:
    assert len(real_menu_paths) >= 1
    for path in real_menu_paths:
        content = path.read_bytes()
        image = process_image(content, "image/png")
        assert image.mime_type in ALLOWED_MIME_TYPES
        assert image.width > 0
        assert image.height > 0
