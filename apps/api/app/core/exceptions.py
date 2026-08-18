from typing import cast

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.error_codes import ErrorCode
from app.schemas.response import ApiResponse


class AppException(Exception):
    """An expected application error with a stable machine-readable code."""

    def __init__(
        self,
        *,
        status_code: int,
        code: ErrorCode,
        message: str,
        details: object | None = None,
    ) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details
        super().__init__(message)


def _json_response(status_code: int, response: ApiResponse[None]) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=response.model_dump(mode="json"))


async def app_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    app_exc = cast(AppException, exc)
    return _json_response(
        app_exc.status_code,
        ApiResponse[None].error_response(
            code=app_exc.code,
            message=app_exc.message,
            details=app_exc.details,
        ),
    )


async def request_validation_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    validation_exc = cast(RequestValidationError, exc)
    return _json_response(
        422,
        ApiResponse[None].error_response(
            code=ErrorCode.VALIDATION_ERROR,
            message="Request validation failed.",
            details=jsonable_encoder(validation_exc.errors()),
        ),
    )


async def http_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    http_exc = cast(StarletteHTTPException, exc)
    message = http_exc.detail if isinstance(http_exc.detail, str) else "HTTP request failed."
    details = None if isinstance(http_exc.detail, str) else http_exc.detail
    return _json_response(
        http_exc.status_code,
        ApiResponse[None].error_response(
            code=ErrorCode.HTTP_ERROR,
            message=message,
            details=details,
        ),
    )


async def unhandled_exception_handler(_request: Request, _exc: Exception) -> JSONResponse:
    return _json_response(
        500,
        ApiResponse[None].error_response(
            code=ErrorCode.INTERNAL_SERVER_ERROR,
            message="Internal server error.",
        ),
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, request_validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
