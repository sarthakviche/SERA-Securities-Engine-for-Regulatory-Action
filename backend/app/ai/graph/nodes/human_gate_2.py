"""human_gate_2 — TRD §8.1's `graph.add_node("gate_2", human_gate_2)  #
interrupt() until human_approvals written`.

Uses LangGraph's own `interrupt()` primitive (TRD §8.4 ties checkpointing
directly to this pattern), not a plain read-only stub: if
`swd.human_approvals.gate_2` is already populated — e.g. a teammate's future
approval API already recorded a decision via `workflow_service.record_gate_approval`
before invoking/resuming the graph — this node proceeds immediately.
Otherwise it calls `interrupt(...)`, which pauses and checkpoints the graph
(`checkpointer.py`) until resumed with `Command(resume={...})`.

Routing (approved -> execution_handoff, rejected -> sop_generation) is a
conditional edge in build_graph.py, not this node — this node's only job is
to ensure `human_approvals.gate_2` ends up populated, and to fire
`gate_2.rejected` for the Notification Service / re-entry trigger.
"""

from __future__ import annotations

from datetime import datetime, timezone

from langgraph.types import interrupt

from app.ai.graph.deps import NodeDeps
from app.ai.graph.state import WorkflowState
from app.core.events import DomainEvent
from app.modules.workflow.schemas import GateApproval, GateDecision

AGENT_NAME = "gate_2"


async def human_gate_2(state: WorkflowState, deps: NodeDeps) -> WorkflowState:
    document = await deps.workflow_service.get_document(state.workflow_id)
    approval = document.swd.human_approvals.get("gate_2")

    if approval is None:
        resumed = interrupt(
            {
                "workflow_id": str(state.workflow_id),
                "prompt": "Department head approval required for the SOP amendment(s) and implementation plan.",
                "sop_drafts": document.swd.agent_outputs.get("sop_generation_agent"),
                "implementation_plan": document.swd.agent_outputs.get("evidence_implementation_plan_agent"),
            }
        )
        approval = GateApproval(
            decision=GateDecision(resumed["decision"]),
            approved_by=resumed.get("approved_by"),
            approved_at=datetime.now(timezone.utc),
            comment=resumed.get("comment"),
        )
        await deps.workflow_service.record_gate_approval(state.workflow_id, "gate_2", approval)

    if approval.decision == GateDecision.rejected:
        await deps.event_publisher.publish(
            DomainEvent(
                event_type="gate_2.rejected",
                organization_id=document.organization_id,
                workflow_id=state.workflow_id,
                payload={"comment": approval.comment},
            )
        )

    return state.advance()
