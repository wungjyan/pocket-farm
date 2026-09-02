from collections.abc import AsyncGenerator, Sequence
from dataclasses import dataclass
from typing import Any, Protocol, cast

from openai import APIConnectionError, APIStatusError, APITimeoutError, AsyncOpenAI

from app.core.config import settings
from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException


@dataclass(frozen=True)
class AIToolCall:
    id: str
    name: str
    arguments: str


@dataclass(frozen=True)
class AICompletion:
    content: str | None
    tool_calls: list[AIToolCall]


class AIClient(Protocol):
    async def complete(
        self,
        *,
        messages: Sequence[dict[str, Any]],
        tools: Sequence[dict[str, Any]],
        provider_user_id: str,
    ) -> AICompletion: ...


class AIProviderTimeout(Exception):
    pass


class AIProviderUnavailable(Exception):
    pass


class DeepSeekAIClient:
    def __init__(self, *, api_key: str, base_url: str, timeout_seconds: int) -> None:
        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url, timeout=timeout_seconds)

    async def close(self) -> None:
        await self._client.close()

    async def complete(
        self,
        *,
        messages: Sequence[dict[str, Any]],
        tools: Sequence[dict[str, Any]],
        provider_user_id: str,
    ) -> AICompletion:
        try:
            response = await self._client.chat.completions.create(
                model=settings.deepseek_model,
                messages=cast(Any, list(messages)),
                tools=cast(Any, list(tools)),
                tool_choice="auto",
                max_tokens=settings.ai_max_output_tokens,
                extra_body={"user": provider_user_id},
            )
        except APITimeoutError as exc:
            raise AIProviderTimeout from exc
        except (APIConnectionError, APIStatusError) as exc:
            raise AIProviderUnavailable from exc

        if not response.choices:
            raise AIProviderUnavailable
        message = response.choices[0].message
        return AICompletion(
            content=message.content,
            tool_calls=[
                AIToolCall(
                    id=tool_call.id,
                    name=tool_call.function.name,
                    arguments=tool_call.function.arguments,
                )
                for tool_call in message.tool_calls or []
            ],
        )


async def get_ai_client() -> AsyncGenerator[AIClient, None]:
    api_key = settings.deepseek_api_key
    hash_key = settings.ai_user_id_hash_key
    if api_key is None or hash_key is None:
        raise AppException(
            status_code=503,
            code=ErrorCode.AI_NOT_CONFIGURED,
            message="AI is not configured yet.",
        )

    client = DeepSeekAIClient(
        api_key=api_key.get_secret_value(),
        base_url=settings.deepseek_base_url,
        timeout_seconds=settings.ai_request_timeout_seconds,
    )
    try:
        yield client
    finally:
        await client.close()
