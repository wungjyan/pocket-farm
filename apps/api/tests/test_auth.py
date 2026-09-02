import asyncio
from collections.abc import Mapping
from typing import Any

import httpx

from app.db.session import engine
from app.main import app

TEST_PHONE = "13800000001"


async def request_api(
    path: str,
    *,
    method: str = "get",
    json: Mapping[str, Any] | None = None,
    headers: Mapping[str, str] | None = None,
) -> httpx.Response:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.request(method, path, json=json, headers=headers)
    await engine.dispose()
    return response


def login() -> httpx.Response:
    return asyncio.run(
        request_api(
            "/api/v1/auth/login",
            method="post",
            json={"phoneNumber": TEST_PHONE, "verificationCode": "8888"},
        )
    )


def test_login_creates_user_and_returns_bearer_token() -> None:
    response = login()

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["error"] is None
    assert body["data"]["accessToken"]
    assert body["data"]["tokenType"] == "bearer"
    assert body["data"]["user"]["phoneNumber"] == TEST_PHONE
    assert "nickname" in body["data"]["user"]


def test_repeated_login_returns_same_user() -> None:
    first = login().json()["data"]["user"]["id"]
    second = login().json()["data"]["user"]["id"]

    assert first == second


def test_any_valid_phone_can_use_the_configured_test_code() -> None:
    response = asyncio.run(
        request_api(
            "/api/v1/auth/login",
            method="post",
            json={"phoneNumber": "19900000001", "verificationCode": "8888"},
        )
    )

    assert response.status_code == 200
    assert response.json()["data"]["user"]["phoneNumber"] == "19900000001"


def test_invalid_code_returns_unauthorized() -> None:
    response = asyncio.run(
        request_api(
            "/api/v1/auth/login",
            method="post",
            json={"phoneNumber": TEST_PHONE, "verificationCode": "0000"},
        )
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_invalid_phone_format_returns_validation_error() -> None:
    response = asyncio.run(
        request_api(
            "/api/v1/auth/login",
            method="post",
            json={"phoneNumber": "123", "verificationCode": "8888"},
        )
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_current_user_requires_token() -> None:
    response = asyncio.run(request_api("/api/v1/users/me"))

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_current_user_can_update_nickname() -> None:
    token = login().json()["data"]["accessToken"]
    headers = {"Authorization": f"Bearer {token}"}

    update_response = asyncio.run(
        request_api(
            "/api/v1/users/me",
            method="patch",
            json={"nickname": "测试用户"},
            headers=headers,
        )
    )
    me_response = asyncio.run(request_api("/api/v1/users/me", headers=headers))

    assert update_response.status_code == 200
    assert update_response.json()["data"]["nickname"] == "测试用户"
    assert me_response.status_code == 200
    assert me_response.json()["data"]["nickname"] == "测试用户"
