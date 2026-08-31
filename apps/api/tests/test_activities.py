import asyncio
from collections.abc import Mapping
from datetime import UTC, date, datetime, timedelta
from typing import Any

import httpx

from app.db.session import engine
from app.main import app

OWNER_PHONE = "13800000001"
OUTSIDER_PHONE = "13800000004"


async def request_api(
    path: str,
    *,
    method: str = "get",
    json: Mapping[str, Any] | None = None,
    headers: Mapping[str, Any] | None = None,
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
    response = call(token, "/api/v1/farms", method="post", json={"name": "动态测试农场"})
    assert response.status_code == 201
    return response.json()["data"]


def create_plot(token: str, farm_id: int) -> dict[str, Any]:
    response = call(
        token,
        f"/api/v1/farms/{farm_id}/plots",
        method="post",
        json={"name": "1号大棚", "type": "GREENHOUSE", "areaValue": 2, "areaUnit": "MU"},
    )
    assert response.status_code == 201
    return response.json()["data"]


def species_id(token: str, name: str) -> int:
    response = call(token, f"/api/v1/species?keyword={name}&pageSize=100")
    assert response.status_code == 200
    return next(item["id"] for item in response.json()["data"]["items"] if item["name"] == name)


def test_farm_activities_use_record_creation_time_and_include_lifecycle_events() -> None:
    token = login(OWNER_PHONE)
    farm = create_farm(token)
    plot = create_plot(token, farm["id"])
    cucumber_id = species_id(token, "黄瓜")
    production_response = call(
        token,
        f"/api/v1/plots/{plot['id']}/productions",
        method="post",
        json={
            "speciesId": cucumber_id,
            "startedOn": (date.today() - timedelta(days=3)).isoformat(),
            "plantingStandard": "NORMAL",
            "plantingMethod": "TRANSPLANT",
            "workMethod": "MANUAL",
        },
    )
    assert production_response.status_code == 201
    production = production_response.json()["data"]

    operation_types = call(token, "/api/v1/operation-types?pageSize=100")
    fertilize_id = next(
        item["id"] for item in operation_types.json()["data"]["items"] if item["name"] == "施肥"
    )
    operation_response = call(
        token,
        f"/api/v1/plots/{plot['id']}/operations",
        method="post",
        json={
            "productionId": production["id"],
            "operationTypeId": fertilize_id,
            "operatedAt": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
        },
    )
    assert operation_response.status_code == 201
    operation = operation_response.json()["data"]

    harvest_response = call(
        token,
        f"/api/v1/productions/{production['id']}/harvests",
        method="post",
        json={"quantity": 12},
    )
    assert harvest_response.status_code == 201
    harvest = harvest_response.json()["data"]

    end_response = call(
        token,
        f"/api/v1/productions/{production['id']}/end",
        method="post",
        json={"endedOn": date.today().isoformat()},
    )
    assert end_response.status_code == 200
    ended = end_response.json()["data"]
    assert ended["endedAt"] is not None

    response = call(token, f"/api/v1/farms/{farm['id']}/activities?limit=5")
    assert response.status_code == 200
    items = response.json()["data"]["items"]
    assert {item["type"] for item in items} == {
        "PRODUCTION_STARTED",
        "PRODUCTION_ENDED",
        "OPERATION_CREATED",
        "HARVEST_CREATED",
    }
    operation_item = next(item for item in items if item["type"] == "OPERATION_CREATED")
    harvest_item = next(item for item in items if item["type"] == "HARVEST_CREATED")
    ended_item = next(item for item in items if item["type"] == "PRODUCTION_ENDED")
    assert operation_item["occurredAt"] != operation["operatedAt"]
    assert operation_item["operationId"] == operation["id"]
    assert operation_item["plotName"] == "1号大棚"
    assert operation_item["plotAreaUnit"] == "MU"
    assert harvest_item["harvestId"] == harvest["id"]
    assert float(harvest_item["quantity"]) == 12
    assert ended_item["productionId"] == production["id"]
    assert ended_item["occurredAt"].startswith(ended["endedAt"][:19])

    limited = call(token, f"/api/v1/farms/{farm['id']}/activities?limit=2")
    assert limited.status_code == 200
    assert len(limited.json()["data"]["items"]) == 2

    outsider_token = login(OUTSIDER_PHONE)
    unauthorized = call(outsider_token, f"/api/v1/farms/{farm['id']}/activities")
    assert unauthorized.status_code == 404
