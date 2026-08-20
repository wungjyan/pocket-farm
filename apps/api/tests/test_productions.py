import asyncio
from collections.abc import Mapping
from datetime import date, timedelta
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


def create_farm(token: str, name: str = "种养测试农场") -> dict[str, Any]:
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


def add_member(token: str, farm_id: int, phone: str) -> None:
    response = call(
        token,
        f"/api/v1/farms/{farm_id}/members",
        method="post",
        json={"phoneNumber": phone},
    )
    assert response.status_code == 201


def species_by_name(token: str, name: str) -> dict[str, Any]:
    response = call(token, f"/api/v1/species?keyword={name}&pageSize=100")
    assert response.status_code == 200
    return next(item for item in response.json()["data"]["items"] if item["name"] == name)


def start_production(
    token: str,
    plot_id: int,
    species_id: int,
    *,
    industry: str = "AGRICULTURE",
    **overrides: Any,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "speciesId": species_id,
        "startedOn": (date.today() - timedelta(days=1)).isoformat(),
    }
    if industry in {"AGRICULTURE", "FORESTRY"}:
        payload.update(
            {
                "plantingStandard": "NORMAL",
                "plantingMethod": "TRANSPLANT",
                "workMethod": "MANUAL",
            }
        )
    elif industry == "LIVESTOCK":
        payload.update({"initialQuantity": "1", "entryAgeDays": 1})
    elif industry == "FISHERY":
        payload.update({"initialQuantity": "1", "workMethod": "MANUAL"})
    payload.update(overrides)
    response = call(
        token,
        f"/api/v1/plots/{plot_id}/productions",
        method="post",
        json=payload,
    )
    assert response.status_code == 201
    return response.json()["data"]


async def mark_production_ended(production_id: int) -> None:
    async with async_session_factory() as session:
        production = await session.get(Production, production_id)
        assert production is not None
        production.status = ProductionStatus.ENDED
        production.ended_on = date.today()
        await session.commit()
    await engine.dispose()


def test_species_search_and_agriculture_production_fields() -> None:
    owner_token = login(OWNER_PHONE)
    all_species_response = call(owner_token, "/api/v1/species?pageSize=100")
    agriculture_response = call(owner_token, "/api/v1/species?industry=AGRICULTURE&keyword=黄")
    assert all_species_response.status_code == 200
    assert all_species_response.json()["data"]["total"] == 23
    assert agriculture_response.status_code == 200
    assert agriculture_response.json()["data"]["items"][0]["name"] == "黄瓜"
    assert agriculture_response.json()["data"]["items"][0]["individualUnit"] == "PLANT"

    farm = create_farm(owner_token)
    plot = create_plot(owner_token, farm["id"], "1号大棚")
    cucumber = species_by_name(owner_token, "黄瓜")
    production = start_production(
        owner_token,
        plot["id"],
        cucumber["id"],
        variety="水果黄瓜",
        expectedYieldPerMu="120.5",
        initialQuantity="300",
        plantSpacingCm="35",
    )
    assert production["status"] == "ACTIVE"
    assert production["speciesName"] == "黄瓜"
    assert production["industry"] == "AGRICULTURE"
    assert production["individualUnit"] == "PLANT"
    assert production["plantingStandard"] == "NORMAL"
    assert production["plantingMethod"] == "TRANSPLANT"
    assert production["workMethod"] == "MANUAL"
    assert float(production["expectedYieldPerMu"]) == 120.5
    assert float(production["initialQuantity"]) == 300
    assert float(production["plantSpacingCm"]) == 35

    detail_response = call(owner_token, f"/api/v1/productions/{production['id']}")
    list_response = call(owner_token, f"/api/v1/plots/{plot['id']}/productions?status=ACTIVE")
    assert detail_response.status_code == 200
    assert list_response.status_code == 200
    assert list_response.json()["data"]["total"] == 1


