import asyncio
from collections.abc import Mapping
from typing import Any

import httpx
import pytest
from pydantic import SecretStr

from app.api.v1.endpoints.ai import get_ai_client
from app.core.config import settings
from app.db.session import engine
from app.main import app
from app.services.ai_client import AICompletion, AIProviderTimeout, AIToolCall

OWNER_PHONE = "13800000001"
OUTSIDER_PHONE = "13800000002"


class FakeAIClient:
    def __init__(self, responses: list[AICompletion | Exception]) -> None:
        self.responses = responses
        self.calls: list[dict[str, Any]] = []

    async def complete(
        self,
        *,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        provider_user_id: str,
    ) -> AICompletion:
        self.calls.append(
            {
                "messages": messages,
                "tools": tools,
                "provider_user_id": provider_user_id,
            }
        )
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


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


def create_farm(token: str, name: str = "测试农场") -> dict[str, Any]:
    response = call(token, "/api/v1/farms", method="post", json={"name": name})
    assert response.status_code == 201
    return response.json()["data"]


def create_plot(token: str, farm_id: int, name: str) -> dict[str, Any]:
    response = call(
        token,
        f"/api/v1/farms/{farm_id}/plots",
        method="post",
        json={"name": name, "type": "GREENHOUSE", "areaValue": "1", "areaUnit": "MU"},
    )
    assert response.status_code == 201
    return response.json()["data"]


def create_conversation(token: str, farm_id: int) -> dict[str, Any]:
    response = call(
        token,
        "/api/v1/ai/conversations",
        method="post",
        json={"farmId": farm_id},
    )
    assert response.status_code == 201
    return response.json()["data"]


@pytest.fixture
def fake_client(monkeypatch: pytest.MonkeyPatch) -> FakeAIClient:
    client = FakeAIClient([])
    monkeypatch.setattr(settings, "ai_user_id_hash_key", SecretStr("test-ai-user-hash-key"))
    app.dependency_overrides[get_ai_client] = lambda: client
    yield client
    app.dependency_overrides.pop(get_ai_client, None)


def turn(token: str, conversation_id: int, message: str = "现在有什么？") -> httpx.Response:
    return call(
        token,
        "/api/v1/ai/turn",
        method="post",
        json={"conversationId": conversation_id, "message": message},
    )


def test_ai_turn_uses_read_only_tool_and_returns_verified_reference(
    fake_client: FakeAIClient,
) -> None:
    owner_token = login(OWNER_PHONE)
    farm = create_farm(owner_token)
    plot = create_plot(owner_token, farm["id"], "1号大棚")
    conversation = create_conversation(owner_token, farm["id"])
    fake_client.responses = [
        AICompletion(
            content=None,
            tool_calls=[
                AIToolCall(id="call-1", name="search_plots", arguments='{"keyword":"1号"}')
            ],
        ),
        AICompletion(content="当前农场有 1 个匹配地块：1号大棚。", tool_calls=[]),
    ]

    response = turn(owner_token, conversation["id"], "1号大棚有什么？")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["answer"] == "当前农场有 1 个匹配地块：1号大棚。"
    assert data["references"] == [
        {
            "kind": "PLOT",
            "id": plot["id"],
            "label": "1号大棚",
            "route": f"/pages/plots/detail?plotId={plot['id']}",
        }
    ]
    assert len(fake_client.calls) == 2
    assert OWNER_PHONE not in str(fake_client.calls)


def test_ai_turn_requires_member_and_honors_farm_ai_switch(fake_client: FakeAIClient) -> None:
    owner_token = login(OWNER_PHONE)
    outsider_token = login(OUTSIDER_PHONE)
    farm = create_farm(owner_token)
    conversation = create_conversation(owner_token, farm["id"])

    outsider_response = turn(outsider_token, conversation["id"])
    assert outsider_response.status_code == 404
    assert outsider_response.json()["error"]["code"] == "NOT_FOUND"
    assert not fake_client.calls

    disable_response = call(
        owner_token,
        f"/api/v1/farms/{farm['id']}",
        method="patch",
        json={"aiEnabled": False},
    )
    assert disable_response.status_code == 200
    assert disable_response.json()["data"]["aiEnabled"] is False

    disabled_response = turn(owner_token, conversation["id"])
    assert disabled_response.status_code == 403
    assert disabled_response.json()["error"]["code"] == "AI_NOT_ENABLED"
    assert not fake_client.calls


