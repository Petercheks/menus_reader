from anthropic import APIError, AsyncAnthropic
from anthropic.types import ToolUseBlock
from pydantic import ValidationError

from app.core.config import get_settings
from app.core.exceptions import InvalidExtractionResultError, ProviderCallError
from app.models.menu import ExtractedMenu
from app.prompts.menu_extraction import SYSTEM_PROMPT, USER_INSTRUCTION
from app.providers.base import MenuExtractor
from app.services.image_processing import ProcessedImage

EXTRACTION_TOOL_NAME = "submit_menu_extraction"
EXTRACTION_TOOL_DESCRIPTION = (
    "Devuelve el menu extraido como JSON estructurado segun el esquema dado."
)


class AnthropicProvider(MenuExtractor):
    name = "anthropic"

    def __init__(self, api_key: str, model: str) -> None:
        settings = get_settings()
        self._client = AsyncAnthropic(api_key=api_key, timeout=settings.request_timeout_seconds)
        self._model = model
        self._tool = {
            "name": EXTRACTION_TOOL_NAME,
            "description": EXTRACTION_TOOL_DESCRIPTION,
            "input_schema": ExtractedMenu.model_json_schema(),
        }

    async def extract(self, image: ProcessedImage) -> ExtractedMenu:
        try:
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=[self._tool],
                tool_choice={"type": "tool", "name": EXTRACTION_TOOL_NAME},
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": image.mime_type,
                                    "data": image.base64_data,
                                },
                            },
                            {"type": "text", "text": USER_INSTRUCTION},
                        ],
                    }
                ],
            )
        except APIError as exc:
            raise ProviderCallError(self.name, str(exc)) from exc

        tool_block = next(
            (block for block in response.content if isinstance(block, ToolUseBlock)),
            None,
        )
        if tool_block is None:
            raise InvalidExtractionResultError(self.name, "no se devolvio tool_use")

        try:
            return ExtractedMenu.model_validate(tool_block.input)
        except ValidationError as exc:
            raise InvalidExtractionResultError(self.name, str(exc)) from exc
