import asyncio
from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
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
        json={"name": name, "type": plot_type, "areaValue": 1, "areaUnit": "MU"},
    )
    assert response.status_code == 201
    return response.json()["data"]


def species_id(token: str, name: str) -> int:
    response = call(token, f"/api/v1/species?keyword={name}&pageSize=100")
    assert response.status_code == 200
    return next(item["id"] for item in response.json()["data"]["items"] if item["name"] == name)


def start_cucumber_production(token: str, plot_id: int) -> dict[str, Any]:
    response = call(
        token,
        f"/api/v1/plots/{plot_id}/productions",
        method="post",
        json={
            "speciesId": species_id(token, "黄瓜"),
            "startedOn": datetime.now(timezone.utc).date().isoformat(),
            "plantingStandard": "NORMAL",
            "plantingMethod": "TRANSPLANT",
            "workMethod": "MANUAL",
        },
    )
    assert response.status_code == 201, response.json()
    return response.json()["data"]


def operation_type_ids(token: str) -> dict[str, int]:
    response = call(token, "/api/v1/operation-types?pageSize=100")
    assert response.status_code == 200
    return {item["name"]: item["id"] for item in response.json()["data"]["items"]}


def create_operation(
    token: str,
    plot_id: int,
    operation_type_id: int,
    hours_ago: int,
    production_id: int | None = None,
) -> dict[str, Any]:
    payload = {
        "productionId": production_id,
        "operationTypeId": operation_type_id,
        "workMethod": "MANUAL",
        "operatedAt": (datetime.now(timezone.utc) - timedelta(hours=hours_ago)).isoformat(),
    }
    response = call(token, f"/api/v1/plots/{plot_id}/operations", method="post", json=payload)
    assert response.status_code == 201, response.json()
    return response.json()["data"]


def setup_farm() -> tuple[str, int, dict[str, int]]:
    """创建农场并准备农事数据。

    返回 (owner_token, farm_id, operation_type_ids)。数据顺序：
    - 1号大棚：黄瓜种养（进行中）
    - 施肥（8 小时前，关联黄瓜种养）
    - 灌溉（2 小时前，整个地块）
    - 东鱼塘：清塘（5 小时前，无种养）
    """
    token = login(OWNER_PHONE)
    farm = create_farm(token, "农场农事记录测试")
    greenhouse = create_plot(token, farm["id"], "1号大棚", "GREENHOUSE")
    pond = create_plot(token, farm["id"], "东鱼塘", "POND")
    production = start_cucumber_production(token, greenhouse["id"])
    type_ids = operation_type_ids(token)

    create_operation(token, greenhouse["id"], type_ids["施肥"], 8, production["id"])
    create_operation(token, greenhouse["id"], type_ids["灌溉"], 2)
    create_operation(token, pond["id"], type_ids["清塘"], 5)
    return token, farm["id"], type_ids


def test_farm_operations_requires_farm_membership() -> None:
    owner_token, farm_id, _ = setup_farm()
    outsider_token = login(OUTSIDER_PHONE)

    operations = call(outsider_token, f"/api/v1/farms/{farm_id}/operations")
    options = call(outsider_token, f"/api/v1/farms/{farm_id}/operation-filter-options")

    assert operations.status_code == 404
    assert operations.json()["error"]["code"] == "NOT_FOUND"
    assert options.status_code == 404
    assert owner_token


def test_farm_operations_list_order_and_species() -> None:
    token, farm_id, type_ids = setup_farm()

    response = call(token, f"/api/v1/farms/{farm_id}/operations?pageSize=100")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] == 3
    # 按操作时间倒序。
    items = data["items"]
    assert [item["operationTypeId"] for item in items] == [
        type_ids["灌溉"],
        type_ids["清塘"],
        type_ids["施肥"],
    ]
    assert items[0]["operationTypeName"] == "灌溉"
    assert items[0]["plotName"] == "1号大棚"
    assert float(items[0]["plotAreaValue"]) == 1
    assert items[0]["plotAreaUnit"] == "MU"
    assert items[0]["speciesName"] is None
    assert items[1]["plotName"] == "东鱼塘"
    assert items[1]["speciesName"] is None
    # 关联种养的农事带回作物名称。
    assert items[2]["speciesName"] == "黄瓜"
    assert items[2]["productionId"] is not None


def test_farm_operations_type_filter() -> None:
    token, farm_id, type_ids = setup_farm()

    response = call(
        token,
        f"/api/v1/farms/{farm_id}/operations?operationTypeId={type_ids['灌溉']}&pageSize=100",
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] == 1
    assert data["items"][0]["operationTypeName"] == "灌溉"

    unused = call(
        token,
        f"/api/v1/farms/{farm_id}/operations?operationTypeId={type_ids['翻耕']}&pageSize=100",
    )
    assert unused.status_code == 200
    assert unused.json()["data"]["total"] == 0

    invalid = call(token, f"/api/v1/farms/{farm_id}/operations?operationTypeId=0")
    assert invalid.status_code == 422


def test_farm_operation_filter_options() -> None:
    owner_token, farm_id, _ = setup_farm()

    response = call(owner_token, f"/api/v1/farms/{farm_id}/operation-filter-options")

    assert response.status_code == 200
    # 只反查当前农场实际进行过的农事类型。
    names = {item["name"] for item in response.json()["data"]["types"]}
    assert names == {"施肥", "灌溉", "清塘"}
    assert "翻耕" not in names

    # 其他农场使用过的类型不出现在选项中。
    outsider_token = login(OUTSIDER_PHONE)
    other_farm = create_farm(outsider_token, "其他农事农场")
    other_plot = create_plot(outsider_token, other_farm["id"], "其他大棚", "GREENHOUSE")
    type_ids = operation_type_ids(outsider_token)
    create_operation(outsider_token, other_plot["id"], type_ids["除草"], 1)

    owner_view = call(owner_token, f"/api/v1/farms/{farm_id}/operation-filter-options")
    assert owner_view.status_code == 200
    owner_names = {item["name"] for item in owner_view.json()["data"]["types"]}
    assert "除草" not in owner_names

    outsider_view = call(
        outsider_token,
        f"/api/v1/farms/{other_farm['id']}/operation-filter-options",
    )
    assert outsider_view.status_code == 200
    assert {item["name"] for item in outsider_view.json()["data"]["types"]} == {"除草"}
