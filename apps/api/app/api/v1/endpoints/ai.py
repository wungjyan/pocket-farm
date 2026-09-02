from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.models.user import User
from app.schemas.ai import (
    AIConversationPage,
    AIConversationResponse,
    AIMessagePage,
    AITurnRequest,
    AITurnResponse,
    CreateAIConversationRequest,
)
from app.schemas.response import ApiResponse
from app.services.ai import (
    create_ai_conversation,
    delete_ai_conversation,
    list_ai_conversations,
    list_ai_messages,
    run_ai_turn,
)
from app.services.ai_client import AIClient, get_ai_client

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/conversations", response_model=ApiResponse[AIConversationPage])
async def get_ai_conversations(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(alias="pageSize", ge=1, le=100)] = 20,
) -> ApiResponse[AIConversationPage]:
    conversations = await list_ai_conversations(
        session, current_user=current_user, page=page, page_size=page_size
    )
    return ApiResponse.success_response(data=conversations)


@router.post(
    "/conversations",
    response_model=ApiResponse[AIConversationResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_conversation(
    request: CreateAIConversationRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[AIConversationResponse]:
    conversation = await create_ai_conversation(
        session, current_user=current_user, farm_id=request.farm_id
    )
    return ApiResponse.success_response(data=conversation)


@router.get("/conversations/{conversation_id}/messages", response_model=ApiResponse[AIMessagePage])
async def get_ai_messages(
    conversation_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(alias="pageSize", ge=1, le=100)] = 50,
) -> ApiResponse[AIMessagePage]:
    messages = await list_ai_messages(
        session,
        current_user=current_user,
        conversation_id=conversation_id,
        page=page,
        page_size=page_size,
    )
    return ApiResponse.success_response(data=messages)


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_conversation(
    conversation_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Response:
    await delete_ai_conversation(
        session, current_user=current_user, conversation_id=conversation_id
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


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
        conversation_id=request.conversation_id,
        message=request.message,
    )
    return ApiResponse.success_response(data=response)
