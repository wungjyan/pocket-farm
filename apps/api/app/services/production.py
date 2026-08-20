from datetime import date, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException
from app.models.farm import FarmMember
from app.models.harvest import HarvestRecord
from app.models.operation import FarmOperation
from app.models.plot import Plot
from app.models.production import (
    PlantingMethod,
    PlantingStandard,
    Production,
    ProductionStatus,
    WorkMethod,
)
from app.models.species import Industry, Species
from app.services.plot import get_plot_with_member

PLANTING_INDUSTRIES = {Industry.AGRICULTURE, Industry.FORESTRY}


def _not_found(message: str) -> AppException:
    return AppException(status_code=404, code=ErrorCode.NOT_FOUND, message=message)


def _conflict(message: str) -> AppException:
    return AppException(status_code=409, code=ErrorCode.BUSINESS_CONFLICT, message=message)


def _validation_error(message: str) -> AppException:
    return AppException(status_code=422, code=ErrorCode.VALIDATION_ERROR, message=message)


def _today() -> date:
    return datetime.now(ZoneInfo(settings.app_timezone)).date()


def _validate_started_on(started_on: date) -> None:
    if started_on > _today():
        raise _validation_error("startedOn cannot be later than today.")


def _business_date(value: datetime) -> date:
    return value.replace(tzinfo=ZoneInfo("UTC")).astimezone(ZoneInfo(settings.app_timezone)).date()


def _require(value: object | None, field_name: str) -> None:
    if value is None:
        raise _validation_error(f"{field_name} is required for this industry.")


def _forbid(value: object | None, field_name: str, industry: Industry) -> None:
    if value is not None:
        raise _validation_error(f"{field_name} does not apply to {industry.value} productions.")


def _validate_industry_fields(
    *,
    industry: Industry,
    planting_standard: PlantingStandard | None,
    planting_method: PlantingMethod | None,
    work_method: WorkMethod | None,
    expected_harvest_on: date | None,
    expected_yield_per_mu: Decimal | None,
    initial_quantity: Decimal | None,
    plant_spacing_cm: Decimal | None,
    entry_age_days: int | None,
) -> None:
    if initial_quantity is not None and initial_quantity != initial_quantity.to_integral_value():
        raise _validation_error("initialQuantity must be an integer for the selected species unit.")

    if industry in PLANTING_INDUSTRIES:
        _require(planting_standard, "plantingStandard")
        _require(planting_method, "plantingMethod")
        _require(work_method, "workMethod")
        _forbid(entry_age_days, "entryAgeDays", industry)
        if industry == Industry.FORESTRY:
            _require(initial_quantity, "initialQuantity")
            _forbid(expected_yield_per_mu, "expectedYieldPerMu", industry)
        return

    _forbid(planting_standard, "plantingStandard", industry)
    _forbid(planting_method, "plantingMethod", industry)
    _forbid(expected_harvest_on, "expectedHarvestOn", industry)
    _forbid(expected_yield_per_mu, "expectedYieldPerMu", industry)
    _forbid(plant_spacing_cm, "plantSpacingCm", industry)

    if industry == Industry.LIVESTOCK:
        _require(initial_quantity, "initialQuantity")
        _require(entry_age_days, "entryAgeDays")
        _forbid(work_method, "workMethod", industry)
        return

    _require(initial_quantity, "initialQuantity")
    _require(work_method, "workMethod")
    _forbid(entry_age_days, "entryAgeDays", industry)


async def _get_species(session: AsyncSession, species_id: int) -> Species:
    species = await session.scalar(select(Species).where(Species.id == species_id))
    if species is None:
        raise _not_found("Species not found.")
    return species


