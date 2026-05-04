from openai import APIError, AsyncOpenAI

from app.core.config import get_settings
from app.core.exceptions import InvalidExtractionResultError, ProviderCallError
from app.models.menu import ExtractedMenu
from app.prompts.menu_extraction import SYSTEM_PROMPT, USER_INSTRUCTION
from app.providers.base import MenuExtractor
from app.services.image_processing import ProcessedImage


class OpenAIProvider(MenuExtractor):
    name = "openai"

    def __init__(self, api_key: str, model: str) -> None:
        settings = get_settings()
        self._client = AsyncOpenAI(api_key=api_key, timeout=settings.request_timeout_seconds)
        self._model = model

    async def extract(self, image: ProcessedImage) -> ExtractedMenu:
        try:
            response = await self._client.responses.parse(
                model=self._model,
                input=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": USER_INSTRUCTION},
                            {"type": "input_image", "image_url": image.data_url},
                        ],
                    },
                ],
                text_format=ExtractedMenu,
            )
        except APIError as exc:
            raise ProviderCallError(self.name, str(exc)) from exc

        parsed = response.output_parsed
        if parsed is None:
            refusal = getattr(response, "output_text", None) or "empty response"
            raise InvalidExtractionResultError(self.name, refusal)
        return parsed
