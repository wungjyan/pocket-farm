from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException
from app.models.farm import FarmMember
from app.models.harvest import HarvestRecord
from app.models.plot import Plot
from app.models.production import Production, ProductionStatus, QuantityUnit, WorkMethod
from app.models.species import Industry, Species
from app.models.user import User, utc_now_naive
from app.services.farm import get_farm_with_member
from app.services.plot import get_plot_with_member
from app.services.production import get_production_with_member

INTEGER_UNITS = {
    QuantityUnit.HEAD,
    QuantityUnit.FEATHER,
    QuantityUnit.PIECE,
    QuantityUnit.PLANT,
    QuantityUnit.TAIL,
}

WEIGHT_HARVEST_INDUSTRIES = {Industry.AGRICULTURE, Industry.FISHERY}


def _not_found(message: str) -> AppException:
    return AppException(status_code=404, code=ErrorCode.NOT_FOUND, message=message)


def _conflict(message: str) -> AppException:
    return AppException(status_code=409, code=ErrorCode.BUSINESS_CONFLICT, message=message)


def _validation_error(message: str) -> AppException:
    return AppException(status_code=422, code=ErrorCode.VALIDATION_ERROR, message=message)


def _to_utc_naive(value: datetime) -> datetime:
    return value.astimezone(UTC).replace(tzinfo=None)


def _validate_quantity(quantity: Decimal, unit: QuantityUnit) -> None:
    if quantity <= 0:
        raise _validation_error("quantity must be greater than 0.")
    if unit in INTEGER_UNITS and quantity != quantity.to_integral_value():
        raise _validation_error(f"quantity must be an integer when unit is {unit.value}.")


def _harvest_unit(species: Species) -> QuantityUnit:
    if Industry(species.industry) in WEIGHT_HARVEST_INDUSTRIES:
        return QuantityUnit.KG
    return QuantityUnit(species.individual_unit)


def _validate_harvested_at(harvested_at: datetime, *, production: Production) -> None:
    if harvested_at > utc_now_naive():
        raise _validation_error("harvestedAt cannot be later than the current time.")
    started_at = datetime.combine(production.started_on, datetime.min.time())
    if harvested_at < started_at:
        raise _validation_error("harvestedAt cannot be earlier than production.startedOn.")


def _ensure_production_is_active(production: Production) -> None:
    if ProductionStatus(production.status) != ProductionStatus.ACTIVE:
        raise _conflict("An ended production cannot have harvest records changed.")


async def _validate_operator(
    session: AsyncSession,
    *,
    farm_id: int,
    operator_id: int,
) -> None:
    result = await session.execute(
        select(User.id)
        .join(FarmMember, FarmMember.user_id == User.id)
        .where(User.id == operator_id, FarmMember.farm_id == farm_id)
    )
    if result.scalar_one_or_none() is None:
        raise _validation_error("operatorId must belong to the production's farm.")


