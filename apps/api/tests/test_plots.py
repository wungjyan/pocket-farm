import asyncio
from collections.abc import Mapping
from datetime import date, timedelta
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
        json={"name": "管理员创建地块", "type": "GREENHOUSE", "areaValue": 1, "areaUnit": "MU"},
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
        json={"name": "私有地块", "type": "FIELD", "areaValue": 1, "areaUnit": "MU"},
    )
    assert create_response.status_code == 201
    plot_id = create_response.json()["data"]["id"]

    list_response = call(outsider_token, f"/api/v1/farms/{farm['id']}/plots")
    summary_response = call(outsider_token, f"/api/v1/farms/{farm['id']}/plot-summaries")
    filter_options_response = call(
        outsider_token,
        f"/api/v1/farms/{farm['id']}/plot-filter-options",
    )
    detail_response = call(outsider_token, f"/api/v1/plots/{plot_id}")
    assert list_response.status_code == 404
    assert summary_response.status_code == 404
    assert filter_options_response.status_code == 404
    assert detail_response.status_code == 404


def test_plot_summaries_include_active_species_and_filter_in_the_database() -> None:
    owner_token = login(OWNER_PHONE)
    farm = create_farm(owner_token)
    plots = []
    for name in ("种养地块", "生菜地块", "空闲地块"):
        response = call(
            owner_token,
            f"/api/v1/farms/{farm['id']}/plots",
            method="post",
            json={"name": name, "type": "FIELD", "areaValue": 1, "areaUnit": "MU"},
        )
        assert response.status_code == 201
        plots.append(response.json()["data"])

    cucumber = species_by_name(owner_token, "黄瓜")
    lettuce = species_by_name(owner_token, "生菜")
    start_agriculture_production(owner_token, plots[0]["id"], cucumber["id"])
    start_agriculture_production(owner_token, plots[0]["id"], cucumber["id"])
    start_agriculture_production(owner_token, plots[0]["id"], lettuce["id"])
    start_agriculture_production(owner_token, plots[1]["id"], lettuce["id"])

    summary_response = call(
        owner_token,
        f"/api/v1/farms/{farm['id']}/plot-summaries?page=1&pageSize=100&filter=ALL",
    )
    assert summary_response.status_code == 200
    summary_page = summary_response.json()["data"]
    assert summary_page["total"] == 3
    active_species_by_plot = {
        item["name"]: {species["name"] for species in item["activeSpecies"]}
        for item in summary_page["items"]
    }
    assert active_species_by_plot["种养地块"] == {"黄瓜", "生菜"}
    assert active_species_by_plot["生菜地块"] == {"生菜"}
    assert active_species_by_plot["空闲地块"] == set()

    filter_options_response = call(
        owner_token,
        f"/api/v1/farms/{farm['id']}/plot-filter-options",
    )
    assert filter_options_response.status_code == 200
    filter_options = filter_options_response.json()["data"]
    assert {item["name"] for item in filter_options["activeSpecies"]} == {"黄瓜", "生菜"}
    assert filter_options["idlePlotCount"] == 1

    species_response = call(
        owner_token,
        f"/api/v1/farms/{farm['id']}/plot-summaries?filter=SPECIES&speciesId={lettuce['id']}",
    )
    assert species_response.status_code == 200
    assert species_response.json()["data"]["total"] == 2
    assert {item["name"] for item in species_response.json()["data"]["items"]} == {
        "种养地块",
        "生菜地块",
    }

    idle_response = call(owner_token, f"/api/v1/farms/{farm['id']}/plot-summaries?filter=IDLE")
    assert idle_response.status_code == 200
    assert [item["name"] for item in idle_response.json()["data"]["items"]] == ["空闲地块"]

    paged_response = call(
        owner_token,
        f"/api/v1/farms/{farm['id']}/plot-summaries?page=2&pageSize=1",
    )
    assert paged_response.status_code == 200
    assert paged_response.json()["data"]["page"] == 2
    assert paged_response.json()["data"]["pageSize"] == 1
    assert paged_response.json()["data"]["total"] == 3
    assert len(paged_response.json()["data"]["items"]) == 1

    missing_species_response = call(
        owner_token,
        f"/api/v1/farms/{farm['id']}/plot-summaries?filter=SPECIES",
    )
    assert missing_species_response.status_code == 422


