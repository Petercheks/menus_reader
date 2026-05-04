import asyncio
from collections.abc import Sequence

from tenacity import (
    AsyncRetrying,
    RetryError,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.exceptions import InvalidExtractionResultError, ProviderCallError
from app.core.logging import get_logger
from app.models.menu import ExtractedMenu
from app.providers.base import MenuExtractor
from app.services.image_processing import ProcessedImage, process_image

logger = get_logger(__name__)


class MenuExtractionService:
    def __init__(self, provider: MenuExtractor) -> None:
        self._provider = provider

    @property
    def provider_name(self) -> str:
        return self._provider.name

    async def extract_from_bytes(
        self,
        content: bytes,
        mime_type: str | None = None,
    ) -> ExtractedMenu:
        image = process_image(content, mime_type)
        return await self._extract_with_retry(image)

    async def extract_many(
        self,
        items: Sequence[tuple[bytes, str | None]],
    ) -> list[ExtractedMenu]:
        async def run(payload: tuple[bytes, str | None]) -> ExtractedMenu:
            content, mime = payload
            return await self.extract_from_bytes(content, mime)

        return await asyncio.gather(*(run(item) for item in items))

    async def _extract_with_retry(self, image: ProcessedImage) -> ExtractedMenu:
        retrying = AsyncRetrying(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=1, max=8),
            retry=retry_if_exception_type((ProviderCallError, InvalidExtractionResultError)),
            reraise=True,
        )
        try:
            async for attempt in retrying:
                with attempt:
                    log = logger.bind(
                        provider=self._provider.name,
                        attempt=attempt.retry_state.attempt_number,
                        width=image.width,
                        height=image.height,
                    )
                    log.info("menu_extraction.start")
                    result = await self._provider.extract(image)
                    log.info(
                        "menu_extraction.success",
                        categories=len(result.categories),
                        promotions=len(result.promotions),
                    )
                    return result
        except RetryError as exc:
            raise exc.last_attempt.exception() from exc

        raise RuntimeError("Unreachable: AsyncRetrying terminated without yielding")
