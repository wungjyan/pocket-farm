from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    phone_number: str = Field(
        validation_alias=AliasChoices("phoneNumber", "phone_number"),
        min_length=11,
        max_length=11,
        pattern=r"^1[3-9]\d{9}$",
    )
    verification_code: str = Field(
        validation_alias=AliasChoices("verificationCode", "verification_code"),
        min_length=1,
        max_length=20,
    )


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    phone_number: str = Field(serialization_alias="phoneNumber")
    nickname: str | None = None


class LoginResponse(BaseModel):
    access_token: str = Field(serialization_alias="accessToken")
    token_type: str = Field(default="bearer", serialization_alias="tokenType")
    user: UserResponse


class UpdateCurrentUserRequest(BaseModel):
    nickname: str | None = Field(default=None, max_length=50)
