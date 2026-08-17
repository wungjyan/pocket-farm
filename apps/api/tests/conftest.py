import asyncio
import os

import pytest
from sqlalchemy import delete

os.environ.setdefault(
    "DATABASE_URL",
    "mysql+aiomysql://root:wj123456@127.0.0.1:3306/pocket_farm?charset=utf8mb4",
)
os.environ.setdefault("JWT_SECRET_KEY", "test-only-secret-at-least-32-bytes")


async def remove_test_user() -> None:
    from app.db.session import async_session_factory, engine
    from app.models.user import User

    async with async_session_factory() as session:
        await session.execute(delete(User).where(User.phone_number == "13800000001"))
        await session.commit()
    await engine.dispose()


@pytest.fixture(autouse=True)
def clean_test_user() -> None:
    yield
    asyncio.run(remove_test_user())
