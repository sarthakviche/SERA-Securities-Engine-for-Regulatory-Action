"""sop_generation_agent — TRD §8.1 node (one of the 2 replacing the old
single `planning_agent`), spec detailed in
sera_three_agents_workflow_and_plan.md §2.2.

Drafts a new SOP or an amendment to an existing one, per obligation and per
department impact_mapping_agent identified. Deliberately never calls any
write method on `organizational_repo` — only its read-only lookups
(`list_sops_for_departments`, used to decide new-vs-amendment) — which
structurally enforces "proposal only, nothing lands in `org_sops` until
gate_2 approves" (companion doc §2.2) rather than relying on convention.
`org_sops` only gets real rows in `execution_handoff`.
"""

from __future__ import annotations

from app.ai.graph.deps import NodeDeps
from app.ai.graph.nodes.common import generate_structured_or_flag
from app.ai.graph.projections import project_swd
from app.ai.graph.schemas.sop_generation import SOPGenerationOutput
from app.ai.graph.state import WorkflowState
from app.ai.prompts.sop_generation_agent.v1 import SYSTEM_PROMPT, build_user_prompt
from app.core.events import DomainEvent
from app.modules.workflow.schemas import WorkflowStatus

AGENT_NAME = "sop_generation_agent"


async def sop_generation_agent(state: WorkflowState, deps: NodeDeps) -> WorkflowState:
    document = await deps.workflow_service.get_document(state.workflow_id)
    projection = project_swd(document.swd, AGENT_NAME)

    impact_mapping = projection.get("impact_mapping_agent", {})
    department_ids = sorted(
        {
            dept["department_id"]
            for mapping in impact_mapping.get("mappings", [])
            for dept in mapping.get("affected_departments", [])
            if dept.get("department_id") is not None
        }
    )

    obligations = projection.get("obligation_extraction_agent", {}).get("obligations", [])
    query = " ".join(o.get("description", "") for o in obligations)
    retrieved = await deps.retrieval_provider.search_organizational(
        query, document.organization_id, top_k=8, department_ids=department_ids or None
    )

    # existing SOPs for the impacted departments, for the new-vs-amendment match
    existing_sops = await deps.organizational_repo.list_sops_for_departments(department_ids)

    user_prompt = build_user_prompt(
        projection,
        [chunk.model_dump(mode="json") for chunk in retrieved],
        {"existing_sops": [{"id": str(s.id), "department_id": str(s.department_id) if s.department_id else None, "title": s.title, "content": s.content, "version": s.version} for s in existing_sops]},
    )

    result = await generate_structured_or_flag(
        deps=deps,
        workflow_id=state.workflow_id,
        agent_name=AGENT_NAME,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        response_schema=SOPGenerationOutput,
    )

    await deps.workflow_service.write_agent_output(state.workflow_id, AGENT_NAME, result)
    await deps.workflow_service.append_execution_history(state.workflow_id, AGENT_NAME, "completed")

    if projection.get("gate_2") is not None:
        # This was a loop-back re-run: the prior gate_2 rejection's comment
        # was just used above to inform the re-draft. Clear it now so the
        # next pass through gate_2 pauses for a FRESH decision instead of
        # finding the stale rejection and looping forever (gate_2 re-runs
        # its whole node body on LangGraph resume — see human_gate_2.py).
        await deps.workflow_service.clear_gate_approval(state.workflow_id, "gate_2")

    await deps.event_publisher.publish(
        DomainEvent(
            event_type="workflow.stage_completed",
            organization_id=document.organization_id,
            workflow_id=state.workflow_id,
            payload={"agent_name": AGENT_NAME},
        )
    )

    await deps.workflow_service.advance_status(state.workflow_id, WorkflowStatus.planning, "evidence_implementation_plan")

    return state.advance()
