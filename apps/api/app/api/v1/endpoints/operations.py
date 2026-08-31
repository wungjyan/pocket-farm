from datetime import UTC
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.models.operation import OperationType
from app.models.plot import AreaUnit
from app.models.production import ProductionStatus, WorkMethod
from app.models.user import User
from app.schemas.operation import (
    CreateOperationRequest,
    FarmOperationSummaryPage,
    FarmOperationSummaryResponse,
    OperationFilterOptionsResponse,
    OperationPage,
    OperationResponse,
    OperationTypeOption,
    OperationTypePage,
    OperationTypeResponse,
    UpdateOperationRequest,
)
from app.schemas.response import ApiResponse
from app.services.operation import (
    create_operation,
    delete_operation,
    get_farm_operation_filter_options,
    get_operation_with_member,
    list_farm_operations,
    list_operation_types,
    list_plot_operations,
    update_operation,
)

router = APIRouter(tags=["operations"])


def _as_utc(value):
    return value.replace(tzinfo=UTC)


def _operation_type_response(operation_type: OperationType) -> OperationTypeResponse:
    return OperationTypeResponse(
        id=operation_type.id,
        code=operation_type.code,
        name=operation_type.name,
        status=operation_type.status,
        sort_order=operation_type.sort_order,
        created_at=_as_utc(operation_type.created_at),
        updated_at=_as_utc(operation_type.updated_at),
    )


def _operation_response(operation, operation_type: OperationType) -> OperationResponse:
    return OperationResponse(
        id=operation.id,
        plot_id=operation.plot_id,
        production_id=operation.production_id,
        operation_type=_operation_type_response(operation_type),
        work_method=WorkMethod(operation.work_method),
        operated_at=_as_utc(operation.operated_at),
        operator_id=operation.operator_id,
        created_by=operation.created_by,
        remark=operation.remark,
        created_at=_as_utc(operation.created_at),
        updated_at=_as_utc(operation.updated_at),
    )


@router.get("/plots/{plot_id}/operations", response_model=ApiResponse[OperationPage])
async def get_plot_operations(
    plot_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(alias="pageSize", ge=1, le=100)] = 20,
) -> ApiResponse[OperationPage]:
    operations, total = await list_plot_operations(
        session,
        plot_id=plot_id,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
    )
    return ApiResponse.success_response(
        data=OperationPage(
            items=[
                _operation_response(operation, operation_type)
                for operation, operation_type in operations
            ],
            page=page,
            page_size=page_size,
            total=total,
        )
    )


@router.get(
    "/farms/{farm_id}/operations",
    response_model=ApiResponse[FarmOperationSummaryPage],
)
async def get_farm_operations(
    farm_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    operation_type_id: Annotated[int | None, Query(alias="operationTypeId", gt=0)] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(alias="pageSize", ge=1, le=100)] = 20,
) -> ApiResponse[FarmOperationSummaryPage]:
    operations, total = await list_farm_operations(
        session,
        farm_id=farm_id,
        user_id=current_user.id,
        operation_type_id=operation_type_id,
        page=page,
        page_size=page_size,
    )
    return ApiResponse.success_response(
        data=FarmOperationSummaryPage(
            items=[
                FarmOperationSummaryResponse(
                    id=operation.id,
                    plot_id=plot.id,
                    plot_name=plot.name,
                    plot_area_value=plot.area_value,
                    plot_area_unit=AreaUnit(plot.area_unit) if plot.area_unit else None,
                    production_id=operation.production_id,
                    operation_type_id=operation_type.id,
                    operation_type_name=operation_type.name,
                    operated_at=_as_utc(operation.operated_at),
                    species_name=species.name if species else None,
                    production_status=(
                        ProductionStatus(production_status) if production_status else None
                    ),
                )
                for operation, plot, operation_type, production_status, species in operations
            ],
            page=page,
            page_size=page_size,
            total=total,
        )
    )


@router.get(
    "/farms/{farm_id}/operation-filter-options",
    response_model=ApiResponse[OperationFilterOptionsResponse],
)
async def list_farm_operation_filter_options(
    farm_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[OperationFilterOptionsResponse]:
    type_options = await get_farm_operation_filter_options(
        session,
        farm_id=farm_id,
        user_id=current_user.id,
    )
    return ApiResponse.success_response(
        data=OperationFilterOptionsResponse(
            types=[
                OperationTypeOption(id=type_id, name=type_name)
                for type_id, type_name in type_options
            ]
        )
    )


@router.post(
    "/plots/{plot_id}/operations",
    response_model=ApiResponse[OperationResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_plot_operation(
    plot_id: int,
    request: CreateOperationRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[OperationResponse]:
    operation, operation_type = await create_operation(
        session,
        plot_id=plot_id,
        user_id=current_user.id,
        production_id=request.production_id,
        operation_type_id=request.operation_type_id,
        work_method=request.work_method,
        operated_at=request.operated_at,
        operator_id=request.operator_id,
        remark=request.remark,
    )
    return ApiResponse.success_response(data=_operation_response(operation, operation_type))


@router.get("/operations/{operation_id}", response_model=ApiResponse[OperationResponse])
async def get_operation(
    operation_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[OperationResponse]:
    operation, _, _, operation_type = await get_operation_with_member(
        session,
        operation_id=operation_id,
        user_id=current_user.id,
    )
    return ApiResponse.success_response(data=_operation_response(operation, operation_type))


@router.patch("/operations/{operation_id}", response_model=ApiResponse[OperationResponse])
async def edit_operation(
    operation_id: int,
    request: UpdateOperationRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[OperationResponse]:
    operation, operation_type = await update_operation(
        session,
        operation_id=operation_id,
        user_id=current_user.id,
        production_id=request.production_id,
        operation_type_id=request.operation_type_id,
        work_method=request.work_method,
        operated_at=request.operated_at,
        operator_id=request.operator_id,
        remark=request.remark,
        fields_set=request.model_fields_set,
    )
    return ApiResponse.success_response(data=_operation_response(operation, operation_type))


@router.delete("/operations/{operation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_operation(
    operation_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Response:
    await delete_operation(session, operation_id=operation_id, user_id=current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/operation-types", response_model=ApiResponse[OperationTypePage])
async def get_operation_types(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(alias="pageSize", ge=1, le=100)] = 100,
) -> ApiResponse[OperationTypePage]:
    operation_types, total = await list_operation_types(
        session,
        page=page,
        page_size=page_size,
    )
    return ApiResponse.success_response(
        data=OperationTypePage(
            items=[_operation_type_response(operation_type) for operation_type in operation_types],
            page=page,
            page_size=page_size,
            total=total,
        )
    )
