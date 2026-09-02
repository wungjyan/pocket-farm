from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.config import settings

MAX_HISTORY_MESSAGES = settings.ai_max_history_turns * 2
MAX_HISTORY_TOTAL_CHARS = settings.ai_max_history_turns * settings.ai_max_message_chars * 2


class AIHistoryMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["user", "assistant"]
    content: Annotated[str, Field(min_length=1, max_length=settings.ai_max_message_chars)]

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("content cannot be blank.")
        return value


class AITurnRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    farm_id: int = Field(
        gt=0,
        validation_alias="farmId",
        serialization_alias="farmId",
    )
    message: Annotated[str, Field(min_length=1, max_length=settings.ai_max_message_chars)]
    history: list[AIHistoryMessage] = Field(default_factory=list, max_length=MAX_HISTORY_MESSAGES)

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        message = value.strip()
        if not message:
            raise ValueError("message cannot be blank.")
        return message

    @field_validator("history")
    @classmethod
    def validate_history_total_chars(cls, value: list[AIHistoryMessage]) -> list[AIHistoryMessage]:
        if sum(len(item.content) for item in value) > MAX_HISTORY_TOTAL_CHARS:
            raise ValueError("history is too long.")
        return value


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
