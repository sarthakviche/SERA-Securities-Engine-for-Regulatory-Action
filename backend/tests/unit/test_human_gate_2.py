from __future__ import annotations

import pytest

from app.adapters.memory.seed_data import WORKFLOW_ID
from app.ai.graph.nodes.human_gate_2 import human_gate_2
from app.ai.graph.state import WorkflowState
from app.modules.workflow.schemas import GateApproval, GateDecision


async def test_missing_approval_attempts_to_interrupt(deps):
    # interrupt() called outside an active graph run raises RuntimeError —
    # a real graph run would instead pause/checkpoint (see tests/integration
    # for the full pause-and-resume flow via graph.ainvoke + Command(resume=...)).
    with pytest.raises(RuntimeError):
        await human_gate_2(WorkflowState(workflow_id=WORKFLOW_ID), deps)


async def test_existing_approval_short_circuits_without_interrupt(deps):
    await deps.workflow_service.record_gate_approval(WORKFLOW_ID, "gate_2", GateApproval(decision=GateDecision.approved))
    await human_gate_2(WorkflowState(workflow_id=WORKFLOW_ID), deps)  # must not raise
    assert deps.event_publisher.published == []  # only rejection publishes an event


async def test_existing_rejection_publishes_event(deps):
    await deps.workflow_service.record_gate_approval(
        WORKFLOW_ID, "gate_2", GateApproval(decision=GateDecision.rejected, comment="rework needed")
    )
    await human_gate_2(WorkflowState(workflow_id=WORKFLOW_ID), deps)
    assert len(deps.event_publisher.published) == 1
    event = deps.event_publisher.published[0]
    assert event.event_type == "gate_2.rejected"
    assert event.payload["comment"] == "rework needed"
