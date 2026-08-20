import asyncio
import os

import pytest
from sqlalchemy import delete, or_, select

os.environ.setdefault(
    "DATABASE_URL",
    "mysql+aiomysql://root:wj123456@127.0.0.1:3306/pocket_farm?charset=utf8mb4",
)
os.environ.setdefault("JWT_SECRET_KEY", "test-only-secret-at-least-32-bytes")


async def remove_test_user() -> None:
    from app.db.session import async_session_factory, engine
    from app.models.farm import Farm, FarmMember
    from app.models.operation import FarmOperation
    from app.models.plot import Plot
    from app.models.production import Production
    from app.models.user import User

    async with async_session_factory() as session:
        test_phones = [f"1380000000{index}" for index in range(1, 7)]
        user_ids = list(
            (await session.scalars(select(User.id).where(User.phone_number.in_(test_phones)))).all()
        )
        farm_ids = list(
            (await session.scalars(select(Farm.id).where(Farm.created_by.in_(user_ids)))).all()
        )
        if user_ids or farm_ids:
            await session.execute(
                delete(FarmMember).where(
                    or_(
                        FarmMember.user_id.in_(user_ids),
                        FarmMember.farm_id.in_(farm_ids),
                    )
                )
            )
        if farm_ids:
            plot_ids = list(
                (await session.scalars(select(Plot.id).where(Plot.farm_id.in_(farm_ids)))).all()
            )
            if plot_ids:
                await session.execute(
                    delete(FarmOperation).where(FarmOperation.plot_id.in_(plot_ids))
                )
                await session.execute(delete(Production).where(Production.plot_id.in_(plot_ids)))
            await session.execute(delete(Plot).where(Plot.farm_id.in_(farm_ids)))
            await session.execute(delete(Farm).where(Farm.id.in_(farm_ids)))
        if user_ids:
            await session.execute(delete(User).where(User.id.in_(user_ids)))
        await session.commit()
    await engine.dispose()


@pytest.fixture(autouse=True)
def clean_test_user() -> None:
    yield
    asyncio.run(remove_test_user())