async def list_production_harvests(
    session: AsyncSession,
    *,
    production_id: int,
    user_id: int,
    page: int,
    page_size: int,
) -> tuple[list[HarvestRecord], int]:
    await get_production_with_member(session, production_id=production_id, user_id=user_id)
    filters = [HarvestRecord.production_id == production_id]
    total = await session.scalar(select(func.count()).select_from(HarvestRecord).where(*filters))
    result = await session.execute(
        select(HarvestRecord)
        .where(*filters)
        .order_by(HarvestRecord.harvested_at.desc(), HarvestRecord.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list(result.scalars()), int(total or 0)


async def list_plot_harvests(
    session: AsyncSession,
    *,
    plot_id: int,
    user_id: int,
    page: int,
    page_size: int,
) -> tuple[list[HarvestRecord], int]:
    await get_plot_with_member(session, plot_id=plot_id, user_id=user_id)
    filters = [Production.plot_id == plot_id]
    total = await session.scalar(
        select(func.count())
        .select_from(HarvestRecord)
        .join(Production, Production.id == HarvestRecord.production_id)
        .where(*filters)
    )
    result = await session.execute(
        select(HarvestRecord)
        .join(Production, Production.id == HarvestRecord.production_id)
        .where(*filters)
        .order_by(HarvestRecord.harvested_at.desc(), HarvestRecord.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list(result.scalars()), int(total or 0)


async def list_farm_harvests(
    session: AsyncSession,
    *,
    farm_id: int,
    user_id: int,
    industry: Industry | None,
    species_id: int | None,
    page: int,
    page_size: int,
) -> tuple[
    list[
        tuple[
            HarvestRecord,
            Production,
            Plot,
            Species,
            User | None,
            User | None,
        ]
    ],
    int,
]:
    await get_farm_with_member(session, farm_id=farm_id, user_id=user_id)
    filters = [Plot.farm_id == farm_id]
    if industry is not None:
        filters.append(Species.industry == industry)
    if species_id is not None:
        filters.append(Production.species_id == species_id)

    total = await session.scalar(
        select(func.count())
        .select_from(HarvestRecord)
        .join(Production, Production.id == HarvestRecord.production_id)
        .join(Plot, Plot.id == Production.plot_id)
        .join(Species, Species.id == Production.species_id)
        .where(*filters)
    )
    operator = aliased(User)
    creator = aliased(User)
    result = await session.execute(
        select(HarvestRecord, Production, Plot, Species, operator, creator)
        .join(Production, Production.id == HarvestRecord.production_id)
        .join(Plot, Plot.id == Production.plot_id)
        .join(Species, Species.id == Production.species_id)
        .outerjoin(operator, operator.id == HarvestRecord.operator_id)
        .outerjoin(creator, creator.id == HarvestRecord.created_by)
        .where(*filters)
        .order_by(HarvestRecord.harvested_at.desc(), HarvestRecord.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list(result.all()), int(total or 0)


async def get_farm_harvest_filter_options(
    session: AsyncSession,
    *,
    farm_id: int,
    user_id: int,
    industry: Industry,
) -> list[tuple[int, str]]:
    await get_farm_with_member(session, farm_id=farm_id, user_id=user_id)
    result = await session.execute(
        select(Species.id, Species.name)
        .join(Production, Production.species_id == Species.id)
        .join(HarvestRecord, HarvestRecord.production_id == Production.id)
        .join(Plot, Plot.id == Production.plot_id)
        .where(Plot.farm_id == farm_id, Species.industry == industry)
        .distinct()
        .order_by(Species.name.asc(), Species.id.asc())
    )
    return list(result.all())


async def create_harvest(
    session: AsyncSession,
    *,
    production_id: int,
    user_id: int,
    quantity: Decimal,
    work_method: WorkMethod,
    harvested_at: datetime | None,
    operator_id: int | None,
    product_name: str | None,
    grade: str | None,
    remark: str | None,
) -> HarvestRecord:
    production, plot, _, species = await get_production_with_member(
        session,
        production_id=production_id,
        user_id=user_id,
        lock=True,
    )
    _ensure_production_is_active(production)
    unit = _harvest_unit(species)
    _validate_quantity(quantity, unit)
    actual_harvested_at = (
        _to_utc_naive(harvested_at) if harvested_at is not None else utc_now_naive()
    )
    _validate_harvested_at(actual_harvested_at, production=production)
    actual_operator_id = operator_id if operator_id is not None else user_id
    await _validate_operator(session, farm_id=plot.farm_id, operator_id=actual_operator_id)

    harvest = HarvestRecord(
        production_id=production.id,
        quantity=quantity,
        unit=unit,
        work_method=work_method,
        harvested_at=actual_harvested_at,
        operator_id=actual_operator_id,
        created_by=user_id,
        product_name=product_name if product_name is not None else species.name,
        grade=grade,
        remark=remark,
    )
    session.add(harvest)
    await session.commit()
    await session.refresh(harvest)
    return harvest


async def get_harvest_with_member(
    session: AsyncSession,
    *,
    harvest_id: int,
    user_id: int,
    lock: bool = False,
) -> tuple[HarvestRecord, Production, Plot, FarmMember]:
    statement = (
        select(HarvestRecord, Production, Plot, FarmMember)
        .join(Production, Production.id == HarvestRecord.production_id)
        .join(Plot, Plot.id == Production.plot_id)
        .join(FarmMember, FarmMember.farm_id == Plot.farm_id)
        .where(HarvestRecord.id == harvest_id, FarmMember.user_id == user_id)
    )
    if lock:
        statement = statement.with_for_update()
    result = await session.execute(statement)
    harvest_and_context = result.one_or_none()
    if harvest_and_context is None:
        raise _not_found("Harvest record not found.")
    return harvest_and_context


async def update_harvest(
    session: AsyncSession,
    *,
    harvest_id: int,
    user_id: int,
    quantity: Decimal | None,
    work_method: WorkMethod | None,
    harvested_at: datetime | None,
    operator_id: int | None,
    product_name: str | None,
    grade: str | None,
    remark: str | None,
    fields_set: set[str],
) -> HarvestRecord:
    harvest, production, plot, _ = await get_harvest_with_member(
        session,
        harvest_id=harvest_id,
        user_id=user_id,
        lock=True,
    )
    _ensure_production_is_active(production)

    target_quantity = quantity if "quantity" in fields_set else harvest.quantity
    target_unit = QuantityUnit(harvest.unit)
    if target_quantity is None:
        raise _validation_error("quantity cannot be null.")
    _validate_quantity(target_quantity, target_unit)

    target_harvested_at = harvest.harvested_at
    if "harvested_at" in fields_set:
        if harvested_at is None:
            raise _validation_error("harvestedAt cannot be null.")
        target_harvested_at = _to_utc_naive(harvested_at)
        _validate_harvested_at(target_harvested_at, production=production)

    target_operator_id = operator_id if "operator_id" in fields_set else harvest.operator_id
    if target_operator_id is None:
        raise _validation_error("operatorId cannot be null.")
    await _validate_operator(session, farm_id=plot.farm_id, operator_id=target_operator_id)

    if "quantity" in fields_set:
        harvest.quantity = target_quantity
    if "work_method" in fields_set:
        if work_method is None:
            raise _validation_error("workMethod cannot be null.")
        harvest.work_method = work_method
    if "harvested_at" in fields_set:
        harvest.harvested_at = target_harvested_at
    if "operator_id" in fields_set:
        harvest.operator_id = target_operator_id
    if "product_name" in fields_set:
        harvest.product_name = product_name
    if "grade" in fields_set:
        harvest.grade = grade
    if "remark" in fields_set:
        harvest.remark = remark

    await session.commit()
    await session.refresh(harvest)
    return harvest


async def delete_harvest(
    session: AsyncSession,
    *,
    harvest_id: int,
    user_id: int,
) -> None:
    harvest, production, _, _ = await get_harvest_with_member(
        session,
        harvest_id=harvest_id,
        user_id=user_id,
        lock=True,
    )
    _ensure_production_is_active(production)
    await session.delete(harvest)
    await session.commit()
