from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.core.security import create_access_token
from app.schemas.response import ApiResponse
from app.schemas.user import LoginRequest, LoginResponse, UserResponse
from app.services.auth import login_with_verification_code

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=ApiResponse[LoginResponse])
async def login(
    request: LoginRequest,
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[LoginResponse]:
    user = await login_with_verification_code(
        session,
        phone_number=request.phone_number,
        verification_code=request.verification_code,
    )
    return ApiResponse.success_response(
        data=LoginResponse(
            access_token=create_access_token(user_id=user.id),
            user=UserResponse.model_validate(user),
        )
    )
