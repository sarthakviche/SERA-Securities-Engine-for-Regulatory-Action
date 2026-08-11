"""Pydantic model -> strict Anthropic tool `input_schema` converter.

Used to force Claude's structured output (TRD §8.5 "Structured Output
Enforcement") via tool-use with `strict: true`, rather than free-text
parsing. Every object in the schema (including nested `$defs`) gets
`additionalProperties: false` and `required` set to ALL of its properties —
that's what "strict" means for Anthropic/OpenAI-style JSON-schema tool
calling: optionality is expressed by the field's type being nullable
(`anyOf: [..., {"type": "null"}]`), not by omitting it from `required`.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


def _tighten(node: Any) -> None:
    if isinstance(node, dict):
        if node.get("type") == "object" and "properties" in node:
            node["additionalProperties"] = False
            node["required"] = list(node["properties"].keys())
        for value in node.values():
            _tighten(value)
    elif isinstance(node, list):
        for item in node:
            _tighten(item)


def pydantic_to_tool_input_schema(model_cls: type[BaseModel]) -> dict[str, Any]:
    schema = model_cls.model_json_schema()
    schema.pop("$schema", None)
    schema.pop("title", None)
    _tighten(schema)
    return schema


def tool_from_output_model(model_cls: type[BaseModel], *, tool_name: str, description: str) -> dict[str, Any]:
    # "strict" is a top-level field on the tool definition itself (sibling of
    # input_schema), not on tool_choice — this is what actually turns on
    # strict JSON-schema enforcement server-side. Easy to omit since the
    # schema tightening (_tighten above) looks like the whole story but isn't.
    return {
        "name": tool_name,
        "description": description,
        "strict": True,
        "input_schema": pydantic_to_tool_input_schema(model_cls),
    }
