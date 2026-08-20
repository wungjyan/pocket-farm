import asyncio
from collections.abc import Mapping
from datetime import date, timedelta
from typing import Any

import httpx

from app.db.session import engine
from app.main import app

OWNER_PHONE = "13800000001"


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


def login() -> str:
    response = asyncio.run(
        request_api(
            "/api/v1/auth/login",
            method="post",
            json={"phoneNumber": OWNER_PHONE, "verificationCode": "8888"},
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


def create_farm(token: str, name: str) -> dict[str, Any]:
    response = call(token, "/api/v1/farms", method="post", json={"name": name})
    assert response.status_code == 201
    return response.json()["data"]


def create_plot(
    token: str,
    farm_id: int,
    name: str,
    plot_type: str,
) -> dict[str, Any]:
    response = call(
        token,
        f"/api/v1/farms/{farm_id}/plots",
        method="post",
        json={"name": name, "type": plot_type},
    )
    assert response.status_code == 201
    return response.json()["data"]


def species_id(token: str, name: str) -> int:
    response = call(token, f"/api/v1/species?keyword={name}&pageSize=100")
    assert response.status_code == 200
    return next(item["id"] for item in response.json()["data"]["items"] if item["name"] == name)


def operation_type_ids(token: str) -> dict[str, int]:
    response = call(token, "/api/v1/operation-types?pageSize=100")
    assert response.status_code == 200
    return {item["code"]: item["id"] for item in response.json()["data"]["items"]}


def start_production(
    token: str,
    plot_id: int,
    species: int,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    response = call(
        token,
        f"/api/v1/plots/{plot_id}/productions",
        method="post",
        json={
            "speciesId": species,
            "startedOn": (date.today() - timedelta(days=1)).isoformat(),
            **payload,
        },
    )
    assert response.status_code == 201, response.json()
    return response.json()["data"]


def record_operation(
    token: str,
    plot_id: int,
    operation_type_id: int,
    production_id: int | None,
) -> dict[str, Any]:
    response = call(
        token,
        f"/api/v1/plots/{plot_id}/operations",
        method="post",
        json={"operationTypeId": operation_type_id, "productionId": production_id},
    )
    assert response.status_code == 201, response.json()
    return response.json()["data"]


def record_harvest(token: str, production_id: int, quantity: int | float) -> dict[str, Any]:
    response = call(
        token,
        f"/api/v1/productions/{production_id}/harvests",
        method="post",
        json={"quantity": quantity},
    )
    assert response.status_code == 201, response.json()
    return response.json()["data"]


def end_production(token: str, production_id: int) -> dict[str, Any]:
    response = call(token, f"/api/v1/productions/{production_id}/end", method="post", json={})
    assert response.status_code == 200, response.json()
    return response.json()["data"]


def plot_detail(token: str, plot_id: int) -> dict[str, Any]:
    response = call(token, f"/api/v1/plots/{plot_id}/detail")
    assert response.status_code == 200, response.json()
    return response.json()["data"]


def test_agriculture_complete_workflow() -> None:
    token = login()
    farm = create_farm(token, "农业联调农场")
    plot = create_plot(token, farm["id"], "1号大棚", "GREENHOUSE")
    cucumber = species_id(token, "黄瓜")
    operation_types = operation_type_ids(token)
    production = start_production(
        token,
        plot["id"],
        cucumber,
        {
            "plantingStandard": "NORMAL",
            "plantingMethod": "TRANSPLANT",
            "workMethod": "MANUAL",
        },
    )

    record_operation(token, plot["id"], operation_types["FERTILIZE"], production["id"])
    record_operation(token, plot["id"], operation_types["IRRIGATE"], production["id"])
    first_harvest = record_harvest(token, production["id"], 100)
    second_harvest = record_harvest(token, production["id"], 80)
    ended = end_production(token, production["id"])
    detail = plot_detail(token, plot["id"])

    assert ended["status"] == "ENDED"
    assert detail["activeProductions"] == []
    assert [item["id"] for item in detail["endedProductions"]] == [production["id"]]
    assert detail["operationTotal"] == 2
    assert detail["harvestTotal"] == 2
    assert {item["id"] for item in detail["harvests"]} == {
        first_harvest["id"],
        second_harvest["id"],
    }


def test_fishery_complete_workflow() -> None:
    token = login()
    farm = create_farm(token, "渔业联调农场")
    plot = create_plot(token, farm["id"], "东鱼塘", "POND")
    grass_carp = species_id(token, "青鱼")
    operation_types = operation_type_ids(token)
    production = start_production(
        token,
        plot["id"],
        grass_carp,
        {"initialQuantity": 300, "workMethod": "MANUAL"},
    )

    record_operation(token, plot["id"], operation_types["CHANGE_WATER"], production["id"])
    record_operation(token, plot["id"], operation_types["FEED_FISH"], production["id"])
    record_harvest(token, production["id"], 42.5)
    record_harvest(token, production["id"], 36)
    end_production(token, production["id"])
    detail = plot_detail(token, plot["id"])

    assert detail["endedProductions"][0]["id"] == production["id"]
    assert detail["operationTotal"] == 2
    assert detail["harvestTotal"] == 2
    assert {item["unit"] for item in detail["harvests"]} == {"KG"}


def test_livestock_complete_workflow() -> None:
    token = login()
    farm = create_farm(token, "牧业联调农场")
    plot = create_plot(token, farm["id"], "1号栏舍", "BARN")
    pig = species_id(token, "猪")
    operation_types = operation_type_ids(token)
    production = start_production(
        token,
        plot["id"],
        pig,
        {"initialQuantity": 20, "entryAgeDays": 30},
    )

    record_operation(token, plot["id"], operation_types["FEED"], production["id"])
    record_operation(token, plot["id"], operation_types["DISINFECT"], production["id"])
    harvest = record_harvest(token, production["id"], 12)
    end_production(token, production["id"])
    detail = plot_detail(token, plot["id"])

    assert detail["endedProductions"][0]["id"] == production["id"]
    assert detail["operationTotal"] == 2
    assert detail["harvestTotal"] == 1
    assert detail["harvests"][0]["id"] == harvest["id"]
    assert detail["harvests"][0]["unit"] == "HEAD"


def test_empty_plot_accepts_plot_level_operation() -> None:
    token = login()
    farm = create_farm(token, "空闲地块联调农场")
    plot = create_plot(token, farm["id"], "空闲大田", "FIELD")
    plow = operation_type_ids(token)["PLOW"]

    operation = record_operation(token, plot["id"], plow, None)
    detail = plot_detail(token, plot["id"])

    assert operation["productionId"] is None
    assert detail["activeProductions"] == []
    assert detail["endedProductions"] == []
    assert detail["operationTotal"] == 1
    assert detail["operations"][0]["productionId"] is None
    assert detail["harvestTotal"] == 0


def test_multiple_rounds_keep_production_records_independent() -> None:
    token = login()
    farm = create_farm(token, "多轮种植联调农场")
    plot = create_plot(token, farm["id"], "1号大棚", "GREENHOUSE")
    cucumber = species_id(token, "黄瓜")
    operation_types = operation_type_ids(token)
    first = start_production(
        token,
        plot["id"],
        cucumber,
        {
            "plantingStandard": "NORMAL",
            "plantingMethod": "TRANSPLANT",
            "workMethod": "MANUAL",
        },
    )
    record_operation(token, plot["id"], operation_types["FERTILIZE"], first["id"])
    first_harvest = record_harvest(token, first["id"], 100)
    end_production(token, first["id"])
    second = start_production(
        token,
        plot["id"],
        cucumber,
        {
            "plantingStandard": "NORMAL",
            "plantingMethod": "TRANSPLANT",
            "workMethod": "MANUAL",
        },
    )
    second_operation = record_operation(
        token,
        plot["id"],
        operation_types["IRRIGATE"],
        second["id"],
    )
    detail = plot_detail(token, plot["id"])

    assert [item["id"] for item in detail["activeProductions"]] == [second["id"]]
    assert [item["id"] for item in detail["endedProductions"]] == [first["id"]]
    assert detail["harvestTotal"] == 1
    assert detail["harvests"][0]["productionId"] == first["id"]
    assert {item["productionId"] for item in detail["operations"]} == {
        first["id"],
        second_operation["productionId"],
    }
    assert first_harvest["productionId"] != second["id"]


def test_multiple_active_productions_support_each_choice_and_plot_level_operation() -> None:
    token = login()
    farm = create_farm(token, "同时多种联调农场")
    plot = create_plot(token, farm["id"], "综合大棚", "GREENHOUSE")
    cucumber = species_id(token, "黄瓜")
    lettuce = species_id(token, "生菜")
    operation_types = operation_type_ids(token)
    agriculture_payload = {
        "plantingStandard": "NORMAL",
        "plantingMethod": "TRANSPLANT",
        "workMethod": "MANUAL",
    }
    cucumber_production = start_production(token, plot["id"], cucumber, agriculture_payload)
    lettuce_production = start_production(token, plot["id"], lettuce, agriculture_payload)

    cucumber_operation = record_operation(
        token,
        plot["id"],
        operation_types["FERTILIZE"],
        cucumber_production["id"],
    )
    lettuce_operation = record_operation(
        token,
        plot["id"],
        operation_types["IRRIGATE"],
        lettuce_production["id"],
    )
    plot_operation = record_operation(token, plot["id"], operation_types["WEED"], None)
    detail = plot_detail(token, plot["id"])

    assert {item["id"] for item in detail["activeProductions"]} == {
        cucumber_production["id"],
        lettuce_production["id"],
    }
    assert detail["operationTotal"] == 3
    assert {item["productionId"] for item in detail["operations"]} == {
        cucumber_operation["productionId"],
        lettuce_operation["productionId"],
        plot_operation["productionId"],
    }
