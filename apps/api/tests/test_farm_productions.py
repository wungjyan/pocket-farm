import asyncio
from collections.abc import Mapping
from datetime import date, timedelta
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


def start_production(
    token: str,
    plot_id: int,
    species: int,
    industry: str,
    days_ago: int,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "speciesId": species,
        "startedOn": (date.today() - timedelta(days=days_ago)).isoformat(),
    }
    if industry in {"AGRICULTURE", "FORESTRY"}:
        payload.update(
            {
                "plantingStandard": "NORMAL",
                "plantingMethod": "TRANSPLANT",
                "workMethod": "MANUAL",
            }
        )
    elif industry == "FISHERY":
        payload.update({"initialQuantity": "120", "workMethod": "MANUAL"})
    response = call(
        token,
        f"/api/v1/plots/{plot_id}/productions",
        method="post",
        json=payload,
    )
    assert response.status_code == 201, response.json()
    return response.json()["data"]


def end_production(token: str, production_id: int) -> None:
    response = call(
        token,
        f"/api/v1/productions/{production_id}/end",
        method="post",
        json={"endedOn": date.today().isoformat()},
    )
    assert response.status_code == 200


def setup_farm() -> tuple[str, int]:
    """创建农场并准备跨地块、跨行业、跨状态的种养数据。

    返回 (owner_token, farm_id)。数据顺序：
    - 黄瓜（农业）1 号大棚，5 天前开始，已结束
    - 生菜（农业）东鱼塘，3 天前开始，进行中
    - 青鱼（渔业）东鱼塘，2 天前开始，进行中
    - 黄瓜（农业）1 号大棚，1 天前开始，进行中
    """
    token = login(OWNER_PHONE)
    farm = create_farm(token, "农场种养记录测试")
    greenhouse = create_plot(token, farm["id"], "1号大棚", "GREENHOUSE")
    pond = create_plot(token, farm["id"], "东鱼塘", "POND")
    cucumber = species_id(token, "黄瓜")
    lettuce = species_id(token, "生菜")
    black_carp = species_id(token, "青鱼")

    ended_cucumber = start_production(token, greenhouse["id"], cucumber, "AGRICULTURE", 5)
    start_production(token, pond["id"], lettuce, "AGRICULTURE", 3)
    start_production(token, pond["id"], black_carp, "FISHERY", 2)
    start_production(token, greenhouse["id"], cucumber, "AGRICULTURE", 1)
    end_production(token, ended_cucumber["id"])
    return token, farm["id"]


def setup_species_farm() -> tuple[str, int, dict[str, int]]:
    """创建农场并准备跨种类的种养数据。

    返回 (owner_token, farm_id, species_ids)。数据顺序：
    - 黄瓜（农业）1 号大棚，5 天前开始，已结束（黄瓜仅存在于已结束状态）
    - 生菜（农业）1 号大棚，3 天前开始，进行中
    - 青鱼（渔业）东鱼塘，2 天前开始，进行中
    - 大豆（农业）东鱼塘，1 天前开始，进行中
    """
    token = login(OWNER_PHONE)
    farm = create_farm(token, "农场种类筛选测试")
    greenhouse = create_plot(token, farm["id"], "1号大棚", "GREENHOUSE")
    pond = create_plot(token, farm["id"], "东鱼塘", "POND")
    cucumber = species_id(token, "黄瓜")
    lettuce = species_id(token, "生菜")
    black_carp = species_id(token, "青鱼")
    soybean = species_id(token, "大豆")

    ended_cucumber = start_production(token, greenhouse["id"], cucumber, "AGRICULTURE", 5)
    start_production(token, greenhouse["id"], lettuce, "AGRICULTURE", 3)
    start_production(token, pond["id"], black_carp, "FISHERY", 2)
    start_production(token, pond["id"], soybean, "AGRICULTURE", 1)
    end_production(token, ended_cucumber["id"])
    return (
        token,
        farm["id"],
        {
            "黄瓜": cucumber,
            "生菜": lettuce,
            "青鱼": black_carp,
            "大豆": soybean,
        },
    )


