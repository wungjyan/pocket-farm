import asyncio
from collections.abc import Mapping
from datetime import UTC, date, datetime, timedelta
from typing import Any

import httpx

from app.db.session import async_session_factory, engine
from app.main import app
from app.models.operation import OperationType, OperationTypeStatus
from app.models.production import Production, ProductionStatus

OWNER_PHONE = "13800000001"
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


def create_farm(token: str, name: str = "农事测试农场") -> dict[str, Any]:
    response = call(token, "/api/v1/farms", method="post", json={"name": name})
    assert response.status_code == 201
    return response.json()["data"]


def create_plot(token: str, farm_id: int, name: str) -> dict[str, Any]:
    response = call(
        token,
        f"/api/v1/farms/{farm_id}/plots",
        method="post",
        json={"name": name, "type": "FIELD", "areaValue": 1, "areaUnit": "MU"},
    )
    assert response.status_code == 201
    return response.json()["data"]


def add_member(token: str, farm_id: int, phone: str) -> dict[str, Any]:
    response = call(
        token,
        f"/api/v1/farms/{farm_id}/members",
        method="post",
        json={"phoneNumber": phone},
    )
    assert response.status_code == 201
    return response.json()["data"]


def species_by_name(token: str, name: str) -> dict[str, Any]:
    response = call(token, f"/api/v1/species?keyword={name}&pageSize=100")
    assert response.status_code == 200
    return next(item for item in response.json()["data"]["items"] if item["name"] == name)


def start_agriculture_production(token: str, plot_id: int, species_id: int) -> dict[str, Any]:
    response = call(
        token,
        f"/api/v1/plots/{plot_id}/productions",
        method="post",
        json={
            "speciesId": species_id,
            "startedOn": (date.today() - timedelta(days=2)).isoformat(),
            "plantingStandard": "NORMAL",
            "plantingMethod": "TRANSPLANT",
            "workMethod": "MANUAL",
        },
    )
    assert response.status_code == 201
    return response.json()["data"]


def create_operation(token: str, plot_id: int, payload: Mapping[str, Any]) -> httpx.Response:
    request_payload = dict(payload)
    operation_type_code = request_payload.pop("operationType", None)
    if operation_type_code is not None:
        request_payload["operationTypeId"] = operation_type_id(token, operation_type_code)
    return call(token, f"/api/v1/plots/{plot_id}/operations", method="post", json=request_payload)


def operation_type_id(token: str, code: str) -> int:
    response = call(token, "/api/v1/operation-types?pageSize=100")
    assert response.status_code == 200
    return next(item["id"] for item in response.json()["data"]["items"] if item["code"] == code)


def current_user_id(token: str) -> int:
    response = call(token, "/api/v1/users/me")
    assert response.status_code == 200
    return response.json()["data"]["id"]


async def mark_production_ended(production_id: int) -> None:
    async with async_session_factory() as session:
        production = await session.get(Production, production_id)
        assert production is not None
        production.status = ProductionStatus.ENDED
        production.ended_on = date.today()
        await session.commit()
    await engine.dispose()


async def set_operation_type_status(operation_type_id: int, status: OperationTypeStatus) -> None:
    async with async_session_factory() as session:
        operation_type = await session.get(OperationType, operation_type_id)
        assert operation_type is not None
        operation_type.status = status
        await session.commit()
    await engine.dispose()


def test_operation_types_only_expose_active_records_and_reject_disabled_type() -> None:
    owner_token = login(OWNER_PHONE)
    farm = create_farm(owner_token)
    plot = create_plot(owner_token, farm["id"], "农事类型测试地块")
    operation_types = call(owner_token, "/api/v1/operation-types?pageSize=100")
    assert operation_types.status_code == 200
    plow = next(item for item in operation_types.json()["data"]["items"] if item["code"] == "PLOW")
    assert plow["status"] == "ACTIVE"

    asyncio.run(set_operation_type_status(plow["id"], OperationTypeStatus.DISABLED))
    try:
        active_types = call(owner_token, "/api/v1/operation-types?pageSize=100")
        create_response = create_operation(
            owner_token,
            plot["id"],
            {"operationTypeId": plow["id"], "productionId": None},
        )
        assert active_types.status_code == 200
        assert all(item["id"] != plow["id"] for item in active_types.json()["data"]["items"])
        assert create_response.status_code == 409
    finally:
        asyncio.run(set_operation_type_status(plow["id"], OperationTypeStatus.ACTIVE))


def test_empty_plot_operation_uses_defaults_and_lists_by_operated_at() -> None:
    owner_token = login(OWNER_PHONE)
    farm = create_farm(owner_token)
    plot = create_plot(owner_token, farm["id"], "空闲地块")

    first_response = create_operation(
        owner_token,
        plot["id"],
        {"operationType": "PLOW", "productionId": None, "remark": "翻耕"},
    )
    assert first_response.status_code == 201
    first = first_response.json()["data"]
    assert first["plotId"] == plot["id"]
    assert first["productionId"] is None
    assert first["operationType"]["code"] == "PLOW"
    assert first["operationType"]["name"] == "翻耕"
    assert first["workMethod"] == "MANUAL"
    assert first["operatorId"] == first["createdBy"]

    earlier = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
    second_response = create_operation(
        owner_token,
        plot["id"],
        {"operationType": "IRRIGATE", "productionId": None, "operatedAt": earlier},
    )
    assert second_response.status_code == 201
    list_response = call(owner_token, f"/api/v1/plots/{plot['id']}/operations")
    assert list_response.status_code == 200
    items = list_response.json()["data"]["items"]
    assert [item["id"] for item in items] == [first["id"], second_response.json()["data"]["id"]]
    delete_response = call(
        owner_token,
        f"/api/v1/operations/{second_response.json()['data']['id']}",
        method="delete",
    )
    assert delete_response.status_code == 204


