from __future__ import annotations

from types import SimpleNamespace

import pytest
from pydantic import BaseModel

from app.ai.providers.llm_provider import AnthropicLLMProvider, StructuredGenerationError
from app.core.config import Settings


class Foo(BaseModel):
    value: int


def _tool_use_response(tool_input: dict, *, stop_reason: str = "tool_use", tool_id: str = "tool_1"):
    block = SimpleNamespace(type="tool_use", input=tool_input, id=tool_id)
    return SimpleNamespace(stop_reason=stop_reason, content=[block])


class FakeMessages:
    def __init__(self, responses: list) -> None:
        self._responses = list(responses)
        self.create_calls: list[dict] = []

    async def create(self, **kwargs):
        self.create_calls.append(kwargs)
        return self._responses.pop(0)


class FakeClient:
    def __init__(self, responses: list) -> None:
        self.messages = FakeMessages(responses)


def _provider(responses: list) -> tuple[AnthropicLLMProvider, FakeClient]:
    client = FakeClient(responses)
    settings = Settings(anthropic_api_key="test", anthropic_model="claude-sonnet-5")
    return AnthropicLLMProvider(settings, client=client), client


async def test_succeeds_first_attempt():
    provider, client = _provider([_tool_use_response({"value": 42})])
    result = await provider.generate_structured(system_prompt="sys", user_prompt="usr", response_schema=Foo)
    assert result == Foo(value=42)
    assert len(client.messages.create_calls) == 1


async def test_retries_then_succeeds():
    provider, client = _provider(
        [
            _tool_use_response({"value": "not-an-int"}),  # fails validation
            _tool_use_response({"value": 7}),
        ]
    )
    result = await provider.generate_structured(system_prompt="sys", user_prompt="usr", response_schema=Foo, max_retries=2)
    assert result == Foo(value=7)
    assert len(client.messages.create_calls) == 2
    # second call must include the tool_result/is_error retry message
    second_call_messages = client.messages.create_calls[1]["messages"]
    assert second_call_messages[-1]["content"][0]["is_error"] is True


async def test_exhausts_retries_and_raises():
    provider, client = _provider(
        [
            _tool_use_response({"value": "a"}),
            _tool_use_response({"value": "b"}),
            _tool_use_response({"value": "c"}),
        ]
    )
    with pytest.raises(StructuredGenerationError):
        await provider.generate_structured(system_prompt="sys", user_prompt="usr", response_schema=Foo, max_retries=2)
    assert len(client.messages.create_calls) == 3


async def test_refusal_raises_immediately():
    provider, client = _provider([_tool_use_response({"value": 1}, stop_reason="refusal")])
    with pytest.raises(StructuredGenerationError):
        await provider.generate_structured(system_prompt="sys", user_prompt="usr", response_schema=Foo, max_retries=2)
    assert len(client.messages.create_calls) == 1
