from __future__ import annotations

import pytest

from app.ai.graph.projections import ProjectionFieldMissingError, project_swd
from app.modules.workflow.schemas import GateApproval, GateDecision, SWDPayload


def _swd(**overrides) -> SWDPayload:
    base = dict(
        document_metadata={"title": "t"},
        agent_outputs={
            "obligation_extraction_agent": {"obligations": []},
            "change_analysis_agent": {"summary": "s"},
            "ambiguity_detection_agent": {"resolved_clarifications": []},
        },
        human_approvals={"gate_1": GateApproval(decision=GateDecision.approved)},
    )
    base.update(overrides)
    return SWDPayload(**base)


def test_impact_mapping_projection_resolves_all_required_fields():
    swd = _swd()
    projection = project_swd(swd, "impact_mapping_agent")
    assert projection["document_metadata"] == {"title": "t"}
    assert projection["obligation_extraction_agent"] == {"obligations": []}
    assert projection["gate_1"]["decision"] == "approved"


def test_missing_required_field_raises():
    swd = _swd(human_approvals={})
    with pytest.raises(ProjectionFieldMissingError):
        project_swd(swd, "impact_mapping_agent")


def test_sop_generation_gate_2_is_optional_when_absent():
    swd = _swd(
        agent_outputs={
            "impact_mapping_agent": {"mappings": []},
            "obligation_extraction_agent": {"obligations": []},
        }
    )
    projection = project_swd(swd, "sop_generation_agent")
    assert projection["gate_2"] is None


def test_sop_generation_gate_2_present_on_loop_back():
    swd = _swd(
        agent_outputs={
            "impact_mapping_agent": {"mappings": []},
            "obligation_extraction_agent": {"obligations": []},
        },
        human_approvals={
            "gate_1": GateApproval(decision=GateDecision.approved),
            "gate_2": GateApproval(decision=GateDecision.rejected, comment="needs rework"),
        },
    )
    projection = project_swd(swd, "sop_generation_agent")
    assert projection["gate_2"]["comment"] == "needs rework"
