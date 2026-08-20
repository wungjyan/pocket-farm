import asyncio
from collections.abc import Mapping
from datetime import UTC, date, datetime, timedelta
from typing import Any

import httpx

from app.db.session import async_session_factory, engine
from app.main import app
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


def create_farm(token: str, name: str = "收获测试农场") -> dict[str, Any]:
    response = call(token, "/api/v1/farms", method="post", json={"name": name})
    assert response.status_code == 201
    return response.json()["data"]


def create_plot(token: str, farm_id: int, name: str) -> dict[str, Any]:
    response = call(
        token,
        f"/api/v1/farms/{farm_id}/plots",
        method="post",
        json={"name": name},
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


def start_agriculture_production(
    token: str,
    plot_id: int,
    species_id: int,
    *,
    days_ago: int = 2,
) -> dict[str, Any]:
    response = call(
        token,
        f"/api/v1/plots/{plot_id}/productions",
        method="post",
        json={
            "speciesId": species_id,
            "startedOn": (date.today() - timedelta(days=days_ago)).isoformat(),
            "plantingStandard": "NORMAL",
            "plantingMethod": "TRANSPLANT",
            "workMethod": "MANUAL",
        },
    )
    assert response.status_code == 201
    return response.json()["data"]


def start_industry_production(
    token: str,
    plot_id: int,
    species_id: int,
    *,
    industry: str,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "speciesId": species_id,
        "startedOn": (date.today() - timedelta(days=1)).isoformat(),
    }
    if industry == "FORESTRY":
        payload.update(
            {
                "plantingStandard": "NORMAL",
                "plantingMethod": "TRANSPLANT",
                "workMethod": "MANUAL",
                "initialQuantity": 30,
            }
        )
    elif industry == "LIVESTOCK":
        payload.update({"initialQuantity": 20, "entryAgeDays": 7})
    elif industry == "FISHERY":
        payload.update({"initialQuantity": 100, "workMethod": "MANUAL"})
    response = call(
        token,
        f"/api/v1/plots/{plot_id}/productions",
        method="post",
        json=payload,
    )
    assert response.status_code == 201
    return response.json()["data"]


def create_harvest(
    token: str,
    production_id: int,
    payload: Mapping[str, Any],
) -> httpx.Response:
    return call(
        token,
        f"/api/v1/productions/{production_id}/harvests",
        method="post",
        json=payload,
    )


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


def test_multiple_harvests_use_defaults_and_both_lists_sort_by_time() -> None:
    owner_token = login(OWNER_PHONE)
    farm = create_farm(owner_token)
    plot = create_plot(owner_token, farm["id"], "多次采收地块")
    cucumber = species_by_name(owner_token, "黄瓜")
    first_production = start_agriculture_production(owner_token, plot["id"], cucumber["id"])
    second_production = start_agriculture_production(owner_token, plot["id"], cucumber["id"])

    latest_response = create_harvest(
        owner_token,
        first_production["id"],
        {"quantity": 100},
    )
    earlier_time = (datetime.now(UTC) - timedelta(hours=2)).isoformat()
    earlier_response = create_harvest(
        owner_token,
        first_production["id"],
        {
            "quantity": 120.5,
            "workMethod": "MECHANICAL",
            "harvestedAt": earlier_time,
            "grade": "一级",
        },
    )
    oldest_response = create_harvest(
        owner_token,
        second_production["id"],
        {
            "quantity": 80,
            "harvestedAt": (datetime.now(UTC) - timedelta(hours=4)).isoformat(),
        },
    )
    assert latest_response.status_code == 201
    assert earlier_response.status_code == 201
    assert oldest_response.status_code == 201
    latest = latest_response.json()["data"]
    assert latest["productionId"] == first_production["id"]
    assert latest["unit"] == "KG"
    assert latest["workMethod"] == "MANUAL"
    assert latest["operatorId"] == latest["createdBy"]
    assert latest["productName"] == "黄瓜"

    production_list = call(
        owner_token,
        f"/api/v1/productions/{first_production['id']}/harvests",
    )
    assert production_list.status_code == 200
    assert production_list.json()["data"]["total"] == 2
    assert [item["id"] for item in production_list.json()["data"]["items"]] == [
        latest["id"],
        earlier_response.json()["data"]["id"],
    ]

    plot_list = call(owner_token, f"/api/v1/plots/{plot['id']}/harvests?pageSize=2")
    assert plot_list.status_code == 200
    assert plot_list.json()["data"]["total"] == 3
    assert [item["id"] for item in plot_list.json()["data"]["items"]] == [
        latest["id"],
        earlier_response.json()["data"]["id"],
    ]

    production_detail = call(
        owner_token,
        f"/api/v1/productions/{first_production['id']}",
    )
    assert production_detail.status_code == 200
    assert production_detail.json()["data"]["status"] == "ACTIVE"


def test_harvest_derives_units_and_validates_quantity_and_time_boundaries() -> None:
    owner_token = login(OWNER_PHONE)
    farm = create_farm(owner_token)
    plot = create_plot(owner_token, farm["id"], "数量校验地块")
    cucumber = species_by_name(owner_token, "黄瓜")
    production = start_agriculture_production(
        owner_token,
        plot["id"],
        cucumber["id"],
        days_ago=2,
    )

    decimal_kg = create_harvest(
        owner_token,
        production["id"],
        {"quantity": 12.5},
    )
    client_unit = create_harvest(
        owner_token,
        production["id"],
        {"quantity": 1.5, "unit": "HEAD"},
    )
    unknown_unit = create_harvest(
        owner_token,
        production["id"],
        {"quantity": 1, "unit": "BOX"},
    )
    excessive_precision = create_harvest(
        owner_token,
        production["id"],
        {"quantity": 1.23456},
    )
    before_start = create_harvest(
        owner_token,
        production["id"],
        {
            "quantity": 1,
            "harvestedAt": (datetime.now(UTC) - timedelta(days=3)).isoformat(),
        },
    )
    future = create_harvest(
        owner_token,
        production["id"],
        {
            "quantity": 1,
            "harvestedAt": (datetime.now(UTC) + timedelta(minutes=1)).isoformat(),
        },
    )
    no_timezone = create_harvest(
        owner_token,
        production["id"],
        {"quantity": 1, "harvestedAt": "2026-08-20T08:00:00"},
    )
    assert decimal_kg.status_code == 201
    assert decimal_kg.json()["data"]["unit"] == "KG"
    assert client_unit.status_code == 422
    assert unknown_unit.status_code == 422
    assert excessive_precision.status_code == 422
    assert before_start.status_code == 422
    assert future.status_code == 422
    assert no_timezone.status_code == 422

    cedar = species_by_name(owner_token, "杉木")
    sheep = species_by_name(owner_token, "羊")
    chicken = species_by_name(owner_token, "鸡")
    carp = species_by_name(owner_token, "鲤鱼")
    forestry = start_industry_production(
        owner_token,
        plot["id"],
        cedar["id"],
        industry="FORESTRY",
    )
    livestock = start_industry_production(
        owner_token,
        plot["id"],
        chicken["id"],
        industry="LIVESTOCK",
    )
    sheep_production = start_industry_production(
        owner_token,
        plot["id"],
        sheep["id"],
        industry="LIVESTOCK",
    )
    fishery = start_industry_production(
        owner_token,
        plot["id"],
        carp["id"],
        industry="FISHERY",
    )
    forestry_harvest = create_harvest(owner_token, forestry["id"], {"quantity": 2})
    livestock_harvest = create_harvest(owner_token, livestock["id"], {"quantity": 3})
    sheep_harvest = create_harvest(owner_token, sheep_production["id"], {"quantity": 4})
    decimal_livestock = create_harvest(owner_token, livestock["id"], {"quantity": 1.5})
    fishery_harvest = create_harvest(owner_token, fishery["id"], {"quantity": 6.5})
    assert forestry_harvest.status_code == 201
    assert forestry_harvest.json()["data"]["unit"] == "PLANT"
    assert livestock_harvest.status_code == 201
    assert livestock_harvest.json()["data"]["unit"] == "FEATHER"
    assert sheep_harvest.status_code == 201
    assert sheep_harvest.json()["data"]["unit"] == "HEAD"
    assert decimal_livestock.status_code == 422
    assert fishery_harvest.status_code == 201
    assert fishery_harvest.json()["data"]["unit"] == "KG"


def test_operator_can_change_but_creator_is_preserved_and_outsiders_are_hidden() -> None:
    owner_token = login(OWNER_PHONE)
    login(MEMBER_PHONE)
    outsider_token = login(OUTSIDER_PHONE)
    farm = create_farm(owner_token)
    member = add_member(owner_token, farm["id"], MEMBER_PHONE)
    plot = create_plot(owner_token, farm["id"], "操作人测试地块")
    cucumber = species_by_name(owner_token, "黄瓜")
    production = start_agriculture_production(owner_token, plot["id"], cucumber["id"])

    invalid_operator = create_harvest(
        owner_token,
        production["id"],
        {
            "quantity": 10,
            "operatorId": current_user_id(outsider_token),
        },
    )
    created_response = create_harvest(
        owner_token,
        production["id"],
        {"quantity": 10, "operatorId": member["userId"]},
    )
    assert invalid_operator.status_code == 422
    assert created_response.status_code == 201
    created = created_response.json()["data"]
    assert created["operatorId"] == member["userId"]
    assert created["createdBy"] != created["operatorId"]

    owner_id = current_user_id(owner_token)
    update_response = call(
        owner_token,
        f"/api/v1/harvests/{created['id']}",
        method="patch",
        json={"operatorId": owner_id, "quantity": 3, "remark": "更正"},
    )
    assert update_response.status_code == 200, update_response.json()
    updated = update_response.json()["data"]
    assert updated["operatorId"] == owner_id
    assert updated["unit"] == "KG"
    assert updated["createdBy"] == created["createdBy"]
    assert updated["createdAt"] == created["createdAt"]

    outsider_list = call(
        outsider_token,
        f"/api/v1/productions/{production['id']}/harvests",
    )
    outsider_edit = call(
        outsider_token,
        f"/api/v1/harvests/{created['id']}",
        method="patch",
        json={"remark": "越权修改"},
    )
    assert outsider_list.status_code == 404
    assert outsider_edit.status_code == 404


def test_cross_farm_creation_is_hidden_and_harvest_blocks_core_production_changes() -> None:
    owner_token = login(OWNER_PHONE)
    outsider_token = login(OUTSIDER_PHONE)
    owner_farm = create_farm(owner_token, "本农场")
    owner_plot = create_plot(owner_token, owner_farm["id"], "本地块")
    outsider_farm = create_farm(outsider_token, "外部农场")
    outsider_plot = create_plot(outsider_token, outsider_farm["id"], "外部地块")
    cucumber = species_by_name(owner_token, "黄瓜")
    owner_production = start_agriculture_production(
        owner_token,
        owner_plot["id"],
        cucumber["id"],
    )
    outsider_production = start_agriculture_production(
        outsider_token,
        outsider_plot["id"],
        cucumber["id"],
    )

    cross_create = create_harvest(
        owner_token,
        outsider_production["id"],
        {"quantity": 10},
    )
    cross_plot_list = call(owner_token, f"/api/v1/plots/{outsider_plot['id']}/harvests")
    created = create_harvest(
        owner_token,
        owner_production["id"],
        {"quantity": 10},
    )
    assert cross_create.status_code == 404
    assert cross_plot_list.status_code == 404
    assert created.status_code == 201

    core_update = call(
        owner_token,
        f"/api/v1/productions/{owner_production['id']}",
        method="patch",
        json={"startedOn": (date.today() - timedelta(days=1)).isoformat()},
    )
    production_delete = call(
        owner_token,
        f"/api/v1/productions/{owner_production['id']}",
        method="delete",
    )
    assert core_update.status_code == 409
    assert production_delete.status_code == 409


def test_harvest_edit_and_delete_lock_after_production_ends() -> None:
    owner_token = login(OWNER_PHONE)
    farm = create_farm(owner_token)
    plot = create_plot(owner_token, farm["id"], "结束锁定地块")
    cucumber = species_by_name(owner_token, "黄瓜")
    production = start_agriculture_production(owner_token, plot["id"], cucumber["id"])

    deletable_response = create_harvest(
        owner_token,
        production["id"],
        {"quantity": 8},
    )
    assert deletable_response.status_code == 201
    delete_response = call(
        owner_token,
        f"/api/v1/harvests/{deletable_response.json()['data']['id']}",
        method="delete",
    )
    assert delete_response.status_code == 204

    locked_response = create_harvest(
        owner_token,
        production["id"],
        {"quantity": 12},
    )
    assert locked_response.status_code == 201
    locked = locked_response.json()["data"]
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

    ended_create = create_harvest(
        owner_token,
        production["id"],
        {"quantity": 5},
    )
    ended_edit = call(
        owner_token,
        f"/api/v1/harvests/{locked['id']}",
        method="patch",
        json={"remark": "结束后不可修改"},
    )
    ended_delete = call(
        owner_token,
        f"/api/v1/harvests/{locked['id']}",
        method="delete",
    )
    ended_list = call(
        owner_token,
        f"/api/v1/productions/{production['id']}/harvests",
    )
    assert ended_create.status_code == 409
    assert ended_edit.status_code == 409
    assert ended_delete.status_code == 409
    assert ended_list.status_code == 200
    assert ended_list.json()["data"]["total"] == 1
