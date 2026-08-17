from typing import Any, Generic, TypeVar

from pydantic import BaseModel

from app.core.error_codes import ErrorCode

DataT = TypeVar("DataT")


class ErrorDetail(BaseModel):
    code: ErrorCode | str
    message: str
    details: Any | None = None


class ApiResponse(BaseModel, Generic[DataT]):
    """The common response envelope for every API response."""

    success: bool
    data: DataT | None = None
    error: ErrorDetail | None = None

    @classmethod
    def success_response(cls, data: DataT | None = None) -> "ApiResponse[DataT]":
        return cls(success=True, data=data, error=None)

    @classmethod
    def error_response(
        cls,
        *,
        code: ErrorCode | str,
        message: str,
        details: Any | None = None,
    ) -> "ApiResponse[DataT]":
        return cls(
            success=False,
            data=None,
            error=ErrorDetail(code=code, message=message, details=details),
        )
