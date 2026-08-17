import asyncio

import httpx
from fastapi import FastAPI, Query

from app.core.exceptions import register_exception_handlers
from app.main import app

validation_app = FastAPI()
register_exception_handlers(validation_app)


@validation_app.get("/validate")
async def validate(value: int = Query(...)) -> dict[str, int]:
    return {"value": value}


async def request_path(path: str, asgi_app: FastAPI = app) -> httpx.Response:
    transport = httpx.ASGITransport(app=asgi_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.get(path)


def test_health_check_returns_ok() -> None:
    response = asyncio.run(request_path("/health"))

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "data": {"status": "ok"},
        "error": None,
    }


def test_http_errors_use_common_response_envelope() -> None:
    response = asyncio.run(request_path("/does-not-exist"))

    assert response.status_code == 404
    assert response.json() == {
        "success": False,
        "data": None,
        "error": {
            "code": "HTTP_ERROR",
            "message": "Not Found",
            "details": None,
        },
    }


def test_validation_errors_use_common_response_envelope() -> None:
    response = asyncio.run(request_path("/validate?value=not-an-integer", validation_app))

    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert body["data"] is None
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert body["error"]["message"] == "Request validation failed."
    assert isinstance(body["error"]["details"], list)
