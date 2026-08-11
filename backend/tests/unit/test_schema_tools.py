from __future__ import annotations

from app.ai.graph.schemas.impact_mapping import ImpactMappingOutput
from app.ai.graph.schemas.implementation_plan import ImplementationPlanOutput
from app.ai.graph.schemas.sop_generation import SOPGenerationOutput
from app.ai.providers.schema_tools import pydantic_to_tool_input_schema, tool_from_output_model


def _assert_strict(node) -> None:
    if isinstance(node, dict):
        if node.get("type") == "object" and "properties" in node:
            assert node.get("additionalProperties") is False
            assert set(node["required"]) == set(node["properties"].keys())
        for value in node.values():
            _assert_strict(value)
    elif isinstance(node, list):
        for item in node:
            _assert_strict(item)


import pytest


@pytest.mark.parametrize("model_cls", [ImpactMappingOutput, SOPGenerationOutput, ImplementationPlanOutput])
def test_every_object_is_strict(model_cls):
    schema = pydantic_to_tool_input_schema(model_cls)
    _assert_strict(schema)
    _assert_strict(schema.get("$defs", {}))


def test_tool_from_output_model_shape():
    tool = tool_from_output_model(ImpactMappingOutput, tool_name="emit_x", description="desc")
    assert tool["name"] == "emit_x"
    assert tool["description"] == "desc"
    assert tool["strict"] is True  # top-level field, sibling of input_schema — not on tool_choice
    assert "input_schema" in tool
    assert "$schema" not in tool["input_schema"]
