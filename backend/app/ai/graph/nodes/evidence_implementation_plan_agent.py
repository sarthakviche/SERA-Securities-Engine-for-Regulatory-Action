"""evidence_implementation_plan_agent — TRD §8.1 node (the second of the 2
replacing the old single `planning_agent`), spec detailed in
sera_three_agents_workflow_and_plan.md §2.3.

Breaks each obligation into concrete tasks — the direct precursor to `tasks`
table rows (TRD §4.2). Same rule as SOPs: nothing is inserted into `tasks`
until `execution_handoff` runs on gate_2 approval; this is a proposal only.
No RAG/direct-reads beyond prior agent_outputs — everything it needs
(departments, SOP drafts, obligation frequency/evidence hints) is already
in the SWD from the two upstream nodes in this slice.
"""

from __future__ import annotations

from app.ai.graph.deps import NodeDeps
from app.ai.graph.nodes.common import generate_structured_or_flag
from app.ai.graph.projections import project_swd
from app.ai.graph.schemas.implementation_plan import ImplementationPlanOutput
from app.ai.graph.state import WorkflowState
from app.ai.prompts.evidence_implementation_plan_agent.v1 import SYSTEM_PROMPT, build_user_prompt
from app.core.events import DomainEvent
from app.modules.workflow.schemas import WorkflowStatus

AGENT_NAME = "evidence_implementation_plan_agent"


async def evidence_implementation_plan_agent(state: WorkflowState, deps: NodeDeps) -> WorkflowState:
    document = await deps.workflow_service.get_document(state.workflow_id)
    projection = project_swd(document.swd, AGENT_NAME)

    user_prompt = build_user_prompt(projection)

    result = await generate_structured_or_flag(
        deps=deps,
        workflow_id=state.workflow_id,
        agent_name=AGENT_NAME,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        response_schema=ImplementationPlanOutput,
    )

    await deps.workflow_service.write_agent_output(state.workflow_id, AGENT_NAME, result)
    await deps.workflow_service.append_execution_history(state.workflow_id, AGENT_NAME, "completed")

    await deps.event_publisher.publish(
        DomainEvent(
            event_type="workflow.stage_completed",
            organization_id=document.organization_id,
            workflow_id=state.workflow_id,
            payload={"agent_name": AGENT_NAME},
        )
    )

    await deps.workflow_service.advance_status(state.workflow_id, WorkflowStatus.pending_approval_2, "gate_2")

    return state.advance()