def test_farm_productions_requires_farm_membership() -> None:
    owner_token, farm_id = setup_farm()
    outsider_token = login(OUTSIDER_PHONE)

    response = call(outsider_token, f"/api/v1/farms/{farm_id}/productions")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"
    assert owner_token


def test_farm_productions_default_lists_all_with_active_first() -> None:
    token, farm_id = setup_farm()

    response = call(token, f"/api/v1/farms/{farm_id}/productions?pageSize=100")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] == 4
    items = data["items"]
    # ACTIVE 优先，同状态按 startedOn 倒序；已结束的排在最后。
    assert [(item["speciesName"], item["status"]) for item in items] == [
        ("黄瓜", "ACTIVE"),
        ("青鱼", "ACTIVE"),
        ("生菜", "ACTIVE"),
        ("黄瓜", "ENDED"),
    ]
    first = items[0]
    assert first["plotName"] == "1号大棚"
    assert float(first["plotAreaValue"]) == 1
    assert first["plotAreaUnit"] == "MU"
    assert first["industry"] == "AGRICULTURE"
    assert first["individualUnit"] == "PLANT"
    fish = items[1]
    assert fish["plotName"] == "东鱼塘"
    assert fish["industry"] == "FISHERY"
    assert fish["individualUnit"] == "TAIL"
    assert float(fish["initialQuantity"]) == 120


def test_farm_productions_status_filter() -> None:
    token, farm_id = setup_farm()

    active_response = call(token, f"/api/v1/farms/{farm_id}/productions?status=ACTIVE&pageSize=100")
    ended_response = call(token, f"/api/v1/farms/{farm_id}/productions?status=ENDED&pageSize=100")

    assert active_response.status_code == 200
    active_data = active_response.json()["data"]
    assert active_data["total"] == 3
    assert all(item["status"] == "ACTIVE" for item in active_data["items"])
    assert [item["startedOn"] for item in active_data["items"]] == sorted(
        (item["startedOn"] for item in active_data["items"]),
        reverse=True,
    )

    assert ended_response.status_code == 200
    ended_data = ended_response.json()["data"]
    assert ended_data["total"] == 1
    assert ended_data["items"][0]["status"] == "ENDED"
    assert ended_data["items"][0]["endedOn"] == date.today().isoformat()


def test_farm_productions_industry_filter() -> None:
    token, farm_id = setup_farm()

    fishery_response = call(
        token,
        f"/api/v1/farms/{farm_id}/productions?industry=FISHERY&pageSize=100",
    )
    agriculture_response = call(
        token,
        f"/api/v1/farms/{farm_id}/productions?industry=AGRICULTURE&pageSize=100",
    )

    assert fishery_response.status_code == 200
    fishery_data = fishery_response.json()["data"]
    assert fishery_data["total"] == 1
    assert fishery_data["items"][0]["speciesName"] == "青鱼"

    assert agriculture_response.status_code == 200
    agriculture_data = agriculture_response.json()["data"]
    assert agriculture_data["total"] == 3
    assert [item["status"] for item in agriculture_data["items"]] == [
        "ACTIVE",
        "ACTIVE",
        "ENDED",
    ]


def test_farm_productions_combined_filters() -> None:
    token, farm_id = setup_farm()

    response = call(
        token,
        f"/api/v1/farms/{farm_id}/productions?industry=AGRICULTURE&status=ACTIVE&pageSize=100",
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] == 2
    assert [(item["speciesName"], item["plotName"]) for item in data["items"]] == [
        ("黄瓜", "1号大棚"),
        ("生菜", "东鱼塘"),
    ]


def test_farm_productions_pagination() -> None:
    token, farm_id = setup_farm()

    first_page = call(token, f"/api/v1/farms/{farm_id}/productions?page=1&pageSize=2")
    second_page = call(token, f"/api/v1/farms/{farm_id}/productions?page=2&pageSize=2")

    assert first_page.status_code == 200
    first_data = first_page.json()["data"]
    assert first_data["total"] == 4
    assert len(first_data["items"]) == 2
    assert second_page.status_code == 200
    second_data = second_page.json()["data"]
    assert len(second_data["items"]) == 2
    first_page_ids = {item["id"] for item in first_data["items"]}
    second_page_ids = {item["id"] for item in second_data["items"]}
    assert first_page_ids.isdisjoint(second_page_ids)


