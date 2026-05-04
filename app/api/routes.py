from typing import Annotated

from fastapi import APIRouter, Depends, File, Header, HTTPException, Query, UploadFile, status
from pydantic import BaseModel

from app.core.config import ProviderName, get_settings
from app.core.exceptions import (
    InvalidExtractionResultError,
    InvalidImageError,
    ProviderCallError,
    ProviderNotConfiguredError,
    UnknownProviderError,
)
from app.core.logging import get_logger
from app.core.security import verify_api_key
from app.models.menu import ExtractedMenu
from app.providers.factory import get_provider, resolve_provider_name
from app.services.extraction import MenuExtractionService

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/v1",
    tags=["extraction"],
    dependencies=[Depends(verify_api_key)],
)
health_router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    default_provider: ProviderName
    configured_providers: list[ProviderName]


class BatchExtractionResponse(BaseModel):
    results: list[ExtractedMenu]


def _resolve_provider(query: str | None, header: str | None) -> str | None:
    return query or header


def _service_for(provider_request: str | None) -> MenuExtractionService:
    try:
        provider = get_provider(provider_request)
    except UnknownProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except ProviderNotConfiguredError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    return MenuExtractionService(provider)


async def _read_upload(file: UploadFile) -> bytes:
    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo enviado esta vacio",
        )
    return content


def _handle_extraction_errors(exc: Exception, provider_name: str) -> HTTPException:
    if isinstance(exc, InvalidImageError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    if isinstance(exc, InvalidExtractionResultError):
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    if isinstance(exc, ProviderCallError):
        return HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))
    logger.error(
        "extraction.unexpected_error",
        provider=provider_name,
        error=str(exc),
    )
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Error inesperado durante la extraccion",
    )


@router.post(
    "/extract",
    response_model=ExtractedMenu,
    summary="Extrae el menu de una imagen",
)
async def extract_menu(
    file: Annotated[UploadFile, File(description="Imagen del menu (jpg, png, webp)")],
    provider: Annotated[str | None, Query(description="Proveedor LLM a usar")] = None,
    x_llm_provider: Annotated[str | None, Header()] = None,
) -> ExtractedMenu:
    requested = _resolve_provider(provider, x_llm_provider)
    service = _service_for(requested)
    content = await _read_upload(file)
    try:
        return await service.extract_from_bytes(content, file.content_type)
    except Exception as exc:
        raise _handle_extraction_errors(exc, service.provider_name) from exc


# @router.post(
#     "/extract/batch",
#     response_model=BatchExtractionResponse,
#     summary="Extrae el menu de varias imagenes en paralelo",
# )
# async def extract_menus_batch(
#     files: Annotated[list[UploadFile], File(description="Imagenes de menus")],
#     provider: Annotated[str | None, Query(description="Proveedor LLM a usar")] = None,
#     x_llm_provider: Annotated[str | None, Header()] = None,
# ) -> BatchExtractionResponse:
#     if not files:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Debe enviar al menos un archivo",
#         )
#     requested = _resolve_provider(provider, x_llm_provider)
#     service = _service_for(requested)

#     payloads: list[tuple[bytes, str | None]] = []
#     for file in files:
#         content = await _read_upload(file)
#         payloads.append((content, file.content_type))

#     try:
#         results = await service.extract_many(payloads)
#     except Exception as exc:
#         raise _handle_extraction_errors(exc, service.provider_name) from exc
#     return BatchExtractionResponse(results=results)


@health_router.get("/health", response_model=HealthResponse, summary="Estado del servicio")
async def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        default_provider=resolve_provider_name(None),
        configured_providers=settings.configured_providers(),
    )
