from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException
from app.models.farm import FarmMember, FarmMemberRole
from app.models.plot import AreaUnit, Plot, PlotType
from app.services.farm import get_farm_with_member

MU_TO_M2 = Decimal("666.6666666667")
HECTARE_TO_M2 = Decimal("10000")


def _not_found(message: str) -> AppException:
    return AppException(status_code=404, code=ErrorCode.NOT_FOUND, message=message)


def _forbidden(message: str) -> AppException:
    return AppException(status_code=403, code=ErrorCode.FORBIDDEN, message=message)


def _require_plot_management_role(role: FarmMemberRole | str) -> None:
    if FarmMemberRole(role) not in (FarmMemberRole.OWNER, FarmMemberRole.ADMIN):
        raise _forbidden("You do not have permission to manage plots.")


def calculate_area_m2(area_value: Decimal | None, area_unit: AreaUnit | None) -> Decimal | None:
    if area_value is None or area_unit is None:
        return None
    if area_unit == AreaUnit.MU:
        return area_value * MU_TO_M2
    if area_unit == AreaUnit.HECTARE:
        return area_value * HECTARE_TO_M2
    return area_value


async def list_plots(
    session: AsyncSession,
    *,
    farm_id: int,
    user_id: int,
    page: int,
    page_size: int,
) -> tuple[list[Plot], int]:
    await get_farm_with_member(session, farm_id=farm_id, user_id=user_id)
    total = await session.scalar(
        select(func.count()).select_from(Plot).where(Plot.farm_id == farm_id)
    )
    result = await session.execute(
        select(Plot)
        .where(Plot.farm_id == farm_id)
        .order_by(Plot.created_at.desc(), Plot.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list(result.scalars()), int(total or 0)


async def create_plot(
    session: AsyncSession,
    *,
    farm_id: int,
    user_id: int,
    name: str,
    plot_type: PlotType | None,
    area_value: Decimal | None,
    area_unit: AreaUnit | None,
    boundary: dict[str, Any] | None,
) -> Plot:
    _, member = await get_farm_with_member(session, farm_id=farm_id, user_id=user_id)
    _require_plot_management_role(member.role)
    plot = Plot(
        farm_id=farm_id,
        name=name,
        plot_type=plot_type,
        area_value=area_value,
        area_unit=area_unit,
        area_m2=calculate_area_m2(area_value, area_unit),
        boundary=boundary,
    )
    session.add(plot)
    await session.commit()
    await session.refresh(plot)
    return plot


async def get_plot_with_member(
    session: AsyncSession,
    *,
    plot_id: int,
    user_id: int,
) -> tuple[Plot, FarmMember]:
    result = await session.execute(
        select(Plot, FarmMember)
        .join(FarmMember, FarmMember.farm_id == Plot.farm_id)
        .where(Plot.id == plot_id, FarmMember.user_id == user_id)
    )
    plot_and_member = result.one_or_none()
    if plot_and_member is None:
        raise _not_found("Plot not found.")
    return plot_and_member


async def update_plot(
    session: AsyncSession,
    *,
    plot_id: int,
    user_id: int,
    name: str | None,
    plot_type: PlotType | None,
    area_value: Decimal | None,
    area_unit: AreaUnit | None,
    boundary: dict[str, Any] | None,
    fields_set: set[str],
) -> Plot:
    result = await session.execute(
        select(Plot, FarmMember)
        .join(FarmMember, FarmMember.farm_id == Plot.farm_id)
        .where(Plot.id == plot_id, FarmMember.user_id == user_id)
        .with_for_update()
    )
    plot_and_member = result.one_or_none()
    if plot_and_member is None:
        raise _not_found("Plot not found.")
    plot, member = plot_and_member
    _require_plot_management_role(member.role)

    if "name" in fields_set:
        plot.name = name  # type: ignore[assignment]
    if "plot_type" in fields_set:
        plot.plot_type = plot_type
    if {"area_value", "area_unit"}.issubset(fields_set):
        plot.area_value = area_value
        plot.area_unit = area_unit
        plot.area_m2 = calculate_area_m2(area_value, area_unit)
    if "boundary" in fields_set:
        plot.boundary = boundary
    await session.commit()
    await session.refresh(plot)
    return plot
