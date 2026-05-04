import secrets
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

from app.core.config import Settings, get_settings

API_KEY_HEADER_NAME = "X-API-Key"

_api_key_header = APIKeyHeader(name=API_KEY_HEADER_NAME, auto_error=False)


def verify_api_key(
    settings: Annotated[Settings, Depends(get_settings)],
    provided_key: Annotated[str | None, Depends(_api_key_header)],
) -> None:
    expected = settings.api_key
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="api key not configured",
        )
    if not provided_key or not secrets.compare_digest(provided_key, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid or missing api key",
            headers={"WWW-Authenticate": API_KEY_HEADER_NAME},
        )


VerifyApiKeyDep = Annotated[None, Depends(verify_api_key)]
