from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

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
