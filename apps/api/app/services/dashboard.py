from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.farm import FarmMember
from app.models.harvest import HarvestRecord
from app.models.operation import FarmOperation, OperationType
from app.models.plot import Plot
from app.models.production import Production
from app.models.species import Species
from app.models.user import User
from app.services.farm import get_farm_with_member

DASHBOARD_ACTIVITY_LIMIT = 5


async def get_farm_dashboard(
    session: AsyncSession,
    *,
    farm_id: int,
    user_id: int,
) -> tuple[
    list[Plot],
    list[tuple[FarmMember, "object"]],
    list[tuple[FarmOperation, OperationType, Plot]],
    list[tuple[HarvestRecord, Production, Plot, Species]],
]:
    """Return plots, members, recent operations and recent harvests for a farm."""
    await get_farm_with_member(session, farm_id=farm_id, user_id=user_id)

    # 1. All plots for the farm
    plots_result = await session.execute(
        select(Plot)
        .where(Plot.farm_id == farm_id)
        .order_by(Plot.created_at.desc(), Plot.id.desc())
    )
    plots = list(plots_result.scalars())

    # 2. All members for the farm (with their User records)
    members_result = await session.execute(
        select(FarmMember, User)
        .join(User, User.id == FarmMember.user_id)
        .where(FarmMember.farm_id == farm_id)
    )
    members = list(members_result.all())

    # 3. Recent operations across all farm plots
    operations_result = await session.execute(
        select(FarmOperation, OperationType, Plot)
        .join(OperationType, OperationType.id == FarmOperation.operation_type_id)
        .join(Plot, Plot.id == FarmOperation.plot_id)
        .where(Plot.farm_id == farm_id)
        .order_by(FarmOperation.operated_at.desc(), FarmOperation.id.desc())
        .limit(DASHBOARD_ACTIVITY_LIMIT)
    )
    operations = list(operations_result.all())

    # 4. Recent harvests across all farm plots
    harvests_result = await session.execute(
        select(HarvestRecord, Production, Plot, Species)
        .join(Production, Production.id == HarvestRecord.production_id)
        .join(Plot, Plot.id == Production.plot_id)
        .join(Species, Species.id == Production.species_id)
        .where(Plot.farm_id == farm_id)
        .order_by(HarvestRecord.harvested_at.desc(), HarvestRecord.id.desc())
        .limit(DASHBOARD_ACTIVITY_LIMIT)
    )
    harvests = list(harvests_result.all())

    return plots, members, operations, harvests
