from datetime import UTC
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.models.harvest import HarvestRecord
from app.models.operation import OperationType
from app.models.plot import PlotType
from app.models.production import (
    PlantingMethod,
    PlantingStandard,
    ProductionStatus,
    QuantityUnit,
    WorkMethod,
)
from app.models.species import IndividualUnit, Industry
from app.models.user import User
from app.schemas.farm import (
    CreatePlotRequest,
    PlotDetailResponse,
    PlotPage,
    PlotResponse,
    UpdatePlotRequest,
)
from app.schemas.harvest import HarvestResponse
from app.schemas.operation import OperationResponse, OperationTypeResponse
from app.schemas.production import ProductionResponse
from app.schemas.response import ApiResponse
from app.services.plot import (
    create_plot,
    get_plot_detail,
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


def _as_utc(value):
    return value.replace(tzinfo=UTC)


def _production_response(production, species) -> ProductionResponse:
    return ProductionResponse(
        id=production.id,
        plot_id=production.plot_id,
        species_id=production.species_id,
        species_name=species.name,
        industry=Industry(species.industry),
        individual_unit=IndividualUnit(species.individual_unit),
        variety=production.variety,
        status=ProductionStatus(production.status),
        started_on=production.started_on,
        ended_on=production.ended_on,
        planting_standard=(
            PlantingStandard(production.planting_standard)
            if production.planting_standard is not None
            else None
        ),
        planting_method=(
            PlantingMethod(production.planting_method)
            if production.planting_method is not None
            else None
        ),
        work_method=(
            WorkMethod(production.work_method) if production.work_method is not None else None
        ),
        expected_harvest_on=production.expected_harvest_on,
        expected_yield_per_mu=production.expected_yield_per_mu,
        initial_quantity=production.initial_quantity,
        plant_spacing_cm=production.plant_spacing_cm,
        entry_age_days=production.entry_age_days,
        remark=production.remark,
        created_at=production.created_at,
        updated_at=production.updated_at,
    )


def _operation_response(operation, operation_type: OperationType) -> OperationResponse:
    return OperationResponse(
        id=operation.id,
        plot_id=operation.plot_id,
        production_id=operation.production_id,
        operation_type=OperationTypeResponse(
            id=operation_type.id,
            code=operation_type.code,
            name=operation_type.name,
            status=operation_type.status,
            sort_order=operation_type.sort_order,
            created_at=_as_utc(operation_type.created_at),
            updated_at=_as_utc(operation_type.updated_at),
        ),
        work_method=WorkMethod(operation.work_method),
        operated_at=_as_utc(operation.operated_at),
        operator_id=operation.operator_id,
        created_by=operation.created_by,
        remark=operation.remark,
        created_at=_as_utc(operation.created_at),
        updated_at=_as_utc(operation.updated_at),
    )


def _harvest_response(harvest: HarvestRecord) -> HarvestResponse:
    return HarvestResponse(
        id=harvest.id,
        production_id=harvest.production_id,
        quantity=harvest.quantity,
        unit=QuantityUnit(harvest.unit),
        work_method=WorkMethod(harvest.work_method),
        harvested_at=_as_utc(harvest.harvested_at),
        operator_id=harvest.operator_id,
        created_by=harvest.created_by,
        product_name=harvest.product_name,
        grade=harvest.grade,
        remark=harvest.remark,
        created_at=_as_utc(harvest.created_at),
        updated_at=_as_utc(harvest.updated_at),
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


@router.get("/plots/{plot_id}/detail", response_model=ApiResponse[PlotDetailResponse])
async def get_plot_detail_view(
    plot_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[PlotDetailResponse]:
    detail = await get_plot_detail(session, plot_id=plot_id, user_id=current_user.id)
    return ApiResponse.success_response(
        data=PlotDetailResponse(
            plot=_plot_response(detail.plot),
            active_productions=[
                _production_response(production, species)
                for production, species in detail.active_productions
            ],
            ended_productions=[
                _production_response(production, species)
                for production, species in detail.ended_productions
            ],
            operations=[
                _operation_response(operation, operation_type)
                for operation, operation_type in detail.operations
            ],
            operation_total=detail.operation_total,
            harvests=[_harvest_response(harvest) for harvest in detail.harvests],
            harvest_total=detail.harvest_total,
        )
    )


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
