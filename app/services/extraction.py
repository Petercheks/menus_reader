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
from app.models.menu import (
    Category,
    Currency,
    ExtractedMenu,
    MenuItem,
    MenuMetadata,
    Promotion,
)
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
        currency_override: Currency | None = None,
    ) -> ExtractedMenu:
        image = process_image(content, mime_type)
        result = await self._extract_with_retry(image)
        if currency_override is not None:
            return _apply_currency_override(result, currency_override)
        return result

    async def extract_many(
        self,
        items: Sequence[tuple[bytes, str | None]],
        currency_override: Currency | None = None,
    ) -> list[ExtractedMenu]:
        async def run(payload: tuple[bytes, str | None]) -> ExtractedMenu:
            content, mime = payload
            return await self.extract_from_bytes(content, mime, currency_override)

        return await asyncio.gather(*(run(item) for item in items))

    async def extract_combined(
        self,
        items: Sequence[tuple[bytes, str | None]],
        currency_override: Currency | None = None,
    ) -> ExtractedMenu:
        results = await self.extract_many(items, currency_override)
        return merge_menus(results)

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


def merge_menus(menus: Sequence[ExtractedMenu]) -> ExtractedMenu:
    if not menus:
        raise ValueError("Cannot merge an empty list of menus")
    if len(menus) == 1:
        return menus[0]
    return ExtractedMenu(
        metadata=_merge_metadata([menu.metadata for menu in menus]),
        categories=_merge_categories([menu.categories for menu in menus]),
        promotions=_merge_promotions([menu.promotions for menu in menus]),
        notes=_merge_notes([menu.notes for menu in menus]),
    )


def _merge_metadata(metadatas: Sequence[MenuMetadata]) -> MenuMetadata:
    restaurant_name = next(
        (meta.restaurant_name for meta in metadatas if meta.restaurant_name),
        None,
    )
    phone = next((meta.phone for meta in metadatas if meta.phone), None)
    payment_methods: list[str] = []
    seen_payments: set[str] = set()
    for meta in metadatas:
        for method in meta.payment_methods:
            key = method.strip().casefold()
            if key and key not in seen_payments:
                seen_payments.add(key)
                payment_methods.append(method)
    return MenuMetadata(
        restaurant_name=restaurant_name,
        phone=phone,
        payment_methods=payment_methods,
    )


def _merge_categories(category_groups: Sequence[Sequence[Category]]) -> list[Category]:
    indexed: dict[str, Category] = {}
    order: list[str] = []
    for group in category_groups:
        for category in group:
            key = category.name.strip().casefold()
            if key in indexed:
                indexed[key] = indexed[key].model_copy(
                    update={"items": _merge_items(indexed[key].items, category.items)}
                )
            else:
                indexed[key] = category
                order.append(key)
    return [indexed[key] for key in order]


def _merge_items(*item_groups: Sequence[MenuItem]) -> list[MenuItem]:
    indexed: dict[str, MenuItem] = {}
    order: list[str] = []
    for group in item_groups:
        for item in group:
            key = item.name.strip().casefold()
            if key in indexed:
                indexed[key] = _prefer_richer_item(indexed[key], item)
            else:
                indexed[key] = item
                order.append(key)
    return [indexed[key] for key in order]


def _prefer_richer_item(current: MenuItem, candidate: MenuItem) -> MenuItem:
    return candidate if _item_richness(candidate) > _item_richness(current) else current


def _item_richness(item: MenuItem) -> int:
    score = len(item.variants)
    if item.description:
        score += 1
    if item.price is not None:
        score += 1
    if item.currency != Currency.UNKNOWN:
        score += 1
    return score


def _merge_promotions(promotion_groups: Sequence[Sequence[Promotion]]) -> list[Promotion]:
    indexed: dict[str, Promotion] = {}
    order: list[str] = []
    for group in promotion_groups:
        for promotion in group:
            key = promotion.name.strip().casefold()
            if key not in indexed:
                indexed[key] = promotion
                order.append(key)
    return [indexed[key] for key in order]


def _merge_notes(notes: Sequence[str | None]) -> str | None:
    parts: list[str] = []
    seen_notes: set[str] = set()
    for note in notes:
        if not note:
            continue
        cleaned = note.strip()
        if not cleaned or cleaned in seen_notes:
            continue
        seen_notes.add(cleaned)
        parts.append(cleaned)
    if not parts:
        return None
    return "\n".join(parts)


def _apply_currency_override(menu: ExtractedMenu, currency: Currency) -> ExtractedMenu:
    return menu.model_copy(
        update={
            "categories": [
                category.model_copy(
                    update={
                        "items": [
                            item.model_copy(
                                update={
                                    "currency": currency,
                                    "variants": [
                                        variant.model_copy(update={"currency": currency})
                                        for variant in item.variants
                                    ],
                                }
                            )
                            for item in category.items
                        ]
                    }
                )
                for category in menu.categories
            ],
            "promotions": [
                promotion.model_copy(update={"currency": currency})
                for promotion in menu.promotions
            ],
        }
    )
