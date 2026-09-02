from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.config import settings

MAX_HISTORY_MESSAGES = settings.ai_max_history_turns * 2


class CreateAIConversationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    farm_id: int = Field(
        gt=0,
        validation_alias="farmId",
        serialization_alias="farmId",
    )


class AITurnRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    conversation_id: int = Field(
        gt=0,
        validation_alias="conversationId",
        serialization_alias="conversationId",
    )
    message: Annotated[str, Field(min_length=1, max_length=settings.ai_max_message_chars)]

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        message = value.strip()
        if not message:
            raise ValueError("message cannot be blank.")
        return message

class AIReference(BaseModel):
    kind: Literal["PLOT", "PRODUCTION", "OPERATION", "HARVEST", "SPECIES"]
    id: int
    label: str
    route: str


class AITurnResponse(BaseModel):
    answer: str
    references: list[AIReference] = Field(default_factory=list)
    needs_selection: bool = Field(default=False, serialization_alias="needsSelection")
    candidates: list[AIReference] = Field(default_factory=list)


class AIConversationResponse(BaseModel):
    id: int
    farm_id: int = Field(serialization_alias="farmId")
    farm_name: str = Field(serialization_alias="farmName")
    title: str
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")


class AIConversationPage(BaseModel):
    items: list[AIConversationResponse]
    page: int
    page_size: int = Field(serialization_alias="pageSize")
    total: int


class AIMessageResponse(BaseModel):
    id: int
    role: Literal["user", "assistant"]
    content: str
    references: list[AIReference] = Field(default_factory=list)
    candidates: list[AIReference] = Field(default_factory=list)
    created_at: datetime = Field(serialization_alias="createdAt")


class AIMessagePage(BaseModel):
    items: list[AIMessageResponse]
    page: int
    page_size: int = Field(serialization_alias="pageSize")
    total: int
