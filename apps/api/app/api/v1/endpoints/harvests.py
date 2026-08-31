from datetime import UTC
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.models.harvest import HarvestRecord
from app.models.plot import AreaUnit
from app.models.production import ProductionStatus, QuantityUnit, WorkMethod
from app.models.species import Industry
from app.models.user import User
from app.schemas.harvest import (
    CreateHarvestRequest,
    FarmHarvestSummaryPage,
    FarmHarvestSummaryResponse,
    HarvestFilterOptionsResponse,
    HarvestPage,
    HarvestResponse,
    HarvestSpeciesOption,
    UpdateHarvestRequest,
)
from app.schemas.response import ApiResponse
from app.services.harvest import (
    create_harvest,
    delete_harvest,
    get_harvest_with_member,
    list_farm_harvests,
    list_plot_harvests,
    list_production_harvests,
    update_harvest,
)
from app.services.harvest import (
    get_farm_harvest_filter_options as get_farm_harvest_filter_options_service,
)

router = APIRouter(tags=["harvests"])


def _as_utc(value):
    return value.replace(tzinfo=UTC)


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


def _harvest_page(
    harvests: list[HarvestRecord],
    *,
    page: int,
    page_size: int,
    total: int,
) -> HarvestPage:
    return HarvestPage(
        items=[_harvest_response(harvest) for harvest in harvests],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get("/farms/{farm_id}/harvests", response_model=ApiResponse[FarmHarvestSummaryPage])
async def get_farm_harvests(
    farm_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    industry: Industry = Industry.AGRICULTURE,
    species_id: Annotated[int | None, Query(alias="speciesId", gt=0)] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(alias="pageSize", ge=1, le=100)] = 20,
) -> ApiResponse[FarmHarvestSummaryPage]:
    harvests, total = await list_farm_harvests(
        session,
        farm_id=farm_id,
        user_id=current_user.id,
        industry=industry,
        species_id=species_id,
        page=page,
        page_size=page_size,
    )
    return ApiResponse.success_response(
        data=FarmHarvestSummaryPage(
            items=[
                FarmHarvestSummaryResponse(
                    id=harvest.id,
                    production_id=production.id,
                    production_status=ProductionStatus(production.status),
                    plot_id=plot.id,
                    plot_name=plot.name,
                    plot_area_value=plot.area_value,
                    plot_area_unit=AreaUnit(plot.area_unit) if plot.area_unit else None,
                    species_id=species.id,
                    species_name=species.name,
                    industry=Industry(species.industry),
                    quantity=harvest.quantity,
                    unit=QuantityUnit(harvest.unit),
                    harvested_at=_as_utc(harvest.harvested_at),
                    product_name=harvest.product_name,
                    operator_id=harvest.operator_id,
                    operator_name=operator.nickname if operator else None,
                    created_by=harvest.created_by,
                    creator_name=creator.nickname if creator else None,
                )
                for harvest, production, plot, species, operator, creator in harvests
            ],
            page=page,
            page_size=page_size,
            total=total,
        )
    )


@router.get(
    "/farms/{farm_id}/harvest-filter-options",
    response_model=ApiResponse[HarvestFilterOptionsResponse],
)
async def get_farm_harvest_filter_options(
    farm_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    industry: Industry = Industry.AGRICULTURE,
) -> ApiResponse[HarvestFilterOptionsResponse]:
    species_options = await get_farm_harvest_filter_options_service(
        session,
        farm_id=farm_id,
        user_id=current_user.id,
        industry=industry,
    )
    return ApiResponse.success_response(
        data=HarvestFilterOptionsResponse(
            species=[
                HarvestSpeciesOption(id=species_id, name=species_name)
                for species_id, species_name in species_options
            ]
        )
    )


@router.get("/productions/{production_id}/harvests", response_model=ApiResponse[HarvestPage])
async def get_production_harvests(
    production_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(alias="pageSize", ge=1, le=100)] = 20,
) -> ApiResponse[HarvestPage]:
    harvests, total = await list_production_harvests(
        session,
        production_id=production_id,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
    )
    return ApiResponse.success_response(
        data=_harvest_page(harvests, page=page, page_size=page_size, total=total)
    )


@router.post(
    "/productions/{production_id}/harvests",
    response_model=ApiResponse[HarvestResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_production_harvest(
    production_id: int,
    request: CreateHarvestRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[HarvestResponse]:
    harvest = await create_harvest(
        session,
        production_id=production_id,
        user_id=current_user.id,
        quantity=request.quantity,
        work_method=request.work_method,
        harvested_at=request.harvested_at,
        operator_id=request.operator_id,
        product_name=request.product_name,
        grade=request.grade,
        remark=request.remark,
    )
    return ApiResponse.success_response(data=_harvest_response(harvest))


@router.get("/plots/{plot_id}/harvests", response_model=ApiResponse[HarvestPage])
async def get_plot_harvests(
    plot_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(alias="pageSize", ge=1, le=100)] = 20,
) -> ApiResponse[HarvestPage]:
    harvests, total = await list_plot_harvests(
        session,
        plot_id=plot_id,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
    )
    return ApiResponse.success_response(
        data=_harvest_page(harvests, page=page, page_size=page_size, total=total)
    )


@router.get("/harvests/{harvest_id}", response_model=ApiResponse[HarvestResponse])
async def get_harvest(
    harvest_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[HarvestResponse]:
    harvest, _, _, _ = await get_harvest_with_member(
        session,
        harvest_id=harvest_id,
        user_id=current_user.id,
    )
    return ApiResponse.success_response(data=_harvest_response(harvest))


@router.patch("/harvests/{harvest_id}", response_model=ApiResponse[HarvestResponse])
async def edit_harvest(
    harvest_id: int,
    request: UpdateHarvestRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[HarvestResponse]:
    harvest = await update_harvest(
        session,
        harvest_id=harvest_id,
        user_id=current_user.id,
        quantity=request.quantity,
        work_method=request.work_method,
        harvested_at=request.harvested_at,
        operator_id=request.operator_id,
        product_name=request.product_name,
        grade=request.grade,
        remark=request.remark,
        fields_set=request.model_fields_set,
    )
    return ApiResponse.success_response(data=_harvest_response(harvest))


@router.delete("/harvests/{harvest_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_harvest(
    harvest_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Response:
    await delete_harvest(session, harvest_id=harvest_id, user_id=current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
