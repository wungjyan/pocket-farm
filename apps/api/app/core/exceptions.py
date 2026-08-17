from typing import cast

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.error_codes import ErrorCode


class AppException(Exception):
    """An expected application error with a stable machine-readable code."""

    def __init__(self, *, status_code: int, code: ErrorCode, message: str) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(message)


def _error_body(code: ErrorCode, message: str) -> dict[str, dict[str, str]]:
    return {"detail": {"code": code, "message": message}}


async def app_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    app_exc = cast(AppException, exc)
    return JSONResponse(
        status_code=app_exc.status_code,
        content=_error_body(app_exc.code, app_exc.message),
    )


async def unhandled_exception_handler(_request: Request, _exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content=_error_body(ErrorCode.INTERNAL_SERVER_ERROR, "Internal server error."),
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
