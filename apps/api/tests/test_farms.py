import asyncio
from collections.abc import Mapping
from typing import Any

import httpx

from app.db.session import engine
from app.main import app

OWNER_PHONE = "13800000001"
ADMIN_PHONE = "13800000002"
MEMBER_PHONE = "13800000003"
SECOND_OWNER_PHONE = "13800000004"
EXTRA_PHONE = "13800000005"


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


def current_user_id(token: str) -> int:
    response = call(token, "/api/v1/users/me")
    assert response.status_code == 200
    return response.json()["data"]["id"]


def create_farm(token: str, name: str = "测试农场") -> dict[str, Any]:
    response = call(token, "/api/v1/farms", method="post", json={"name": name, "region": "上海"})
    assert response.status_code == 201
    return response.json()["data"]


def add_member(token: str, farm_id: int, phone: str, role: str | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"phoneNumber": phone}
    if role is not None:
        payload["role"] = role
    response = call(token, f"/api/v1/farms/{farm_id}/members", method="post", json=payload)
    assert response.status_code == 201
    return response.json()["data"]


def members_by_user_id(token: str, farm_id: int) -> dict[int, dict[str, Any]]:
    response = call(token, f"/api/v1/farms/{farm_id}/members")
    assert response.status_code == 200
    return {item["userId"]: item for item in response.json()["data"]["items"]}


def test_create_farm_creates_owner_and_lists_farm() -> None:
    token = login(OWNER_PHONE)

    farm = create_farm(token)
    assert len(farm["farmCode"]) == 6
    assert farm["farmCode"].isdigit()
    assert farm["myRole"] == "OWNER"

    list_response = call(token, "/api/v1/farms")
    assert list_response.status_code == 200
    page = list_response.json()["data"]
    assert page["total"] == 1
    assert page["items"][0]["id"] == farm["id"]
    assert page["items"][0]["myRole"] == "OWNER"

    members = members_by_user_id(token, farm["id"])
    owner = next(iter(members.values()))
    assert owner["role"] == "OWNER"
    assert owner["nickname"] is None


def test_current_farm_uses_and_persists_manual_selection() -> None:
    token = login(OWNER_PHONE)
    older_farm = create_farm(token, "较早创建的农场")
    newer_farm = create_farm(token, "较晚创建的农场")

    initial_response = call(token, "/api/v1/farms/current")
    assert initial_response.status_code == 200
    assert initial_response.json()["data"]["currentFarm"]["id"] == newer_farm["id"]

    select_response = call(
        token,
        "/api/v1/farms/current",
        method="put",
        json={"farmId": older_farm["id"]},
    )
    assert select_response.status_code == 200
    assert select_response.json()["data"]["id"] == older_farm["id"]

    restored_response = call(token, "/api/v1/farms/current")
    assert restored_response.status_code == 200
    assert restored_response.json()["data"]["currentFarm"]["id"] == older_farm["id"]

    list_response = call(token, "/api/v1/farms")
    assert list_response.status_code == 200
    assert list_response.json()["data"]["items"][0]["id"] == newer_farm["id"]


def test_current_farm_falls_back_when_preferred_farm_is_no_longer_available() -> None:
    owner_token = login(OWNER_PHONE)
    login(SECOND_OWNER_PHONE)
    preferred_farm = create_farm(owner_token, "原农场")
    fallback_farm = create_farm(owner_token, "备用农场")
    add_member(owner_token, preferred_farm["id"], SECOND_OWNER_PHONE, "OWNER")

    select_response = call(
        owner_token,
        "/api/v1/farms/current",
        method="put",
        json={"farmId": preferred_farm["id"]},
    )
    assert select_response.status_code == 200

    leave_response = call(
        owner_token,
        f"/api/v1/farms/{preferred_farm['id']}/members/me",
        method="delete",
    )
    assert leave_response.status_code == 204

    current_response = call(owner_token, "/api/v1/farms/current")
    assert current_response.status_code == 200
    assert current_response.json()["data"]["currentFarm"]["id"] == fallback_farm["id"]


def test_current_farm_is_empty_without_farms_and_cannot_select_an_unavailable_farm() -> None:
    owner_token = login(OWNER_PHONE)
    outsider_token = login(ADMIN_PHONE)
    farm = create_farm(owner_token)

    empty_response = call(outsider_token, "/api/v1/farms/current")
    assert empty_response.status_code == 200
    assert empty_response.json()["data"]["currentFarm"] is None

    unavailable_response = call(
        outsider_token,
        "/api/v1/farms/current",
        method="put",
        json={"farmId": farm["id"]},
    )
    assert unavailable_response.status_code == 404
    assert unavailable_response.json()["error"]["code"] == "NOT_FOUND"


def test_non_member_cannot_access_or_edit_farm() -> None:
    owner_token = login(OWNER_PHONE)
    outsider_token = login(ADMIN_PHONE)
    farm = create_farm(owner_token)

    detail_response = call(outsider_token, f"/api/v1/farms/{farm['id']}")
    edit_response = call(
        outsider_token,
        f"/api/v1/farms/{farm['id']}",
        method="patch",
        json={"name": "越权修改"},
    )

    assert detail_response.status_code == 404
    assert detail_response.json()["error"]["code"] == "NOT_FOUND"
    assert edit_response.status_code == 404
    assert edit_response.json()["error"]["code"] == "NOT_FOUND"

    owner_edit = call(
        owner_token,
        f"/api/v1/farms/{farm['id']}",
        method="patch",
        json={"name": "更新后的农场", "region": None},
    )
    assert owner_edit.status_code == 200
    assert owner_edit.json()["data"]["name"] == "更新后的农场"
    assert owner_edit.json()["data"]["region"] is None


