from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException
from app.models.farm import FarmMember
from app.models.operation import FarmOperation, OperationType, OperationTypeStatus
from app.models.plot import Plot
from app.models.production import Production, ProductionStatus, WorkMethod
from app.models.user import User, utc_now_naive
from app.services.plot import get_plot_with_member
from app.services.production import get_production_with_member


def _not_found(message: str) -> AppException:
    return AppException(status_code=404, code=ErrorCode.NOT_FOUND, message=message)


def _conflict(message: str) -> AppException:
    return AppException(status_code=409, code=ErrorCode.BUSINESS_CONFLICT, message=message)


def _validation_error(message: str) -> AppException:
    return AppException(status_code=422, code=ErrorCode.VALIDATION_ERROR, message=message)


def _to_utc_naive(value: datetime) -> datetime:
    return value.astimezone(UTC).replace(tzinfo=None)


def _validate_operated_at(
    operated_at: datetime,
    *,
    production: Production | None,
) -> None:
    if operated_at > utc_now_naive():
        raise _validation_error("operatedAt cannot be later than the current time.")
    if production is not None:
        started_at = datetime.combine(production.started_on, datetime.min.time())
        if operated_at < started_at:
            raise _validation_error("operatedAt cannot be earlier than production.startedOn.")


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
        raise _validation_error("operatorId must belong to the plot's farm.")


async def _get_production_for_plot(
    session: AsyncSession,
    *,
    production_id: int | None,
    plot_id: int,
    user_id: int,
) -> Production | None:
    if production_id is None:
        return None
    production, _, _, _ = await get_production_with_member(
        session,
        production_id=production_id,
        user_id=user_id,
        lock=True,
    )
    if production.plot_id != plot_id:
        raise _validation_error("productionId must belong to the plot.")
    if ProductionStatus(production.status) != ProductionStatus.ACTIVE:
        raise _conflict("An ended production cannot have farm operations changed.")
    return production


async def _get_operation_type(
    session: AsyncSession,
    *,
    operation_type_id: int,
    require_active: bool,
) -> OperationType:
    operation_type = await session.scalar(
        select(OperationType).where(OperationType.id == operation_type_id)
    )
    if operation_type is None:
        raise _validation_error("operationTypeId is invalid.")
    if require_active and OperationTypeStatus(operation_type.status) != OperationTypeStatus.ACTIVE:
        raise _conflict("The selected operation type is unavailable.")
    return operation_type