def test_operation_requires_explicit_matching_production_and_validates_dates() -> None:
    owner_token = login(OWNER_PHONE)
    farm = create_farm(owner_token)
    plot = create_plot(owner_token, farm["id"], "1号大棚")
    other_plot = create_plot(owner_token, farm["id"], "2号大棚")
    cucumber = species_by_name(owner_token, "黄瓜")
    production = start_agriculture_production(owner_token, plot["id"], cucumber["id"])
    other_production = start_agriculture_production(owner_token, other_plot["id"], cucumber["id"])

    missing_production = create_operation(owner_token, plot["id"], {"operationType": "FERTILIZE"})
    wrong_plot = create_operation(
        owner_token,
        plot["id"],
        {"operationType": "FERTILIZE", "productionId": other_production["id"]},
    )
    before_start = create_operation(
        owner_token,
        plot["id"],
        {
            "operationType": "FERTILIZE",
            "productionId": production["id"],
            "operatedAt": (datetime.now(UTC) - timedelta(days=3)).isoformat(),
        },
    )
    future = create_operation(
        owner_token,
        plot["id"],
        {
            "operationType": "FERTILIZE",
            "productionId": production["id"],
            "operatedAt": (datetime.now(UTC) + timedelta(minutes=1)).isoformat(),
        },
    )
    created = create_operation(
        owner_token,
        plot["id"],
        {
            "operationType": "FERTILIZE",
            "productionId": production["id"],
            "workMethod": "MECHANICAL",
            "operatedAt": datetime.now(UTC).isoformat(),
        },
    )
    assert missing_production.status_code == 422
    assert wrong_plot.status_code == 422
    assert before_start.status_code == 422
    assert future.status_code == 422
    assert created.status_code == 201
    assert created.json()["data"]["productionId"] == production["id"]


def test_operator_access_and_production_correction_and_deletion_are_restricted() -> None:
    owner_token = login(OWNER_PHONE)
    login(MEMBER_PHONE)
    outsider_token = login(OUTSIDER_PHONE)
    farm = create_farm(owner_token)
    member = add_member(owner_token, farm["id"], MEMBER_PHONE)
    plot = create_plot(owner_token, farm["id"], "成员地块")
    cucumber = species_by_name(owner_token, "黄瓜")
    production = start_agriculture_production(owner_token, plot["id"], cucumber["id"])

    invalid_operator = create_operation(
        owner_token,
        plot["id"],
        {
            "operationType": "FERTILIZE",
            "productionId": production["id"],
            "operatorId": current_user_id(outsider_token),
        },
    )
    operation_response = create_operation(
        owner_token,
        plot["id"],
        {
            "operationType": "FERTILIZE",
            "productionId": production["id"],
            "operatorId": member["userId"],
        },
    )
    assert invalid_operator.status_code == 422
    assert operation_response.status_code == 201
    operation = operation_response.json()["data"]
    assert operation["operatorId"] == member["userId"]
    assert operation["createdBy"] != operation["operatorId"]

    outsider_list = call(outsider_token, f"/api/v1/plots/{plot['id']}/operations")
    outsider_edit = call(
        outsider_token,
        f"/api/v1/operations/{operation['id']}",
        method="patch",
        json={"remark": "越权修改"},
    )
    core_update = call(
        owner_token,
        f"/api/v1/productions/{production['id']}",
        method="patch",
        json={"startedOn": (date.today() - timedelta(days=1)).isoformat()},
    )
    production_delete = call(
        owner_token,
        f"/api/v1/productions/{production['id']}",
        method="delete",
    )
    assert outsider_list.status_code == 404
    assert outsider_edit.status_code == 404
    assert core_update.status_code == 409
    assert production_delete.status_code == 409


def test_operation_can_be_edited_or_deleted_when_active_but_locks_when_ended() -> None:
    owner_token = login(OWNER_PHONE)
    farm = create_farm(owner_token)
    plot = create_plot(owner_token, farm["id"], "锁定测试地块")
    cucumber = species_by_name(owner_token, "黄瓜")
    production = start_agriculture_production(owner_token, plot["id"], cucumber["id"])
    create_response = create_operation(
        owner_token,
        plot["id"],
        {"operationType": "FERTILIZE", "productionId": production["id"]},
    )
    assert create_response.status_code == 201
    operation = create_response.json()["data"]

    edit_response = call(
        owner_token,
        f"/api/v1/operations/{operation['id']}",
        method="patch",
        json={"operationTypeId": operation_type_id(owner_token, "IRRIGATE"), "remark": "补水"},
    )
    assert edit_response.status_code == 200, edit_response.json()
    assert edit_response.json()["data"]["operationType"]["code"] == "IRRIGATE"
    premature_end = call(
        owner_token,
        f"/api/v1/productions/{production['id']}/end",
        method="post",
        json={"endedOn": (date.today() - timedelta(days=1)).isoformat()},
    )
    end_response = call(
        owner_token,
        f"/api/v1/productions/{production['id']}/end",
        method="post",
        json={},
    )
    assert premature_end.status_code == 422
    assert end_response.status_code == 200

    ended_create = create_operation(
        owner_token,
        plot["id"],
        {"operationType": "WEED", "productionId": production["id"]},
    )
    ended_edit = call(
        owner_token,
        f"/api/v1/operations/{operation['id']}",
        method="patch",
        json={"remark": "结束后不可修改"},
    )
    ended_delete = call(
        owner_token,
        f"/api/v1/operations/{operation['id']}",
        method="delete",
    )
    assert ended_create.status_code == 409
    assert ended_edit.status_code == 409
    assert ended_delete.status_code == 409
