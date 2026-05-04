from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from app.api.routes import health_router, router
from app.core.logging import configure_logging, get_logger


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    logger = get_logger(__name__)
    logger.info("menu_reader.startup")
    yield
    logger.info("menu_reader.shutdown")


app = FastAPI(
    title="Menu Reader",
    description=(
        "Microservicio de extraccion estructurada de menus de restaurantes "
        "a partir de imagenes, con LLM Vision multi-proveedor."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(router)
app.include_router(health_router)


def _convert_binary_items_for_swagger(node: Any) -> None:
    if isinstance(node, dict):
        items = node.get("items")
        if (
            node.get("type") == "array"
            and isinstance(items, dict)
            and items.get("type") == "string"
            and items.get("contentMediaType") == "application/octet-stream"
        ):
            items.pop("contentMediaType", None)
            items["format"] = "binary"
        for value in node.values():
            _convert_binary_items_for_swagger(value)
    elif isinstance(node, list):
        for value in node:
            _convert_binary_items_for_swagger(value)


def custom_openapi() -> dict[str, Any]:
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    _convert_binary_items_for_swagger(schema.get("components", {}).get("schemas", {}))
    app.openapi_schema = schema
    return schema


app.openapi = custom_openapi
