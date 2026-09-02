from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.models.user import User
from app.schemas.ai import AITurnRequest, AITurnResponse
from app.schemas.response import ApiResponse
from app.services.ai import run_ai_turn
from app.services.ai_client import AIClient, get_ai_client

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/turn", response_model=ApiResponse[AITurnResponse])
async def create_ai_turn(
    request: AITurnRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    client: Annotated[AIClient, Depends(get_ai_client)],
) -> ApiResponse[AITurnResponse]:
    response = await run_ai_turn(
        session,
        client=client,
        current_user=current_user,
        farm_id=request.farm_id,
        message=request.message,
        history=request.history,
    )
    return ApiResponse.success_response(data=response)
