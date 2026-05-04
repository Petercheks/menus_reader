from typing import Protocol, runtime_checkable

from app.models.menu import ExtractedMenu
from app.services.image_processing import ProcessedImage


@runtime_checkable
class MenuExtractor(Protocol):
    name: str

    async def extract(self, image: ProcessedImage) -> ExtractedMenu: ...
