"""LLMProvider abstraction (TRD §3 names `ai/providers/`) — wraps the
Anthropic Messages API to implement TRD §8.2's

    result = await llm_provider.generate_structured(
        prompt=render_prompt(agent_name, ctx, retrieved),
        response_schema=AGENT_OUTPUT_SCHEMAS[agent_name],
    )

`generate_structured` forces `tool_choice` on a single tool whose
`input_schema` is derived from `response_schema` via `schema_tools.py`
(`strict`-shaped: `additionalProperties: false` + full `required`). On a
Pydantic validation failure, it retries in the *same* conversation using a
`tool_result` block with `is_error: true` so Claude sees exactly what was
wrong — up to `max_retries` (TRD §8.5: "max 2 attempts, then routes to an
agent_task for human review"). This module raises `StructuredGenerationError`
on exhaustion; routing that to an `agent_task` is the calling node's job
(see ai/graph/nodes/common.py), not this provider's.
"""

from __future__ import annotations

from typing import Protocol, TypeVar

import anthropic
from pydantic import BaseModel, ValidationError

from app.ai.providers.schema_tools import tool_from_output_model
from app.core.config import Settings

T = TypeVar("T", bound=BaseModel)


class StructuredGenerationError(Exception):
    def __init__(self, message: str, *, last_raw_input: dict | None = None, cause: Exception | None = None) -> None:
        super().__init__(message)
        self.last_raw_input = last_raw_input
        self.cause = cause


class LLMProvider(Protocol):
    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_schema: type[T],
        max_retries: int = 2,
    ) -> T: ...


class AnthropicLLMProvider:
    def __init__(self, settings: Settings, client: anthropic.AsyncAnthropic | None = None) -> None:
        self._settings = settings
        self._client = client or anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_schema: type[T],
        max_retries: int = 2,
    ) -> T:
        tool_name = f"emit_{response_schema.__name__.lower()}"
        tool = tool_from_output_model(
            response_schema, tool_name=tool_name, description=f"Emit a valid {response_schema.__name__}."
        )
        messages: list[dict] = [{"role": "user", "content": user_prompt}]
        last_raw_input: dict | None = None
        last_error: Exception | None = None

        for attempt in range(max_retries + 1):
            response = await self._client.messages.create(
                model=self._settings.anthropic_model,
                # Sonnet 5 runs adaptive thinking by default (no thinking param
                # needed/set here), and max_tokens caps thinking + tool output
                # together — 16000 leaves headroom so a large circular (many
                # obligations/departments) doesn't truncate the JSON mid-object.
                max_tokens=16000,
                system=system_prompt,
                tools=[tool],
                tool_choice={"type": "tool", "name": tool_name},
                messages=messages,
            )

            if response.stop_reason == "refusal":
                raise StructuredGenerationError(
                    f"{response_schema.__name__}: model refused to generate output", last_raw_input=last_raw_input
                )

            tool_use_block = next((b for b in response.content if b.type == "tool_use"), None)
            if tool_use_block is None:
                last_error = RuntimeError("no tool_use block in response despite forced tool_choice")
                last_raw_input = None
            else:
                last_raw_input = tool_use_block.input
                try:
                    return response_schema.model_validate(tool_use_block.input)
                except ValidationError as exc:
                    last_error = exc

            if attempt == max_retries:
                break

            messages.append({"role": "assistant", "content": response.content})
            messages.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_use_block.id if tool_use_block else "unknown",
                            "content": f"Validation failed: {last_error}. Call {tool_name} again with corrected input.",
                            "is_error": True,
                        }
                    ],
                }
            )

        raise StructuredGenerationError(
            f"{response_schema.__name__}: exhausted {max_retries + 1} attempts, last error: {last_error}",
            last_raw_input=last_raw_input,
            cause=last_error,
        )