async def list_operation_types(
    session: AsyncSession,
    *,
    page: int,
    page_size: int,
) -> tuple[list[OperationType], int]:
    filters = [OperationType.status == OperationTypeStatus.ACTIVE]
    total = await session.scalar(select(func.count()).select_from(OperationType).where(*filters))
    result = await session.execute(
        select(OperationType)
        .where(*filters)
        .order_by(OperationType.sort_order.asc(), OperationType.id.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list(result.scalars()), int(total or 0)


async def list_plot_operations(
    session: AsyncSession,
    *,
    plot_id: int,
    user_id: int,
    page: int,
    page_size: int,
) -> tuple[list[tuple[FarmOperation, OperationType]], int]:
    await get_plot_with_member(session, plot_id=plot_id, user_id=user_id)
    filters = [FarmOperation.plot_id == plot_id]
    total = await session.scalar(select(func.count()).select_from(FarmOperation).where(*filters))
    result = await session.execute(
        select(FarmOperation, OperationType)
        .join(OperationType, OperationType.id == FarmOperation.operation_type_id)
        .where(*filters)
        .order_by(FarmOperation.operated_at.desc(), FarmOperation.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list(result.all()), int(total or 0)


async def create_operation(
    session: AsyncSession,
    *,
    plot_id: int,
    user_id: int,
    production_id: int | None,
    operation_type_id: int,
    work_method: WorkMethod,
    operated_at: datetime | None,
    operator_id: int | None,
    remark: str | None,
) -> tuple[FarmOperation, OperationType]:
    plot, _ = await get_plot_with_member(session, plot_id=plot_id, user_id=user_id)
    production = await _get_production_for_plot(
        session,
        production_id=production_id,
        plot_id=plot.id,
        user_id=user_id,
    )
    actual_operated_at = _to_utc_naive(operated_at) if operated_at is not None else utc_now_naive()
    _validate_operated_at(actual_operated_at, production=production)
    actual_operator_id = operator_id if operator_id is not None else user_id
    await _validate_operator(session, farm_id=plot.farm_id, operator_id=actual_operator_id)
    operation_type = await _get_operation_type(
        session,
        operation_type_id=operation_type_id,
        require_active=True,
    )

    operation = FarmOperation(
        plot_id=plot.id,
        production_id=production_id,
        operation_type_id=operation_type.id,
        work_method=work_method,
        operated_at=actual_operated_at,
        operator_id=actual_operator_id,
        created_by=user_id,
        remark=remark,
    )
    session.add(operation)
    await session.commit()
    await session.refresh(operation)
    return operation, operation_type


async def get_operation_with_member(
    session: AsyncSession,
    *,
    operation_id: int,
    user_id: int,
    lock: bool = False,
) -> tuple[FarmOperation, Plot, FarmMember, OperationType]:
    statement = (
        select(FarmOperation, Plot, FarmMember, OperationType)
        .join(Plot, Plot.id == FarmOperation.plot_id)
        .join(FarmMember, FarmMember.farm_id == Plot.farm_id)
        .join(OperationType, OperationType.id == FarmOperation.operation_type_id)
        .where(FarmOperation.id == operation_id, FarmMember.user_id == user_id)
    )
    if lock:
        statement = statement.with_for_update()
    result = await session.execute(statement)
    operation_and_context = result.one_or_none()
    if operation_and_context is None:
        raise _not_found("Farm operation not found.")
    return operation_and_context


async def _ensure_operation_is_editable(
    session: AsyncSession, operation: FarmOperation
) -> Production | None:
    if operation.production_id is None:
        return None
    production = await session.scalar(
        select(Production).where(Production.id == operation.production_id).with_for_update()
    )
    if production is None:
        raise _not_found("Production not found.")
    if ProductionStatus(production.status) != ProductionStatus.ACTIVE:
        raise _conflict("Farm operations linked to an ended production cannot be changed.")
    return production


async def update_operation(
    session: AsyncSession,
    *,
    operation_id: int,
    user_id: int,
    production_id: int | None,
    operation_type_id: int | None,
    work_method: WorkMethod | None,
    operated_at: datetime | None,
    operator_id: int | None,
    remark: str | None,
    fields_set: set[str],
) -> tuple[FarmOperation, OperationType]:
    operation, plot, _, current_operation_type = await get_operation_with_member(
        session,
        operation_id=operation_id,
        user_id=user_id,
        lock=True,
    )
    await _ensure_operation_is_editable(session, operation)
    target_operation_type = current_operation_type
    if "operation_type_id" in fields_set:
        if operation_type_id is None:
            raise _validation_error("operationTypeId cannot be null.")
        target_operation_type = await _get_operation_type(
            session,
            operation_type_id=operation_type_id,
            require_active=operation_type_id != current_operation_type.id,
        )
    target_production_id = (
        production_id if "production_id" in fields_set else operation.production_id
    )
    target_production = await _get_production_for_plot(
        session,
        production_id=target_production_id,
        plot_id=plot.id,
        user_id=user_id,
    )
    target_operated_at = operation.operated_at
    if "operated_at" in fields_set and operated_at is not None:
        target_operated_at = _to_utc_naive(operated_at)
    if {"operated_at", "production_id"} & fields_set:
        _validate_operated_at(target_operated_at, production=target_production)
    target_operator_id = operator_id if "operator_id" in fields_set else operation.operator_id
    if target_operator_id is None:
        raise _validation_error("operatorId cannot be null.")
    await _validate_operator(session, farm_id=plot.farm_id, operator_id=target_operator_id)

    if "production_id" in fields_set:
        operation.production_id = production_id
    if "operation_type_id" in fields_set:
        operation.operation_type_id = target_operation_type.id
    if "work_method" in fields_set:
        if work_method is None:
            raise _validation_error("workMethod cannot be null.")
        operation.work_method = work_method
    if "operated_at" in fields_set:
        if operated_at is None:
            raise _validation_error("operatedAt cannot be null.")
        operation.operated_at = target_operated_at
    if "operator_id" in fields_set:
        operation.operator_id = target_operator_id
    if "remark" in fields_set:
        operation.remark = remark

    await session.commit()
    await session.refresh(operation)
    return operation, target_operation_type


async def delete_operation(
    session: AsyncSession,
    *,
    operation_id: int,
    user_id: int,
) -> None:
    operation, _, _, _ = await get_operation_with_member(
        session,
        operation_id=operation_id,
        user_id=user_id,
        lock=True,
    )
    await _ensure_operation_is_editable(session, operation)
    await session.delete(operation)
    await session.commit()
