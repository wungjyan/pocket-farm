from datetime import datetime
from typing import Annotated

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from app.models.farm import FarmMemberRole


class CreateFarmRequest(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=100)]
    region: Annotated[str | None, Field(default=None, max_length=100)]


class UpdateFarmRequest(BaseModel):
    name: Annotated[str | None, Field(default=None, min_length=1, max_length=100)]
    region: Annotated[str | None, Field(default=None, max_length=100)]


class FarmResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    farm_code: str = Field(serialization_alias="farmCode")
    name: str
    region: str | None = None
    created_by: int = Field(serialization_alias="createdBy")
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")
    my_role: FarmMemberRole | None = Field(default=None, serialization_alias="myRole")


class FarmPage(BaseModel):
    items: list[FarmResponse]
    page: int
    page_size: int = Field(serialization_alias="pageSize")
    total: int


class CreateMemberRequest(BaseModel):
    phone_number: str = Field(
        validation_alias=AliasChoices("phoneNumber", "phone_number"),
        min_length=11,
        max_length=11,
        pattern=r"^1[3-9]\d{9}$",
    )
    role: FarmMemberRole = FarmMemberRole.MEMBER


class UpdateMemberRequest(BaseModel):
    role: FarmMemberRole


class MemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int = Field(serialization_alias="userId")
    nickname: str | None = None
    role: FarmMemberRole
    joined_at: datetime = Field(serialization_alias="joinedAt")


class MemberPage(BaseModel):
    items: list[MemberResponse]
    page: int
    page_size: int = Field(serialization_alias="pageSize")
    total: int