def test_farm_productions_rejects_invalid_industry() -> None:
    token, farm_id = setup_farm()

    response = call(token, f"/api/v1/farms/{farm_id}/productions?industry=INVALID")

    assert response.status_code == 422


def test_farm_productions_species_filter() -> None:
    token, farm_id, species_ids = setup_species_farm()

    response = call(
        token,
        f"/api/v1/farms/{farm_id}/productions?speciesId={species_ids['黄瓜']}&pageSize=100",
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] == 1
    assert data["items"][0]["speciesId"] == species_ids["黄瓜"]
    assert data["items"][0]["status"] == "ENDED"

    combined = call(
        token,
        f"/api/v1/farms/{farm_id}/productions"
        f"?speciesId={species_ids['生菜']}&status=ACTIVE&pageSize=100",
    )
    assert combined.status_code == 200
    combined_data = combined.json()["data"]
    assert combined_data["total"] == 1
    assert combined_data["items"][0]["speciesName"] == "生菜"

    missing = call(
        token,
        f"/api/v1/farms/{farm_id}/productions"
        f"?speciesId={species_ids['黄瓜']}&status=ACTIVE&pageSize=100",
    )
    assert missing.status_code == 200
    assert missing.json()["data"]["total"] == 0

    invalid = call(token, f"/api/v1/farms/{farm_id}/productions?speciesId=0")
    assert invalid.status_code == 422


def test_farm_production_filter_options_species() -> None:
    owner_token, farm_id, species_ids = setup_species_farm()

    response = call(owner_token, f"/api/v1/farms/{farm_id}/production-filter-options")

    assert response.status_code == 200
    # 当前农场种植过的种类（含已结束），去重并按名称排序。
    assert response.json()["data"]["species"] == [
        {"id": species_ids["大豆"], "name": "大豆"},
        {"id": species_ids["生菜"], "name": "生菜"},
        {"id": species_ids["青鱼"], "name": "青鱼"},
        {"id": species_ids["黄瓜"], "name": "黄瓜"},
    ]

    # 行业筛选联动：品种选项只保留对应行业下种植过的种类。
    fishery = call(
        owner_token,
        f"/api/v1/farms/{farm_id}/production-filter-options?industry=FISHERY",
    )
    assert fishery.status_code == 200
    assert fishery.json()["data"]["species"] == [{"id": species_ids["青鱼"], "name": "青鱼"}]

    agriculture = call(
        owner_token,
        f"/api/v1/farms/{farm_id}/production-filter-options?industry=AGRICULTURE",
    )
    assert agriculture.status_code == 200
    assert [item["name"] for item in agriculture.json()["data"]["species"]] == [
        "大豆",
        "生菜",
        "黄瓜",
    ]

    outsider_token = login(OUTSIDER_PHONE)
    denied = call(outsider_token, f"/api/v1/farms/{farm_id}/production-filter-options")
    assert denied.status_code == 404
    assert denied.json()["error"]["code"] == "NOT_FOUND"


def test_farm_production_filter_options_excludes_other_farms() -> None:
    owner_token, farm_id, _ = setup_species_farm()
    outsider_token = login(OUTSIDER_PHONE)
    other_farm = create_farm(outsider_token, "其他种类农场")
    other_plot = create_plot(outsider_token, other_farm["id"], "其他大棚", "GREENHOUSE")
    rice = species_id(outsider_token, "水稻")
    start_production(outsider_token, other_plot["id"], rice, "AGRICULTURE", 1)

    response = call(owner_token, f"/api/v1/farms/{farm_id}/production-filter-options")

    assert response.status_code == 200
    listed_ids = {item["id"] for item in response.json()["data"]["species"]}
    assert rice not in listed_ids
