from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException
from app.models.user import User


async def login_with_verification_code(
    session: AsyncSession,
    *,
    phone_number: str,
    verification_code: str,
) -> User:
    if not settings.test_login_enabled or verification_code != settings.test_login_code:
        raise AppException(
            status_code=401,
            code=ErrorCode.UNAUTHORIZED,
            message="Invalid phone number or verification code.",
        )

    result = await session.execute(select(User).where(User.phone_number == phone_number))
    user = result.scalar_one_or_none()
    if user is not None:
        return user

    user = User(phone_number=phone_number)
    session.add(user)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        result = await session.execute(select(User).where(User.phone_number == phone_number))
        user = result.scalar_one_or_none()
        if user is None:
            raise AppException(
                status_code=409,
                code=ErrorCode.BUSINESS_CONFLICT,
                message="Unable to create user.",
            ) from exc
        return user

    await session.refresh(user)
    return user
