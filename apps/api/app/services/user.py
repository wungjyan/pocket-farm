from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


async def update_current_user(
    session: AsyncSession,
    *,
    user: User,
    nickname: str | None,
) -> User:
    user.nickname = nickname
    await session.commit()
    await session.refresh(user)
    return user
