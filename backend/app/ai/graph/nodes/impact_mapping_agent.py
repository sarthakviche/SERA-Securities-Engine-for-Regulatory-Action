"""impact_mapping_agent — TRD §8.1 node, spec detailed in
sera_three_agents_workflow_and_plan.md §2.1.

For each obligation, resolves affected department(s)/system(s), classifies
each department's role, scores impact severity, flags inter-obligation
dependencies. Any department that can't be confidently matched is NOT
guessed — it's routed to an AgentTask for a human compliance officer,
fail-closed per TRD §1 principle 7. Confidently-resolved `primary_owner`
mappings get a real `obligations.owner_department_id` UPDATE (the row
already exists from obligation extraction — this is an update, not an
insert). Publishes `impact_mapping.completed` (a dedicated, companion-doc-
specific event — separate from `workflow.stage_completed` — so the
Notification Service can give department heads an early heads-up before
SOP/plan drafting finishes) in addition to the standard stage-advance event.
"""

from __future__ import annotations

import dataclasses
from typing import Any
from uuid import UUID

from app.ai.graph.deps import NodeDeps
from app.ai.graph.nodes.common import generate_structured_or_flag
from app.ai.graph.projections import project_swd
from app.ai.graph.schemas.impact_mapping import ImpactMappingOutput
from app.ai.graph.state import WorkflowState
from app.ai.prompts.impact_mapping_agent.v1 import SYSTEM_PROMPT, build_user_prompt
from app.core.events import DomainEvent
from app.modules.workflow.schemas import WorkflowStatus

AGENT_NAME = "impact_mapping_agent"


def _json_safe(row: Any) -> dict[str, Any]:
    return {k: (str(v) if isinstance(v, UUID) else v) for k, v in dataclasses.asdict(row).items()}


async def impact_mapping_agent(state: WorkflowState, deps: NodeDeps) -> WorkflowState:
    document = await deps.workflow_service.get_document(state.workflow_id)
    projection = project_swd(document.swd, AGENT_NAME)

    departments = await deps.organizational_repo.get_departments()
    systems = await deps.organizational_repo.get_systems()

    obligations = projection.get("obligation_extraction_agent", {}).get("obligations", [])
    query = " ".join(o.get("description", "") for o in obligations) or projection.get("document_metadata", {}).get(
        "title", ""
    )
    retrieved = await deps.retrieval_provider.search_organizational(query, document.organization_id, top_k=8)

    user_prompt = build_user_prompt(
        projection,
        [chunk.model_dump(mode="json") for chunk in retrieved],
        {
            "departments": [_json_safe(d) for d in departments],
            "systems": [_json_safe(s) for s in systems],
        },
    )

    result = await generate_structured_or_flag(
        deps=deps,
        workflow_id=state.workflow_id,
        agent_name=AGENT_NAME,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        response_schema=ImpactMappingOutput,
    )

    for mapping in result.mappings:
        for dept_impact in mapping.affected_departments:
            if dept_impact.department_id is None:
                await deps.workflow_service.add_agent_task(
                    state.workflow_id,
                    raised_by_agent=AGENT_NAME,
                    reason=(
                        f"No confident department match for obligation {mapping.obligation_id}: "
                        f"suggested '{dept_impact.department_name_suggested}'"
                    ),
                    context={
                        "obligation_id": str(mapping.obligation_id),
                        "department_name_suggested": dept_impact.department_name_suggested,
                    },
                )
            elif dept_impact.role == "primary_owner":
                await deps.obligation_repo.update_owner_department(mapping.obligation_id, dept_impact.department_id)

    await deps.workflow_service.write_agent_output(state.workflow_id, AGENT_NAME, result)
    await deps.workflow_service.append_execution_history(state.workflow_id, AGENT_NAME, "completed")

    await deps.event_publisher.publish(
        DomainEvent(
            event_type="impact_mapping.completed",
            organization_id=document.organization_id,
            workflow_id=state.workflow_id,
            payload={"mapping_count": len(result.mappings)},
        )
    )
    await deps.event_publisher.publish(
        DomainEvent(
            event_type="workflow.stage_completed",
            organization_id=document.organization_id,
            workflow_id=state.workflow_id,
            payload={"agent_name": AGENT_NAME},
        )
    )

    await deps.workflow_service.advance_status(state.workflow_id, WorkflowStatus.planning, "sop_generation")

    return state.advance()