def test_industry_specific_required_fields_and_fixed_units() -> None:
    owner_token = login(OWNER_PHONE)
    farm = create_farm(owner_token)
    plot = create_plot(owner_token, farm["id"], "综合地块")
    cedar = species_by_name(owner_token, "杉木")
    pig = species_by_name(owner_token, "猪")
    chicken = species_by_name(owner_token, "鸡")
    carp = species_by_name(owner_token, "鲤鱼")

    missing_forest_quantity = call(
        owner_token,
        f"/api/v1/plots/{plot['id']}/productions",
        method="post",
        json={
            "speciesId": cedar["id"],
            "startedOn": date.today().isoformat(),
            "plantingStandard": "NORMAL",
            "plantingMethod": "TRANSPLANT",
            "workMethod": "MANUAL",
        },
    )
    missing_livestock_age = call(
        owner_token,
        f"/api/v1/plots/{plot['id']}/productions",
        method="post",
        json={
            "speciesId": pig["id"],
            "startedOn": date.today().isoformat(),
            "initialQuantity": "3",
        },
    )
    missing_fish_work_method = call(
        owner_token,
        f"/api/v1/plots/{plot['id']}/productions",
        method="post",
        json={
            "speciesId": carp["id"],
            "startedOn": date.today().isoformat(),
            "initialQuantity": "30",
        },
    )
    assert missing_forest_quantity.status_code == 422
    assert missing_livestock_age.status_code == 422
    assert missing_fish_work_method.status_code == 422

    forestry = start_production(
        owner_token,
        plot["id"],
        cedar["id"],
        industry="FORESTRY",
        initialQuantity="30",
        plantSpacingCm="120",
    )
    livestock = start_production(
        owner_token,
        plot["id"],
        chicken["id"],
        industry="LIVESTOCK",
        initialQuantity="20",
        entryAgeDays=7,
    )
    fishery = start_production(
        owner_token,
        plot["id"],
        carp["id"],
        industry="FISHERY",
        initialQuantity="100",
    )
    assert forestry["individualUnit"] == "PLANT"
    assert livestock["individualUnit"] == "FEATHER"
    assert livestock["workMethod"] is None
    assert fishery["individualUnit"] == "TAIL"
    assert fishery["workMethod"] == "MANUAL"


def test_plot_allows_multiple_active_productions_and_core_fields_can_be_corrected() -> None:
    owner_token = login(OWNER_PHONE)
    farm = create_farm(owner_token)
    plot = create_plot(owner_token, farm["id"], "综合地块")
    second_plot = create_plot(owner_token, farm["id"], "备用地块")
    cucumber = species_by_name(owner_token, "黄瓜")
    tomato = species_by_name(owner_token, "番茄")

    first = start_production(owner_token, plot["id"], cucumber["id"])
    second = start_production(owner_token, plot["id"], tomato["id"], variety="樱桃番茄")
    list_response = call(owner_token, f"/api/v1/plots/{plot['id']}/productions?status=ACTIVE")
    assert list_response.status_code == 200
    assert list_response.json()["data"]["total"] == 2

    edit_response = call(
        owner_token,
        f"/api/v1/productions/{first['id']}",
        method="patch",
        json={
            "plotId": second_plot["id"],
            "speciesId": tomato["id"],
            "startedOn": (date.today() - timedelta(days=2)).isoformat(),
        },
    )
    assert edit_response.status_code == 200
    edited = edit_response.json()["data"]
    assert edited["plotId"] == second_plot["id"]
    assert edited["speciesName"] == "番茄"
    assert second["status"] == "ACTIVE"

    delete_response = call(owner_token, f"/api/v1/productions/{first['id']}", method="delete")
    assert delete_response.status_code == 204