def test_admin_cannot_edit_farm() -> None:
    owner_token = login(OWNER_PHONE)
    admin_token = login(ADMIN_PHONE)
    farm = create_farm(owner_token)
    add_member(owner_token, farm["id"], ADMIN_PHONE, "ADMIN")

    response = call(
        admin_token,
        f"/api/v1/farms/{farm['id']}",
        method="patch",
        json={"name": "管理员修改"},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_owner_admin_member_permissions_and_role_changes() -> None:
    owner_token = login(OWNER_PHONE)
    admin_token = login(ADMIN_PHONE)
    member_token = login(MEMBER_PHONE)
    login(SECOND_OWNER_PHONE)
    farm = create_farm(owner_token)

    admin = add_member(owner_token, farm["id"], ADMIN_PHONE, "ADMIN")
    member = add_member(owner_token, farm["id"], MEMBER_PHONE)
    second_owner = add_member(owner_token, farm["id"], SECOND_OWNER_PHONE, "OWNER")

    admin_cannot_demote_owner = call(
        admin_token,
        f"/api/v1/farms/{farm['id']}/members/{second_owner['id']}",
        method="patch",
        json={"role": "MEMBER"},
    )
    admin_cannot_create_owner = call(
        admin_token,
        f"/api/v1/farms/{farm['id']}/members",
        method="post",
        json={"phoneNumber": EXTRA_PHONE, "role": "OWNER"},
    )
    member_cannot_manage = call(
        member_token,
        f"/api/v1/farms/{farm['id']}/members/{admin['id']}",
        method="patch",
        json={"role": "MEMBER"},
    )
    assert admin_cannot_demote_owner.status_code == 403
    assert admin_cannot_create_owner.status_code == 403
    assert member_cannot_manage.status_code == 403

    admin_can_change_member = call(
        admin_token,
        f"/api/v1/farms/{farm['id']}/members/{member['id']}",
        method="patch",
        json={"role": "ADMIN"},
    )
    assert admin_can_change_member.status_code == 200
    assert admin_can_change_member.json()["data"]["role"] == "ADMIN"

    owner_can_demote_second_owner = call(
        owner_token,
        f"/api/v1/farms/{farm['id']}/members/{second_owner['id']}",
        method="patch",
        json={"role": "ADMIN"},
    )
    assert owner_can_demote_second_owner.status_code == 200
    assert owner_can_demote_second_owner.json()["data"]["role"] == "ADMIN"

    owner_can_remove_member = call(
        owner_token,
        f"/api/v1/farms/{farm['id']}/members/{second_owner['id']}",
        method="delete",
    )
    assert owner_can_remove_member.status_code == 204
    assert second_owner["id"] not in {
        item["id"] for item in members_by_user_id(owner_token, farm["id"]).values()
    }

    owner_cannot_remove_self_through_member_endpoint = call(
        owner_token,
        f"/api/v1/farms/{farm['id']}/members/"
        f"{members_by_user_id(owner_token, farm['id'])[current_user_id(owner_token)]['id']}",
        method="delete",
    )
    assert owner_cannot_remove_self_through_member_endpoint.status_code == 403


def test_owner_minimum_and_leave_rules() -> None:
    owner_token = login(OWNER_PHONE)
    second_owner_token = login(SECOND_OWNER_PHONE)
    member_token = login(MEMBER_PHONE)
    farm = create_farm(owner_token)
    add_member(owner_token, farm["id"], SECOND_OWNER_PHONE, "OWNER")
    add_member(owner_token, farm["id"], MEMBER_PHONE)

    second_owner_leave = call(
        second_owner_token,
        f"/api/v1/farms/{farm['id']}/members/me",
        method="delete",
    )
    assert second_owner_leave.status_code == 204

    last_owner_cannot_leave = call(
        owner_token,
        f"/api/v1/farms/{farm['id']}/members/me",
        method="delete",
    )
    assert last_owner_cannot_leave.status_code == 409
    assert last_owner_cannot_leave.json()["error"]["code"] == "BUSINESS_CONFLICT"

    last_owner_cannot_be_removed = call(
        owner_token,
        f"/api/v1/farms/{farm['id']}/members/"
        f"{members_by_user_id(owner_token, farm['id'])[current_user_id(owner_token)]['id']}",
        method="delete",
    )
    assert last_owner_cannot_be_removed.status_code == 403

    member_leave = call(
        member_token,
        f"/api/v1/farms/{farm['id']}/members/me",
        method="delete",
    )
    assert member_leave.status_code == 204


def test_duplicate_and_unknown_member_are_rejected() -> None:
    owner_token = login(OWNER_PHONE)
    login(ADMIN_PHONE)
    farm = create_farm(owner_token)
    add_member(owner_token, farm["id"], ADMIN_PHONE)

    duplicate = call(
        owner_token,
        f"/api/v1/farms/{farm['id']}/members",
        method="post",
        json={"phoneNumber": ADMIN_PHONE},
    )
    unknown = call(
        owner_token,
        f"/api/v1/farms/{farm['id']}/members",
        method="post",
        json={"phoneNumber": "13900000000"},
    )

    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "BUSINESS_CONFLICT"
    assert unknown.status_code == 404
    assert unknown.json()["error"]["code"] == "NOT_FOUND"
