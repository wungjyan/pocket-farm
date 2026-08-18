import asyncio
from collections.abc import Mapping
from typing import Any

import httpx

from app.db.session import engine
from app.main import app

OWNER_PHONE = "13800000001"
ADMIN_PHONE = "13800000002"
MEMBER_PHONE = "13800000003"
OUTSIDER_PHONE = "13800000004"


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


def login(phone: str) -> str:
    response = asyncio.run(
        request_api(
            "/api/v1/auth/login",
            method="post",
            json={"phoneNumber": phone, "verificationCode": "8888"},
        )
    )
    assert response.status_code == 200
    return response.json()["data"]["accessToken"]


def call(
    token: str,
    path: str,
    *,
    method: str = "get",
    json: Mapping[str, Any] | None = None,
) -> httpx.Response:
    return asyncio.run(
        request_api(
            path,
            method=method,
            json=json,
            headers={"Authorization": f"Bearer {token}"},
        )
    )


def create_farm(token: str) -> dict[str, Any]:
    response = call(token, "/api/v1/farms", method="post", json={"name": "地块测试农场"})
    assert response.status_code == 201
    return response.json()["data"]


def add_member(token: str, farm_id: int, phone: str, role: str) -> dict[str, Any]:
    response = call(
        token,
        f"/api/v1/farms/{farm_id}/members",
        method="post",
        json={"phoneNumber": phone, "role": role},
    )
    assert response.status_code == 201
    return response.json()["data"]


def test_owner_can_create_list_detail_and_edit_plot() -> None:
    owner_token = login(OWNER_PHONE)
    farm = create_farm(owner_token)

    create_response = call(
        owner_token,
        f"/api/v1/farms/{farm['id']}/plots",
        method="post",
        json={
            "name": "1号大棚",
            "type": "GREENHOUSE",
            "areaValue": "6.3",
            "areaUnit": "MU",
            "boundary": {"coordinateSystem": "GCJ02", "coordinates": []},
        },
    )
    assert create_response.status_code == 201
    plot = create_response.json()["data"]
    assert plot["name"] == "1号大棚"
    assert plot["type"] == "GREENHOUSE"
    assert plot["areaUnit"] == "MU"
    assert float(plot["areaM2"]) == 4200.0

    list_response = call(owner_token, f"/api/v1/farms/{farm['id']}/plots")
    assert list_response.status_code == 200
    assert list_response.json()["data"]["total"] == 1

    detail_response = call(owner_token, f"/api/v1/plots/{plot['id']}")
    assert detail_response.status_code == 200
    assert detail_response.json()["data"]["farmId"] == farm["id"]

    edit_response = call(
        owner_token,
        f"/api/v1/plots/{plot['id']}",
        method="patch",
        json={"name": "更新后的大棚", "areaValue": "1000", "areaUnit": "SQUARE_METER"},
    )
    assert edit_response.status_code == 200
    assert edit_response.json()["data"]["name"] == "更新后的大棚"
    assert float(edit_response.json()["data"]["areaM2"]) == 1000.0


def test_member_can_read_but_only_admin_can_manage_plot() -> None:
    owner_token = login(OWNER_PHONE)
    admin_token = login(ADMIN_PHONE)
    member_token = login(MEMBER_PHONE)
    farm = create_farm(owner_token)
    add_member(owner_token, farm["id"], ADMIN_PHONE, "ADMIN")
    add_member(owner_token, farm["id"], MEMBER_PHONE, "MEMBER")

    create_response = call(
        admin_token,
        f"/api/v1/farms/{farm['id']}/plots",
        method="post",
        json={"name": "管理员创建地块"},
    )
    assert create_response.status_code == 201
    plot_id = create_response.json()["data"]["id"]

    member_detail = call(member_token, f"/api/v1/plots/{plot_id}")
    member_edit = call(
        member_token,
        f"/api/v1/plots/{plot_id}",
        method="patch",
        json={"name": "成员越权修改"},
    )
    assert member_detail.status_code == 200
    assert member_edit.status_code == 403


def test_plot_access_is_scoped_to_farm_membership() -> None:
    owner_token = login(OWNER_PHONE)
    outsider_token = login(OUTSIDER_PHONE)
    farm = create_farm(owner_token)
    create_response = call(
        owner_token,
        f"/api/v1/farms/{farm['id']}/plots",
        method="post",
        json={"name": "私有地块"},
    )
    assert create_response.status_code == 201
    plot_id = create_response.json()["data"]["id"]

    list_response = call(outsider_token, f"/api/v1/farms/{farm['id']}/plots")
    detail_response = call(outsider_token, f"/api/v1/plots/{plot_id}")
    assert list_response.status_code == 404
    assert detail_response.status_code == 404


def test_plot_area_and_boundary_validation() -> None:
    owner_token = login(OWNER_PHONE)
    farm = create_farm(owner_token)
    missing_unit = call(
        owner_token,
        f"/api/v1/farms/{farm['id']}/plots",
        method="post",
        json={"name": "面积不完整", "areaValue": 2},
    )
    invalid_boundary = call(
        owner_token,
        f"/api/v1/farms/{farm['id']}/plots",
        method="post",
        json={"name": "坐标系错误", "boundary": {"coordinateSystem": "WGS84"}},
    )
    assert missing_unit.status_code == 422
    assert invalid_boundary.status_code == 422
