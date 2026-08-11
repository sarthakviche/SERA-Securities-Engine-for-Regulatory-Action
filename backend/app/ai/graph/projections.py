"""SWD -> per-agent minimal context builder (TRD §8.3, "the token-savings
mechanism"). `REQUIRED_FIELDS` is an explicit allowlist per agent, reviewed
in code review whenever an agent's prompt changes — intentionally not
"smart"/automatic, because an explicit allowlist is auditable and an
inferred one isn't (TRD §8.3).

Only the 3 agents in this slice (feature/Mapping_Agents) are populated
below. Teammates implementing applicability_agent / obligation_extraction_agent
/ change_analysis_agent / ambiguity_detection_agent should add their own
entries here rather than create a second REQUIRED_FIELDS dict — this is the
one and only allowlist, per TRD §8.3.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from app.modules.workflow.schemas import SWDPayload
from app.modules.workflow.service import WorkflowService

REQUIRED_FIELDS: dict[str, list[str]] = {
    "impact_mapping_agent": [
        "document_metadata",
        "agent_outputs.obligation_extraction_agent",
        "agent_outputs.change_analysis_agent",
        "agent_outputs.ambiguity_detection_agent",
        "human_approvals.gate_1",
    ],
    "sop_generation_agent": [
        "agent_outputs.impact_mapping_agent",
        "agent_outputs.obligation_extraction_agent",
        "document_metadata",
        "human_approvals.gate_2",  # only populated on loop-back re-run
    ],
    "evidence_implementation_plan_agent": [
        "agent_outputs.impact_mapping_agent",
        "agent_outputs.sop_generation_agent",
        "agent_outputs.obligation_extraction_agent",
    ],
    # --- TODO(teammate): add entries for applicability_agent,
    # obligation_extraction_agent, change_analysis_agent,
    # ambiguity_detection_agent as those nodes are implemented. ---
}

# Paths allowed to resolve to None instead of raising — the loop-back-only
# gate_2 field for sop_generation_agent is the only one in this slice.
OPTIONAL_FIELDS: dict[str, set[str]] = {
    "sop_generation_agent": {"human_approvals.gate_2"},
}


class ProjectionFieldMissingError(Exception):
    def __init__(self, agent_name: str, path: str) -> None:
        super().__init__(f"{agent_name}: required projection field '{path}' missing from SWD")
        self.agent_name = agent_name
        self.path = path


def _resolve_path(swd_dict: dict[str, Any], path: str) -> Any:
    node: Any = swd_dict
    for part in path.split("."):
        if not isinstance(node, dict) or part not in node:
            raise KeyError(path)
        node = node[part]
    return node


def project_swd(swd: SWDPayload, agent_name: str) -> dict[str, Any]:
    """Pure function: SWD payload -> flat context dict keyed by each
    required path's last segment. Split out from `build_projection` so it
    can be unit-tested without a WorkflowService/store.
    """

    required_paths = REQUIRED_FIELDS[agent_name]
    optional_paths = OPTIONAL_FIELDS.get(agent_name, set())
    swd_dict = swd.model_dump(mode="json")

    projection: dict[str, Any] = {}
    for path in required_paths:
        key = path.split(".")[-1]
        try:
            projection[key] = _resolve_path(swd_dict, path)
        except KeyError:
            if path in optional_paths:
                projection[key] = None
            else:
                raise ProjectionFieldMissingError(agent_name, path) from None
    return projection


async def build_projection(workflow_service: WorkflowService, workflow_id: UUID, agent_name: str) -> dict[str, Any]:
    swd = await workflow_service.get_swd(workflow_id)
    return project_swd(swd, agent_name)
