from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.models.plot import PlotType
from app.models.user import User
from app.schemas.farm import (
    CreatePlotRequest,
    PlotPage,
    PlotResponse,
    UpdatePlotRequest,
)
from app.schemas.response import ApiResponse
from app.services.plot import (
    create_plot,
    get_plot_with_member,
    list_plots,
    update_plot,
)

router = APIRouter(tags=["plots"])


def _plot_response(plot) -> PlotResponse:
    return PlotResponse(
        id=plot.id,
        farm_id=plot.farm_id,
        name=plot.name,
        plot_type=PlotType(plot.plot_type) if plot.plot_type is not None else None,
        area_value=plot.area_value,
        area_unit=plot.area_unit,
        area_m2=plot.area_m2,
        boundary=plot.boundary,
        created_at=plot.created_at,
        updated_at=plot.updated_at,
    )


@router.get("/farms/{farm_id}/plots", response_model=ApiResponse[PlotPage])
async def get_farm_plots(
    farm_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(alias="pageSize", ge=1, le=100)] = 20,
) -> ApiResponse[PlotPage]:
    plots, total = await list_plots(
        session,
        farm_id=farm_id,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
    )
    return ApiResponse.success_response(
        data=PlotPage(
            items=[_plot_response(plot) for plot in plots],
            page=page,
            page_size=page_size,
            total=total,
        )
    )


@router.post(
    "/farms/{farm_id}/plots",
    response_model=ApiResponse[PlotResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_farm_plot(
    farm_id: int,
    request: CreatePlotRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[PlotResponse]:
    plot = await create_plot(
        session,
        farm_id=farm_id,
        user_id=current_user.id,
        name=request.name,
        plot_type=request.plot_type,
        area_value=request.area_value,
        area_unit=request.area_unit,
        boundary=request.boundary,
    )
    return ApiResponse.success_response(data=_plot_response(plot))


@router.get("/plots/{plot_id}", response_model=ApiResponse[PlotResponse])
async def get_plot(
    plot_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[PlotResponse]:
    plot, _ = await get_plot_with_member(session, plot_id=plot_id, user_id=current_user.id)
    return ApiResponse.success_response(data=_plot_response(plot))


@router.patch("/plots/{plot_id}", response_model=ApiResponse[PlotResponse])
async def edit_plot(
    plot_id: int,
    request: UpdatePlotRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[PlotResponse]:
    plot = await update_plot(
        session,
        plot_id=plot_id,
        user_id=current_user.id,
        name=request.name,
        plot_type=request.plot_type,
        area_value=request.area_value,
        area_unit=request.area_unit,
        boundary=request.boundary,
        fields_set=request.model_fields_set,
    )
    return ApiResponse.success_response(data=_plot_response(plot))
