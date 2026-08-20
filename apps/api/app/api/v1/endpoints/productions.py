from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.models.production import (
    PlantingMethod,
    PlantingStandard,
    ProductionStatus,
    WorkMethod,
)
from app.models.species import IndividualUnit, Industry
from app.models.user import User
from app.schemas.production import (
    CreateProductionRequest,
    EndProductionRequest,
    ProductionPage,
    ProductionResponse,
    UpdateProductionRequest,
)
from app.schemas.response import ApiResponse
from app.services.production import (
    create_production,
    delete_production,
    end_production,
    get_production_with_member,
    list_plot_productions,
    update_production,
)

router = APIRouter(tags=["productions"])


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


@router.get("/plots/{plot_id}/productions", response_model=ApiResponse[ProductionPage])
async def get_plot_productions(
    plot_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    production_status: Annotated[ProductionStatus | None, Query(alias="status")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(alias="pageSize", ge=1, le=100)] = 20,
) -> ApiResponse[ProductionPage]:
    productions, total = await list_plot_productions(
        session,
        plot_id=plot_id,
        user_id=current_user.id,
        status=production_status,
        page=page,
        page_size=page_size,
    )
    return ApiResponse.success_response(
        data=ProductionPage(
            items=[
                _production_response(production, species) for production, species in productions
            ],
            page=page,
            page_size=page_size,
            total=total,
        )
    )


@router.post(
    "/plots/{plot_id}/productions",
    response_model=ApiResponse[ProductionResponse],
    status_code=status.HTTP_201_CREATED,
)
async def start_plot_production(
    plot_id: int,
    request: CreateProductionRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[ProductionResponse]:
    production, species = await create_production(
        session,
        plot_id=plot_id,
        user_id=current_user.id,
        species_id=request.species_id,
        variety=request.variety,
        started_on=request.started_on,
        planting_standard=request.planting_standard,
        planting_method=request.planting_method,
        work_method=request.work_method,
        expected_harvest_on=request.expected_harvest_on,
        expected_yield_per_mu=request.expected_yield_per_mu,
        initial_quantity=request.initial_quantity,
        plant_spacing_cm=request.plant_spacing_cm,
        entry_age_days=request.entry_age_days,
        remark=request.remark,
    )
    return ApiResponse.success_response(data=_production_response(production, species))


@router.get("/productions/{production_id}", response_model=ApiResponse[ProductionResponse])
async def get_production(
    production_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[ProductionResponse]:
    production, _, _, species = await get_production_with_member(
        session,
        production_id=production_id,
        user_id=current_user.id,
    )
    return ApiResponse.success_response(data=_production_response(production, species))


@router.patch("/productions/{production_id}", response_model=ApiResponse[ProductionResponse])
async def edit_production(
    production_id: int,
    request: UpdateProductionRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[ProductionResponse]:
    production, species = await update_production(
        session,
        production_id=production_id,
        user_id=current_user.id,
        plot_id=request.plot_id,
        species_id=request.species_id,
        variety=request.variety,
        started_on=request.started_on,
        planting_standard=request.planting_standard,
        planting_method=request.planting_method,
        work_method=request.work_method,
        expected_harvest_on=request.expected_harvest_on,
        expected_yield_per_mu=request.expected_yield_per_mu,
        initial_quantity=request.initial_quantity,
        plant_spacing_cm=request.plant_spacing_cm,
        entry_age_days=request.entry_age_days,
        remark=request.remark,
        fields_set=request.model_fields_set,
    )
    return ApiResponse.success_response(data=_production_response(production, species))


@router.post("/productions/{production_id}/end", response_model=ApiResponse[ProductionResponse])
async def end_current_production(
    production_id: int,
    request: EndProductionRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[ProductionResponse]:
    production, species = await end_production(
        session,
        production_id=production_id,
        user_id=current_user.id,
        ended_on=request.ended_on,
    )
    return ApiResponse.success_response(data=_production_response(production, species))


@router.delete("/productions/{production_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_production(
    production_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Response:
    await delete_production(session, production_id=production_id, user_id=current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
