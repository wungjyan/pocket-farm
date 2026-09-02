from datetime import UTC
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.models.farm import FarmMemberRole
from app.models.plot import AreaUnit, PlotType
from app.models.user import User
from app.schemas.activity import FarmActivityListResponse, FarmActivityResponse
from app.schemas.farm import (
    CreateFarmRequest,
    CreateMemberRequest,
    FarmPage,
    FarmResponse,
    MemberPage,
    MemberResponse,
    PlotResponse,
    UpdateFarmRequest,
    UpdateMemberRequest,
)
from app.schemas.response import ApiResponse
from app.services.activity import list_farm_activities
from app.services.farm import (
    add_member,
    create_farm,
    get_farm_with_member,
    leave_farm,
    list_members,
    list_my_farms,
    remove_member,
    update_farm,
    update_member_role,
)

router = APIRouter(prefix="/farms", tags=["farms"])


def _farm_response(farm, role: FarmMemberRole | str | None) -> FarmResponse:
    return FarmResponse(
        id=farm.id,
        farm_code=farm.farm_code,
        name=farm.name,
        region=farm.region,
        ai_enabled=farm.ai_enabled,
        created_by=farm.created_by,
        created_at=farm.created_at,
        updated_at=farm.updated_at,
        my_role=FarmMemberRole(role) if role is not None else None,
    )


def _member_response(member, user: User) -> MemberResponse:
    return MemberResponse(
        id=member.id,
        user_id=member.user_id,
        nickname=user.nickname,
        role=FarmMemberRole(member.role),
        joined_at=member.joined_at,
    )


def _as_utc(value):
    return value.replace(tzinfo=UTC)


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


@router.get("", response_model=ApiResponse[FarmPage])
async def get_my_farms(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(alias="pageSize", ge=1, le=100)] = 20,
) -> ApiResponse[FarmPage]:
    farms, total = await list_my_farms(
        session, user_id=current_user.id, page=page, page_size=page_size
    )
    return ApiResponse.success_response(
        data=FarmPage(
            items=[_farm_response(farm, role) for farm, role in farms],
            page=page,
            page_size=page_size,
            total=total,
        )
    )


@router.post("", response_model=ApiResponse[FarmResponse], status_code=status.HTTP_201_CREATED)
async def create_my_farm(
    request: CreateFarmRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[FarmResponse]:
    farm = await create_farm(
        session,
        created_by=current_user.id,
        name=request.name,
        region=request.region,
    )
    return ApiResponse.success_response(data=_farm_response(farm, FarmMemberRole.OWNER))


@router.get("/{farm_id}", response_model=ApiResponse[FarmResponse])
async def get_farm(
    farm_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[FarmResponse]:
    farm, member = await get_farm_with_member(session, farm_id=farm_id, user_id=current_user.id)
    return ApiResponse.success_response(data=_farm_response(farm, member.role))


@router.patch("/{farm_id}", response_model=ApiResponse[FarmResponse])
async def edit_farm(
    farm_id: int,
    request: UpdateFarmRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[FarmResponse]:
    farm, role = await update_farm(
        session,
        farm_id=farm_id,
        user_id=current_user.id,
        name=request.name,
        region=request.region,
        ai_enabled=request.ai_enabled,
        fields_set=request.model_fields_set,
    )
    return ApiResponse.success_response(data=_farm_response(farm, role))


@router.get("/{farm_id}/activities", response_model=ApiResponse[FarmActivityListResponse])
async def get_farm_activities(
    farm_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    limit: Annotated[int, Query(ge=1, le=20)] = 5,
) -> ApiResponse[FarmActivityListResponse]:
    activities = await list_farm_activities(
        session,
        farm_id=farm_id,
        user_id=current_user.id,
        limit=limit,
    )
    return ApiResponse.success_response(
        data=FarmActivityListResponse(
            items=[
                FarmActivityResponse(
                    type=activity.type,
                    occurred_at=_as_utc(activity.occurred_at),
                    production_id=activity.production_id,
                    operation_id=activity.operation_id,
                    harvest_id=activity.harvest_id,
                    plot_id=activity.plot.id,
                    plot_name=activity.plot.name,
                    plot_area_value=activity.plot.area_value,
                    plot_area_unit=(
                        AreaUnit(activity.plot.area_unit) if activity.plot.area_unit else None
                    ),
                    species_name=activity.species_name,
                    industry=activity.industry,
                    operation_type_name=activity.operation_type_name,
                    quantity=activity.quantity,
                    unit=activity.unit,
                    operator_name=activity.operator_name,
                )
                for activity in activities
            ]
        )
    )


@router.get("/{farm_id}/members", response_model=ApiResponse[MemberPage])
async def get_farm_members(
    farm_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(alias="pageSize", ge=1, le=100)] = 20,
) -> ApiResponse[MemberPage]:
    members, total = await list_members(
        session, farm_id=farm_id, user_id=current_user.id, page=page, page_size=page_size
    )
    return ApiResponse.success_response(
        data=MemberPage(
            items=[_member_response(member, user) for member, user in members],
            page=page,
            page_size=page_size,
            total=total,
        )
    )


@router.post(
    "/{farm_id}/members",
    response_model=ApiResponse[MemberResponse],
    status_code=status.HTTP_201_CREATED,
)
async def add_farm_member(
    farm_id: int,
    request: CreateMemberRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[MemberResponse]:
    member, user = await add_member(
        session,
        farm_id=farm_id,
        actor_id=current_user.id,
        phone_number=request.phone_number,
        role=request.role,
    )
    return ApiResponse.success_response(data=_member_response(member, user))


@router.patch("/{farm_id}/members/{member_id}", response_model=ApiResponse[MemberResponse])
async def edit_farm_member(
    farm_id: int,
    member_id: int,
    request: UpdateMemberRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[MemberResponse]:
    member, user = await update_member_role(
        session,
        farm_id=farm_id,
        member_id=member_id,
        actor_id=current_user.id,
        role=request.role,
    )
    return ApiResponse.success_response(data=_member_response(member, user))


@router.delete("/{farm_id}/members/me", status_code=status.HTTP_204_NO_CONTENT)
async def leave_my_farm(
    farm_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Response:
    await leave_farm(session, farm_id=farm_id, user_id=current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/{farm_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_farm_member(
    farm_id: int,
    member_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Response:
    await remove_member(session, farm_id=farm_id, member_id=member_id, actor_id=current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
