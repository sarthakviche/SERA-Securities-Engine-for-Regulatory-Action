from __future__ import annotations

from uuid import uuid4

import pytest

from app.adapters.memory.seed_data import DEPT_COMPLIANCE, OBLIGATION_AUDIT_LOG, OBLIGATION_REVERIFICATION, WORKFLOW_ID
from app.ai.graph.nodes.execution_handoff import handoff_to_execution_engine
from app.ai.graph.schemas.implementation_plan import ImplementationPlanOutput, ObligationPlan, ProposedTask
from app.ai.graph.schemas.sop_generation import SOPDraft, SOPGenerationOutput
from app.ai.graph.state import WorkflowState


def _sop_output() -> SOPGenerationOutput:
    return SOPGenerationOutput(
        sop_drafts=[
            SOPDraft(
                obligation_ids=[OBLIGATION_REVERIFICATION],
                department_id=DEPT_COMPLIANCE,
                title="Client Mobile Verification SOP",
                content="Re-verify every 12 months.",
                based_on_existing_sop_id=None,
                change_type="new",
                diff_summary=None,
                confidence=0.8,
            )
        ]
    )


def _plan_output(obligation_id=OBLIGATION_REVERIFICATION) -> ImplementationPlanOutput:
    return ImplementationPlanOutput(
        plans=[
            ObligationPlan(
                obligation_id=obligation_id,
                tasks=[
                    ProposedTask(
                        title="Reconfigure scheduler",
                        description="desc",
                        owner_department_id=DEPT_COMPLIANCE,
                        suggested_assignee_id=None,
                        due_date_rule="T+30d",
                        recurrence_rule="FREQ=YEARLY",
                        evidence_requirement="config diff",
                        priority="high",
                    )
                ],
            )
        ]
    )


async def _seed(deps, *, plan_obligation_id=OBLIGATION_REVERIFICATION) -> None:
    await deps.workflow_service.write_agent_output(WORKFLOW_ID, "sop_generation_agent", _sop_output())
    await deps.workflow_service.write_agent_output(
        WORKFLOW_ID, "evidence_implementation_plan_agent", _plan_output(plan_obligation_id)
    )


async def test_successful_handoff_writes_all_tables(deps, store):
    await _seed(deps)
    sops_before = len(store.tables.sops)
    tasks_before = len(store.tables.tasks)
    audit_before = len(store.tables.audit_log)

    await handoff_to_execution_engine(WorkflowState(workflow_id=WORKFLOW_ID), deps)

    assert len(store.tables.sops) == sops_before + 1
    assert len(store.tables.tasks) == tasks_before + 1
    assert len(store.tables.audit_log) == audit_before + 1

    obligation = next(o for o in store.tables.obligations if o.id == OBLIGATION_REVERIFICATION)
    assert obligation.status == "approved"

    document = await deps.workflow_service.get_document(WORKFLOW_ID)
    assert document.current_stage == "execution_handoff"


async def test_failed_handoff_rolls_back_everything(deps, store):
    nonexistent_obligation = uuid4()
    await _seed(deps, plan_obligation_id=nonexistent_obligation)

    sops_before = list(store.tables.sops)
    tasks_before = list(store.tables.tasks)
    audit_before = list(store.tables.audit_log)
    obligations_before = [
        (o.id, o.status) for o in store.tables.obligations
    ]

    with pytest.raises(KeyError):
        await handoff_to_execution_engine(WorkflowState(workflow_id=WORKFLOW_ID), deps)

    assert store.tables.sops == sops_before
    assert store.tables.tasks == tasks_before
    assert store.tables.audit_log == audit_before
    assert [(o.id, o.status) for o in store.tables.obligations] == obligations_before