def test_plot_area_and_boundary_validation() -> None:
    owner_token = login(OWNER_PHONE)
    farm = create_farm(owner_token)
    missing_type = call(
        owner_token,
        f"/api/v1/farms/{farm['id']}/plots",
        method="post",
        json={"name": "缺少类型", "areaValue": 2, "areaUnit": "MU"},
    )
    missing_area = call(
        owner_token,
        f"/api/v1/farms/{farm['id']}/plots",
        method="post",
        json={"name": "缺少面积", "type": "FIELD", "areaUnit": "MU"},
    )
    missing_unit = call(
        owner_token,
        f"/api/v1/farms/{farm['id']}/plots",
        method="post",
        json={"name": "缺少单位", "type": "FIELD", "areaValue": 2},
    )
    invalid_boundary = call(
        owner_token,
        f"/api/v1/farms/{farm['id']}/plots",
        method="post",
        json={
            "name": "坐标系错误",
            "type": "FIELD",
            "areaValue": 2,
            "areaUnit": "MU",
            "boundary": {"coordinateSystem": "WGS84"},
        },
    )
    assert missing_type.status_code == 422
    assert missing_area.status_code == 422
    assert missing_unit.status_code == 422
    assert invalid_boundary.status_code == 422


def test_plot_detail_aggregates_productions_operations_and_harvests() -> None:
    owner_token = login(OWNER_PHONE)
    outsider_token = login(OUTSIDER_PHONE)
    farm = create_farm(owner_token)
    create_response = call(
        owner_token,
        f"/api/v1/farms/{farm['id']}/plots",
        method="post",
        json={"name": "聚合详情地块", "type": "GREENHOUSE", "areaValue": 1, "areaUnit": "MU"},
    )
    assert create_response.status_code == 201
    plot = create_response.json()["data"]
    cucumber = species_by_name(owner_token, "黄瓜")
    ended_production = start_agriculture_production(owner_token, plot["id"], cucumber["id"])

    operation_types = call(owner_token, "/api/v1/operation-types?pageSize=100")
    assert operation_types.status_code == 200
    plow_id = next(
        item["id"] for item in operation_types.json()["data"]["items"] if item["code"] == "PLOW"
    )
    operation_response = call(
        owner_token,
        f"/api/v1/plots/{plot['id']}/operations",
        method="post",
        json={"operationTypeId": plow_id, "productionId": ended_production["id"]},
    )
    harvest_response = call(
        owner_token,
        f"/api/v1/productions/{ended_production['id']}/harvests",
        method="post",
        json={"quantity": 12.5},
    )
    assert operation_response.status_code == 201
    assert harvest_response.status_code == 201

    end_response = call(
        owner_token,
        f"/api/v1/productions/{ended_production['id']}/end",
        method="post",
        json={},
    )
    assert end_response.status_code == 200
    active_production = start_agriculture_production(owner_token, plot["id"], cucumber["id"])

    detail_response = call(owner_token, f"/api/v1/plots/{plot['id']}/detail")
    outsider_response = call(outsider_token, f"/api/v1/plots/{plot['id']}/detail")

    assert detail_response.status_code == 200
    detail = detail_response.json()["data"]
    assert detail["plot"]["id"] == plot["id"]
    assert [item["id"] for item in detail["activeProductions"]] == [active_production["id"]]
    assert [item["id"] for item in detail["endedProductions"]] == [ended_production["id"]]
    assert detail["operationTotal"] == 1
    assert detail["operations"][0]["id"] == operation_response.json()["data"]["id"]
    assert detail["harvestTotal"] == 1
    assert detail["harvests"][0]["id"] == harvest_response.json()["data"]["id"]
    assert outsider_response.status_code == 404
