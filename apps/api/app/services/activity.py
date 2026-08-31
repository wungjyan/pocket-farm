from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.models.harvest import HarvestRecord
from app.models.operation import FarmOperation, OperationType
from app.models.plot import Plot
from app.models.production import Production, ProductionStatus, QuantityUnit
from app.models.species import Industry, Species
from app.models.user import User
from app.services.farm import get_farm_with_member

FarmActivityType = Literal[
    "PRODUCTION_STARTED",
    "PRODUCTION_ENDED",
    "OPERATION_CREATED",
    "HARVEST_CREATED",
]


@dataclass(frozen=True)
class FarmActivity:
    type: FarmActivityType
    occurred_at: datetime
    production_id: int | None
    operation_id: int | None
    harvest_id: int | None
    plot: Plot
    species_name: str | None
    industry: Industry | None
    operation_type_name: str | None
    quantity: Decimal | None
    unit: QuantityUnit | None
    operator_name: str | None


async def list_farm_activities(
    session: AsyncSession,
    *,
    farm_id: int,
    user_id: int,
    limit: int,
) -> list[FarmActivity]:
    await get_farm_with_member(session, farm_id=farm_id, user_id=user_id)
    operator = aliased(User)

    started_result = await session.execute(
        select(Production, Plot, Species)
        .join(Plot, Plot.id == Production.plot_id)
        .join(Species, Species.id == Production.species_id)
        .where(Plot.farm_id == farm_id)
        .order_by(Production.created_at.desc(), Production.id.desc())
        .limit(limit)
    )
    started = [
        FarmActivity(
            type="PRODUCTION_STARTED",
            occurred_at=production.created_at,
            production_id=production.id,
            operation_id=None,
            harvest_id=None,
            plot=plot,
            species_name=species.name,
            industry=Industry(species.industry),
            operation_type_name=None,
            quantity=None,
            unit=None,
            operator_name=None,
        )
        for production, plot, species in started_result.all()
    ]

    ended_result = await session.execute(
        select(Production, Plot, Species)
        .join(Plot, Plot.id == Production.plot_id)
        .join(Species, Species.id == Production.species_id)
        .where(
            Plot.farm_id == farm_id,
            Production.status == ProductionStatus.ENDED,
            Production.ended_at.is_not(None),
        )
        .order_by(Production.ended_at.desc(), Production.id.desc())
        .limit(limit)
    )
    ended = [
        FarmActivity(
            type="PRODUCTION_ENDED",
            occurred_at=production.ended_at,
            production_id=production.id,
            operation_id=None,
            harvest_id=None,
            plot=plot,
            species_name=species.name,
            industry=Industry(species.industry),
            operation_type_name=None,
            quantity=None,
            unit=None,
            operator_name=None,
        )
        for production, plot, species in ended_result.all()
        if production.ended_at is not None
    ]

    operations_result = await session.execute(
        select(FarmOperation, OperationType, Plot, Species, operator)
        .join(Plot, Plot.id == FarmOperation.plot_id)
        .join(OperationType, OperationType.id == FarmOperation.operation_type_id)
        .outerjoin(Production, Production.id == FarmOperation.production_id)
        .outerjoin(Species, Species.id == Production.species_id)
        .outerjoin(operator, operator.id == FarmOperation.operator_id)
        .where(Plot.farm_id == farm_id)
        .order_by(FarmOperation.created_at.desc(), FarmOperation.id.desc())
        .limit(limit)
    )
    operations = [
        FarmActivity(
            type="OPERATION_CREATED",
            occurred_at=operation.created_at,
            production_id=operation.production_id,
            operation_id=operation.id,
            harvest_id=None,
            plot=plot,
            species_name=species.name if species else None,
            industry=Industry(species.industry) if species else None,
            operation_type_name=operation_type.name,
            quantity=None,
            unit=None,
            operator_name=user.nickname if user else None,
        )
        for operation, operation_type, plot, species, user in operations_result.all()
    ]

    harvests_result = await session.execute(
        select(HarvestRecord, Production, Plot, Species, operator)
        .join(Production, Production.id == HarvestRecord.production_id)
        .join(Plot, Plot.id == Production.plot_id)
        .join(Species, Species.id == Production.species_id)
        .outerjoin(operator, operator.id == HarvestRecord.operator_id)
        .where(Plot.farm_id == farm_id)
        .order_by(HarvestRecord.created_at.desc(), HarvestRecord.id.desc())
        .limit(limit)
    )
    harvests = [
        FarmActivity(
            type="HARVEST_CREATED",
            occurred_at=harvest.created_at,
            production_id=production.id,
            operation_id=None,
            harvest_id=harvest.id,
            plot=plot,
            species_name=species.name,
            industry=Industry(species.industry),
            operation_type_name=None,
            quantity=harvest.quantity,
            unit=QuantityUnit(harvest.unit),
            operator_name=user.nickname if user else None,
        )
        for harvest, production, plot, species, user in harvests_result.all()
    ]

    return sorted(
        [*started, *ended, *operations, *harvests],
        key=lambda activity: activity.occurred_at,
        reverse=True,
    )[:limit]
