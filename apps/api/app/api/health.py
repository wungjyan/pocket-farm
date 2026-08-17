from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str


@router.get("/health", response_model=HealthResponse)
async def health_check(session: AsyncSession = Depends(get_db_session)) -> HealthResponse:
    """Confirm that the API can make an asynchronous MySQL query."""
    try:
        await session.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        await session.rollback()
        raise AppException(
            status_code=503,
            code=ErrorCode.DATABASE_UNAVAILABLE,
            message="Database is unavailable.",
        ) from exc

    return HealthResponse(status="ok")