def test_ai_turn_returns_candidates_for_ambiguous_plot_name(fake_client: FakeAIClient) -> None:
    owner_token = login(OWNER_PHONE)
    farm = create_farm(owner_token)
    first_plot = create_plot(owner_token, farm["id"], "东区大棚")
    second_plot = create_plot(owner_token, farm["id"], "西区大棚")
    conversation = create_conversation(owner_token, farm["id"])
    fake_client.responses = [
        AICompletion(
            content=None,
            tool_calls=[
                AIToolCall(id="call-1", name="search_plots", arguments='{"keyword":"大棚"}')
            ],
        )
    ]

    response = turn(owner_token, conversation["id"], "大棚里种了什么？")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["needsSelection"] is True
    assert {candidate["id"] for candidate in data["candidates"]} == {
        first_plot["id"],
        second_plot["id"],
    }
    assert len(fake_client.calls) == 1
    messages_response = call(
        owner_token,
        f"/api/v1/ai/conversations/{conversation['id']}/messages",
    )
    stored_candidates = messages_response.json()["data"]["items"][1]["candidates"]
    assert {candidate["id"] for candidate in stored_candidates} == {
        first_plot["id"],
        second_plot["id"],
    }


def test_ai_turn_does_not_expose_a_plot_from_another_current_farm(
    fake_client: FakeAIClient,
) -> None:
    owner_token = login(OWNER_PHONE)
    first_farm = create_farm(owner_token, "第一个农场")
    second_farm = create_farm(owner_token, "第二个农场")
    private_plot = create_plot(owner_token, second_farm["id"], "不应泄露的地块")
    conversation = create_conversation(owner_token, first_farm["id"])
    fake_client.responses = [
        AICompletion(
            content=None,
            tool_calls=[
                AIToolCall(
                    id="call-1",
                    name="get_plot_detail",
                    arguments=f'{{"plot_id":{private_plot["id"]}}}',
                )
            ],
        ),
        AICompletion(content="当前农场没有匹配地块。", tool_calls=[]),
    ]

    response = turn(owner_token, conversation["id"])

    assert response.status_code == 200
    assert response.json()["data"]["references"] == []
    assert "不应泄露的地块" not in str(fake_client.calls[1]["messages"])


def test_ai_turn_enforces_quota_and_handles_provider_timeout(
    fake_client: FakeAIClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "ai_daily_turn_limit", 1)
    owner_token = login(OWNER_PHONE)
    farm = create_farm(owner_token)
    conversation = create_conversation(owner_token, farm["id"])
    fake_client.responses = [AICompletion(content="没有记录。", tool_calls=[])]

    first_response = turn(owner_token, conversation["id"])
    quota_response = turn(owner_token, conversation["id"])

    assert first_response.status_code == 200
    assert quota_response.status_code == 429
    assert quota_response.json()["error"]["code"] == "AI_QUOTA_EXCEEDED"

    monkeypatch.setattr(settings, "ai_daily_turn_limit", 20)
    second_farm = create_farm(owner_token, "超时农场")
    second_conversation = create_conversation(owner_token, second_farm["id"])
    fake_client.responses = [AIProviderTimeout()]
    timeout_response = turn(owner_token, second_conversation["id"])

    assert timeout_response.status_code == 504
    assert timeout_response.json()["error"]["code"] == "AI_UPSTREAM_TIMEOUT"


def test_ai_turn_skips_quota_for_unlimited_phone_number(
    fake_client: FakeAIClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "ai_daily_turn_limit", 1)
    monkeypatch.setattr(settings, "ai_unlimited_phone_numbers", f" {OWNER_PHONE} ")
    owner_token = login(OWNER_PHONE)
    farm = create_farm(owner_token)
    conversation = create_conversation(owner_token, farm["id"])
    fake_client.responses = [
        AICompletion(content="第一条回答。", tool_calls=[]),
        AICompletion(content="第二条回答。", tool_calls=[]),
    ]

    first_response = turn(owner_token, conversation["id"], "第一个问题？")
    second_response = turn(owner_token, conversation["id"], "第二个问题？")

    assert first_response.status_code == 200
    assert second_response.status_code == 200