async def list_plot_productions(
    session: AsyncSession,
    *,
    plot_id: int,
    user_id: int,
    status: ProductionStatus | None,
    page: int,
    page_size: int,
) -> tuple[list[tuple[Production, Species]], int]:
    await get_plot_with_member(session, plot_id=plot_id, user_id=user_id)
    filters = [Production.plot_id == plot_id]
    if status is not None:
        filters.append(Production.status == status)
    total = await session.scalar(select(func.count()).select_from(Production).where(*filters))
    result = await session.execute(
        select(Production, Species)
        .join(Species, Species.id == Production.species_id)
        .where(*filters)
        .order_by(
            case((Production.status == ProductionStatus.ACTIVE, 0), else_=1),
            Production.started_on.desc(),
            Production.id.desc(),
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list(result.all()), int(total or 0)


async def get_production_with_member(
    session: AsyncSession,
    *,
    production_id: int,
    user_id: int,
    lock: bool = False,
) -> tuple[Production, Plot, FarmMember, Species]:
    statement = (
        select(Production, Plot, FarmMember, Species)
        .join(Plot, Plot.id == Production.plot_id)
        .join(FarmMember, FarmMember.farm_id == Plot.farm_id)
        .join(Species, Species.id == Production.species_id)
        .where(Production.id == production_id, FarmMember.user_id == user_id)
    )
    if lock:
        statement = statement.with_for_update()
    result = await session.execute(statement)
    production_and_context = result.one_or_none()
    if production_and_context is None:
        raise _not_found("Production not found.")
    return production_and_context


async def create_production(
    session: AsyncSession,
    *,
    plot_id: int,
    user_id: int,
    species_id: int,
    variety: str | None,
    started_on: date,
    planting_standard: PlantingStandard | None,
    planting_method: PlantingMethod | None,
    work_method: WorkMethod | None,
    expected_harvest_on: date | None,
    expected_yield_per_mu: Decimal | None,
    initial_quantity: Decimal | None,
    plant_spacing_cm: Decimal | None,
    entry_age_days: int | None,
    remark: str | None,
) -> tuple[Production, Species]:
    await get_plot_with_member(session, plot_id=plot_id, user_id=user_id)
    species = await _get_species(session, species_id)
    industry = Industry(species.industry)
    _validate_started_on(started_on)
    _validate_industry_fields(
        industry=industry,
        planting_standard=planting_standard,
        planting_method=planting_method,
        work_method=work_method,
        expected_harvest_on=expected_harvest_on,
        expected_yield_per_mu=expected_yield_per_mu,
        initial_quantity=initial_quantity,
        plant_spacing_cm=plant_spacing_cm,
        entry_age_days=entry_age_days,
    )

    production = Production(
        plot_id=plot_id,
        species_id=species_id,
        variety=variety,
        status=ProductionStatus.ACTIVE,
        started_on=started_on,
        planting_standard=planting_standard,
        planting_method=planting_method,
        work_method=work_method,
        expected_harvest_on=expected_harvest_on,
        expected_yield_per_mu=expected_yield_per_mu,
        initial_quantity=initial_quantity,
        plant_spacing_cm=plant_spacing_cm,
        entry_age_days=entry_age_days,
        remark=remark,
    )
    session.add(production)
    await session.commit()
    await session.refresh(production)
    return production, species


async def update_production(
    session: AsyncSession,
    *,
    production_id: int,
    user_id: int,
    plot_id: int | None,
    species_id: int | None,
    variety: str | None,
    started_on: date | None,
    planting_standard: PlantingStandard | None,
    planting_method: PlantingMethod | None,
    work_method: WorkMethod | None,
    expected_harvest_on: date | None,
    expected_yield_per_mu: Decimal | None,
    initial_quantity: Decimal | None,
    plant_spacing_cm: Decimal | None,
    entry_age_days: int | None,
    remark: str | None,
    fields_set: set[str],
) -> tuple[Production, Species]:
    production, current_plot, _, current_species = await get_production_with_member(
        session,
        production_id=production_id,
        user_id=user_id,
        lock=True,
    )
    if ProductionStatus(production.status) != ProductionStatus.ACTIVE:
        raise _conflict("An ended production cannot be edited.")

    core_fields = {"plot_id", "species_id", "started_on"}
    if core_fields & fields_set:
        operation_count = await session.scalar(
            select(func.count())
            .select_from(FarmOperation)
            .where(FarmOperation.production_id == production.id)
        )
        if operation_count:
            raise _conflict(
                "Production plotId, speciesId, and startedOn cannot be changed "
                "after operations exist."
            )
        harvest_count = await session.scalar(
            select(func.count())
            .select_from(HarvestRecord)
            .where(HarvestRecord.production_id == production.id)
        )
        if harvest_count:
            raise _conflict(
                "Production plotId, speciesId, and startedOn cannot be changed "
                "after harvest records exist."
            )

    target_plot = current_plot
    if "plot_id" in fields_set:
        target_plot, _ = await get_plot_with_member(session, plot_id=plot_id, user_id=user_id)  # type: ignore[arg-type]
        if target_plot.farm_id != current_plot.farm_id:
            raise _conflict("A production can only be moved within the same farm.")

    target_species = current_species
    if "species_id" in fields_set:
        target_species = await _get_species(session, species_id)  # type: ignore[arg-type]

    target_started_on = started_on if "started_on" in fields_set else production.started_on
    target_planting_standard = (
        planting_standard
        if "planting_standard" in fields_set
        else PlantingStandard(production.planting_standard)
        if production.planting_standard is not None
        else None
    )
    target_planting_method = (
        planting_method
        if "planting_method" in fields_set
        else PlantingMethod(production.planting_method)
        if production.planting_method is not None
        else None
    )
    target_work_method = (
        work_method
        if "work_method" in fields_set
        else WorkMethod(production.work_method)
        if production.work_method is not None
        else None
    )
    target_expected_harvest_on = (
        expected_harvest_on
        if "expected_harvest_on" in fields_set
        else production.expected_harvest_on
    )
    target_expected_yield_per_mu = (
        expected_yield_per_mu
        if "expected_yield_per_mu" in fields_set
        else production.expected_yield_per_mu
    )
    target_initial_quantity = (
        initial_quantity if "initial_quantity" in fields_set else production.initial_quantity
    )
    target_plant_spacing_cm = (
        plant_spacing_cm if "plant_spacing_cm" in fields_set else production.plant_spacing_cm
    )
    target_entry_age_days = (
        entry_age_days if "entry_age_days" in fields_set else production.entry_age_days
    )
    _validate_started_on(target_started_on)
    _validate_industry_fields(
        industry=Industry(target_species.industry),
        planting_standard=target_planting_standard,
        planting_method=target_planting_method,
        work_method=target_work_method,
        expected_harvest_on=target_expected_harvest_on,
        expected_yield_per_mu=target_expected_yield_per_mu,
        initial_quantity=target_initial_quantity,
        plant_spacing_cm=target_plant_spacing_cm,
        entry_age_days=target_entry_age_days,
    )

    if "plot_id" in fields_set:
        production.plot_id = target_plot.id
    if "species_id" in fields_set:
        production.species_id = target_species.id
    if "variety" in fields_set:
        production.variety = variety
    if "started_on" in fields_set:
        production.started_on = started_on  # type: ignore[assignment]
    if "planting_standard" in fields_set:
        production.planting_standard = planting_standard
    if "planting_method" in fields_set:
        production.planting_method = planting_method
    if "work_method" in fields_set:
        production.work_method = work_method
    if "expected_harvest_on" in fields_set:
        production.expected_harvest_on = expected_harvest_on
    if "expected_yield_per_mu" in fields_set:
        production.expected_yield_per_mu = expected_yield_per_mu
    if "initial_quantity" in fields_set:
        production.initial_quantity = initial_quantity
    if "plant_spacing_cm" in fields_set:
        production.plant_spacing_cm = plant_spacing_cm
    if "entry_age_days" in fields_set:
        production.entry_age_days = entry_age_days
    if "remark" in fields_set:
        production.remark = remark

    await session.commit()
    await session.refresh(production)
    return production, target_species


async def delete_production(
    session: AsyncSession,
    *,
    production_id: int,
    user_id: int,
) -> None:
    production, _, _, _ = await get_production_with_member(
        session,
        production_id=production_id,
        user_id=user_id,
        lock=True,
    )
    if ProductionStatus(production.status) != ProductionStatus.ACTIVE:
        raise _conflict("An ended production cannot be deleted.")

    operation_count = await session.scalar(
        select(func.count())
        .select_from(FarmOperation)
        .where(FarmOperation.production_id == production.id)
    )
    if operation_count:
        raise _conflict("A production with farm operations cannot be deleted.")

    harvest_count = await session.scalar(
        select(func.count())
        .select_from(HarvestRecord)
        .where(HarvestRecord.production_id == production.id)
    )
    if harvest_count:
        raise _conflict("A production with harvest records cannot be deleted.")

    await session.delete(production)
    await session.commit()


async def end_production(
    session: AsyncSession,
    *,
    production_id: int,
    user_id: int,
    ended_on: date | None,
) -> tuple[Production, Species]:
    production, _, _, species = await get_production_with_member(
        session,
        production_id=production_id,
        user_id=user_id,
        lock=True,
    )
    if ProductionStatus(production.status) != ProductionStatus.ACTIVE:
        raise _conflict("This production has already ended.")

    actual_ended_on = ended_on or _today()
    if actual_ended_on > _today():
        raise _validation_error("endedOn cannot be later than today.")
    if actual_ended_on < production.started_on:
        raise _validation_error("endedOn cannot be earlier than production.startedOn.")

    latest_operation_at = await session.scalar(
        select(func.max(FarmOperation.operated_at)).where(
            FarmOperation.production_id == production.id
        )
    )
    if latest_operation_at is not None and actual_ended_on < _business_date(latest_operation_at):
        raise _validation_error("endedOn cannot be earlier than an associated farm operation.")

    latest_harvested_at = await session.scalar(
        select(func.max(HarvestRecord.harvested_at)).where(
            HarvestRecord.production_id == production.id
        )
    )
    if latest_harvested_at is not None and actual_ended_on < _business_date(latest_harvested_at):
        raise _validation_error("endedOn cannot be earlier than an associated harvest record.")

    production.status = ProductionStatus.ENDED
    production.ended_on = actual_ended_on
    await session.commit()
    await session.refresh(production)
    return production, species
