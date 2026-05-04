import base64
import io
from dataclasses import dataclass

from PIL import Image, UnidentifiedImageError

from app.core.config import get_settings
from app.core.exceptions import InvalidImageError

ALLOWED_MIME_TYPES: frozenset[str] = frozenset({"image/jpeg", "image/png", "image/webp"})

PIL_FORMAT_TO_MIME: dict[str, str] = {
    "JPEG": "image/jpeg",
    "PNG": "image/png",
    "WEBP": "image/webp",
}


@dataclass(frozen=True, slots=True)
class ProcessedImage:
    data: bytes
    mime_type: str
    width: int
    height: int

    @property
    def base64_data(self) -> str:
        return base64.b64encode(self.data).decode("ascii")

    @property
    def data_url(self) -> str:
        return f"data:{self.mime_type};base64,{self.base64_data}"


def _validate_size(content: bytes) -> None:
    settings = get_settings()
    max_bytes = settings.max_image_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise InvalidImageError(
            f"Image exceeds the maximum allowed size ({settings.max_image_mb} MB)"
        )
    if not content:
        raise InvalidImageError("The file is empty")


def _open_image(content: bytes) -> Image.Image:
    try:
        image = Image.open(io.BytesIO(content))
        image.load()
        return image
    except (UnidentifiedImageError, OSError) as exc:
        raise InvalidImageError("Unable to read the image, invalid format") from exc


def _normalize_mime(mime_type: str | None, image: Image.Image) -> str:
    if mime_type:
        normalized = mime_type.lower()
        if normalized not in ALLOWED_MIME_TYPES:
            raise InvalidImageError(
                f"Unsupported image type: '{mime_type}'. "
                f"Allowed: {', '.join(sorted(ALLOWED_MIME_TYPES))}"
            )
        return normalized
    inferred = PIL_FORMAT_TO_MIME.get(image.format or "")
    if inferred:
        return inferred
    raise InvalidImageError(
        f"Unable to determine the image type. "
        f"Allowed: {', '.join(sorted(ALLOWED_MIME_TYPES))}"
    )


def _resize_if_needed(image: Image.Image, max_side: int) -> Image.Image:
    width, height = image.size
    longest = max(width, height)
    if longest <= max_side:
        return image
    scale = max_side / longest
    new_size = (int(width * scale), int(height * scale))
    return image.resize(new_size, Image.Resampling.LANCZOS)


def _encode(image: Image.Image, mime_type: str) -> bytes:
    pil_format = next(
        (fmt for fmt, mime in PIL_FORMAT_TO_MIME.items() if mime == mime_type),
        "JPEG",
    )
    buffer = io.BytesIO()
    save_kwargs: dict[str, object] = {}
    target = image
    if pil_format == "JPEG":
        save_kwargs["quality"] = 90
        save_kwargs["optimize"] = True
        if image.mode not in ("RGB", "L"):
            target = image.convert("RGB")
    elif pil_format == "PNG":
        save_kwargs["optimize"] = True
    target.save(buffer, format=pil_format, **save_kwargs)
    return buffer.getvalue()


def process_image(content: bytes, mime_type: str | None = None) -> ProcessedImage:
    _validate_size(content)
    image = _open_image(content)
    resolved_mime = _normalize_mime(mime_type, image)
    settings = get_settings()
    resized = _resize_if_needed(image, settings.max_image_dimension)
    if resized is image and resolved_mime == PIL_FORMAT_TO_MIME.get(image.format or ""):
        return ProcessedImage(
            data=content,
            mime_type=resolved_mime,
            width=image.size[0],
            height=image.size[1],
        )
    encoded = _encode(resized, resolved_mime)
    return ProcessedImage(
        data=encoded,
        mime_type=resolved_mime,
        width=resized.size[0],
        height=resized.size[1],
    )
