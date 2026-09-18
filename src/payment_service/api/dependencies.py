from collections.abc import AsyncIterator

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from payment_service.core.config import get_settings
from payment_service.infrastructure.database import get_session

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(api_key: str | None = Security(api_key_header)) -> None:
    if api_key != get_settings().api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")


async def session_dependency(
    session: AsyncSession = Depends(get_session),
) -> AsyncIterator[AsyncSession]:
    yield session
