from collections.abc import AsyncGenerator
from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException
from app.core.security import decode_access_token
from app.db.session import async_session_factory
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide one independent asynchronous database session per request."""
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> User:
    if credentials is None:
        raise AppException(
            status_code=401,
            code=ErrorCode.UNAUTHORIZED,
            message="Authentication is required.",
        )

    try:
        payload = decode_access_token(credentials.credentials)
    except jwt.InvalidTokenError as exc:
        raise AppException(
            status_code=401,
            code=ErrorCode.UNAUTHORIZED,
            message="Invalid or expired access token.",
        ) from exc

    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject.isdigit():
        raise AppException(
            status_code=401,
            code=ErrorCode.UNAUTHORIZED,
            message="Invalid or expired access token.",
        )

    result = await session.execute(select(User).where(User.id == int(subject)))
    user = result.scalar_one_or_none()
    if user is None:
        raise AppException(
            status_code=401,
            code=ErrorCode.UNAUTHORIZED,
            message="Invalid or expired access token.",
        )
    return user