def test_member_can_create_and_correct_production_but_outsider_cannot_access_it() -> None:
    owner_token = login(OWNER_PHONE)
    member_token = login(MEMBER_PHONE)
    outsider_token = login(OUTSIDER_PHONE)
    farm = create_farm(owner_token)
    add_member(owner_token, farm["id"], MEMBER_PHONE)
    plot = create_plot(owner_token, farm["id"], "成员地块")
    cucumber = species_by_name(owner_token, "黄瓜")

    production = start_production(member_token, plot["id"], cucumber["id"])
    member_edit = call(
        member_token,
        f"/api/v1/productions/{production['id']}",
        method="patch",
        json={"remark": "成员补充备注"},
    )
    outsider_detail = call(outsider_token, f"/api/v1/productions/{production['id']}")
    outsider_edit = call(
        outsider_token,
        f"/api/v1/productions/{production['id']}",
        method="patch",
        json={"remark": "越权修改"},
    )
    assert member_edit.status_code == 200
    assert outsider_detail.status_code == 404
    assert outsider_edit.status_code == 404


def test_production_validates_integer_quantity_dates_and_ended_state() -> None:
    owner_token = login(OWNER_PHONE)
    farm = create_farm(owner_token)
    plot = create_plot(owner_token, farm["id"], "1号栏舍")
    pig = species_by_name(owner_token, "猪")
    cucumber = species_by_name(owner_token, "黄瓜")

    fractional_quantity = call(
        owner_token,
        f"/api/v1/plots/{plot['id']}/productions",
        method="post",
        json={
            "speciesId": pig["id"],
            "startedOn": date.today().isoformat(),
            "initialQuantity": "1.5",
            "entryAgeDays": 3,
        },
    )
    future_date = call(
        owner_token,
        f"/api/v1/plots/{plot['id']}/productions",
        method="post",
        json={
            "speciesId": cucumber["id"],
            "startedOn": (date.today() + timedelta(days=1)).isoformat(),
            "plantingStandard": "NORMAL",
            "plantingMethod": "TRANSPLANT",
            "workMethod": "MANUAL",
        },
    )
    assert fractional_quantity.status_code == 422
    assert future_date.status_code == 422

    production = start_production(owner_token, plot["id"], cucumber["id"])
    asyncio.run(mark_production_ended(production["id"]))
    ended_edit = call(
        owner_token,
        f"/api/v1/productions/{production['id']}",
        method="patch",
        json={"remark": "结束后不可编辑"},
    )
    ended_delete = call(owner_token, f"/api/v1/productions/{production['id']}", method="delete")
    assert ended_edit.status_code == 409
    assert ended_delete.status_code == 409


def test_production_can_end_once_with_valid_business_dates() -> None:
    owner_token = login(OWNER_PHONE)
    outsider_token = login(OUTSIDER_PHONE)
    farm = create_farm(owner_token)
    plot = create_plot(owner_token, farm["id"], "结束测试地块")
    cucumber = species_by_name(owner_token, "黄瓜")
    production = start_production(
        owner_token,
        plot["id"],
        cucumber["id"],
        startedOn=(date.today() - timedelta(days=2)).isoformat(),
    )

    outsider_end = call(
        outsider_token,
        f"/api/v1/productions/{production['id']}/end",
        method="post",
        json={},
    )
    before_start = call(
        owner_token,
        f"/api/v1/productions/{production['id']}/end",
        method="post",
        json={"endedOn": (date.today() - timedelta(days=3)).isoformat()},
    )
    future_end = call(
        owner_token,
        f"/api/v1/productions/{production['id']}/end",
        method="post",
        json={"endedOn": (date.today() + timedelta(days=1)).isoformat()},
    )
    ended = call(
        owner_token,
        f"/api/v1/productions/{production['id']}/end",
        method="post",
        json={},
    )
    repeated_end = call(
        owner_token,
        f"/api/v1/productions/{production['id']}/end",
        method="post",
        json={},
    )

    assert outsider_end.status_code == 404
    assert before_start.status_code == 422
    assert future_end.status_code == 422
    assert ended.status_code == 200
    assert ended.json()["data"]["status"] == "ENDED"
    assert ended.json()["data"]["endedOn"] == date.today().isoformat()
    assert repeated_end.status_code == 409