def test_ai_turn_validation_and_tool_limit(
    fake_client: FakeAIClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    owner_token = login(OWNER_PHONE)
    farm = create_farm(owner_token)
    conversation = create_conversation(owner_token, farm["id"])
    invalid_response = turn(owner_token, conversation["id"], " " * 3)
    too_long_response = turn(
        owner_token, conversation["id"], "a" * (settings.ai_max_message_chars + 1)
    )
    assert invalid_response.status_code == 422
    assert too_long_response.status_code == 422

    monkeypatch.setattr(settings, "ai_max_tool_calls_per_turn", 1)
    fake_client.responses = [
        AICompletion(
            content=None,
            tool_calls=[
                AIToolCall(id="call-1", name="list_recent_activities", arguments="{}"),
                AIToolCall(id="call-2", name="list_recent_activities", arguments="{}"),
            ],
        )
    ]
    limit_response = turn(owner_token, conversation["id"])

    assert limit_response.status_code == 200
    assert "查询步骤较多" in limit_response.json()["data"]["answer"]
    assert len(fake_client.calls) == 1


def test_ai_conversation_persists_messages_and_can_be_deleted(
    fake_client: FakeAIClient,
) -> None:
    owner_token = login(OWNER_PHONE)
    farm = create_farm(owner_token)
    conversation = create_conversation(owner_token, farm["id"])
    fake_client.responses = [AICompletion(content="当前没有记录。", tool_calls=[])]

    turn_response = turn(owner_token, conversation["id"], "现在有哪些记录？")
    messages_response = call(owner_token, f"/api/v1/ai/conversations/{conversation['id']}/messages")
    conversations_response = call(owner_token, "/api/v1/ai/conversations")

    assert turn_response.status_code == 200
    assert messages_response.status_code == 200
    messages = messages_response.json()["data"]
    assert [item["role"] for item in messages["items"]] == ["user", "assistant"]
    assert messages["items"][0]["content"] == "现在有哪些记录？"
    assert messages["items"][1]["content"] == "当前没有记录。"
    assert conversations_response.json()["data"]["items"][0]["title"] == "现在有哪些记录？"

    delete_response = call(
        owner_token,
        f"/api/v1/ai/conversations/{conversation['id']}",
        method="delete",
    )
    missing_response = call(owner_token, f"/api/v1/ai/conversations/{conversation['id']}/messages")

    assert delete_response.status_code == 204
    assert missing_response.status_code == 404


def test_ai_turn_uses_server_persisted_history(fake_client: FakeAIClient) -> None:
    owner_token = login(OWNER_PHONE)
    farm = create_farm(owner_token)
    conversation = create_conversation(owner_token, farm["id"])
    fake_client.responses = [
        AICompletion(content="第一条回答。", tool_calls=[]),
        AICompletion(content="第二条回答。", tool_calls=[]),
    ]

    first_response = turn(owner_token, conversation["id"], "第一条问题？")
    second_response = turn(owner_token, conversation["id"], "第二条问题？")

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    second_messages = fake_client.calls[1]["messages"]
    assert {"role": "user", "content": "第一条问题？"} in second_messages
    assert {"role": "assistant", "content": "第一条回答。"} in second_messages


def test_removing_member_deletes_their_ai_conversations() -> None:
    owner_token = login(OWNER_PHONE)
    member_token = login(OUTSIDER_PHONE)
    farm = create_farm(owner_token)
    add_response = call(
        owner_token,
        f"/api/v1/farms/{farm['id']}/members",
        method="post",
        json={"phoneNumber": OUTSIDER_PHONE, "role": "MEMBER"},
    )
    assert add_response.status_code == 201
    member = add_response.json()["data"]
    conversation = create_conversation(member_token, farm["id"])

    remove_response = call(
        owner_token,
        f"/api/v1/farms/{farm['id']}/members/{member['id']}",
        method="delete",
    )
    readd_response = call(
        owner_token,
        f"/api/v1/farms/{farm['id']}/members",
        method="post",
        json={"phoneNumber": OUTSIDER_PHONE, "role": "MEMBER"},
    )
    messages_response = call(
        member_token,
        f"/api/v1/ai/conversations/{conversation['id']}/messages",
    )
    list_response = call(member_token, "/api/v1/ai/conversations")

    assert remove_response.status_code == 204
    assert readd_response.status_code == 201
    assert messages_response.status_code == 404
    assert list_response.json()["data"]["items"] == []
