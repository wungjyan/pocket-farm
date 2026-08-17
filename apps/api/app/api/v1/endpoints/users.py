from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.models.user import User
from app.schemas.response import ApiResponse
from app.schemas.user import UpdateCurrentUserRequest, UserResponse
from app.services.user import update_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=ApiResponse[UserResponse])
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[UserResponse]:
    return ApiResponse.success_response(data=UserResponse.model_validate(current_user))


@router.patch("/me", response_model=ApiResponse[UserResponse])
async def update_me(
    request: UpdateCurrentUserRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[UserResponse]:
    user = await update_current_user(session, user=current_user, nickname=request.nickname)
    return ApiResponse.success_response(data=UserResponse.model_validate(user))
