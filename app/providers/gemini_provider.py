from google import genai
from google.genai import types
from google.genai.errors import APIError
from pydantic import ValidationError

from app.core.exceptions import InvalidExtractionResultError, ProviderCallError
from app.models.menu import ExtractedMenu
from app.prompts.menu_extraction import SYSTEM_PROMPT, USER_INSTRUCTION
from app.providers.base import MenuExtractor
from app.services.image_processing import ProcessedImage


class GeminiProvider(MenuExtractor):
    name = "gemini"

    def __init__(self, api_key: str, model: str) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model
        self._config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=ExtractedMenu,
        )

    async def extract(self, image: ProcessedImage) -> ExtractedMenu:
        try:
            response = await self._client.aio.models.generate_content(
                model=self._model,
                contents=[
                    types.Part.from_bytes(data=image.data, mime_type=image.mime_type),
                    USER_INSTRUCTION,
                ],
                config=self._config,
            )
        except APIError as exc:
            raise ProviderCallError(self.name, str(exc)) from exc

        parsed = response.parsed
        if isinstance(parsed, ExtractedMenu):
            return parsed

        text = response.text or ""
        if not text:
            raise InvalidExtractionResultError(self.name, "respuesta vacia")
        try:
            return ExtractedMenu.model_validate_json(text)
        except ValidationError as exc:
            raise InvalidExtractionResultError(self.name, str(exc)) from exc
