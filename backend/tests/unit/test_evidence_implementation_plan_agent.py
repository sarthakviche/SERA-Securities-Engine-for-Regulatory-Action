from __future__ import annotations

from app.adapters.memory.seed_data import DEPT_COMPLIANCE, OBLIGATION_REVERIFICATION, WORKFLOW_ID
from app.ai.graph.nodes.evidence_implementation_plan_agent import evidence_implementation_plan_agent
from app.ai.graph.schemas.implementation_plan import ImplementationPlanOutput, ObligationPlan, ProposedTask
from app.ai.graph.state import WorkflowState
from app.modules.workflow.schemas import WorkflowStatus


async def _seed_upstream(deps) -> None:
    await deps.workflow_service.write_agent_output(WORKFLOW_ID, "impact_mapping_agent", _fake_dict())
    await deps.workflow_service.write_agent_output(WORKFLOW_ID, "sop_generation_agent", _fake_dict())


class _FakeOutput:
    def model_dump(self, mode="json"):
        return {}


def _fake_dict():
    return _FakeOutput()


def _plan_output() -> ImplementationPlanOutput:
    return ImplementationPlanOutput(
        plans=[
            ObligationPlan(
                obligation_id=OBLIGATION_REVERIFICATION,
                tasks=[
                    ProposedTask(
                        title="Reconfigure OTP scheduler",
                        description="Change interval from 24 to 12 months",
                        owner_department_id=DEPT_COMPLIANCE,
                        suggested_assignee_id=None,
                        due_date_rule="T+30d from gate_2 approval",
                        recurrence_rule="FREQ=YEARLY;INTERVAL=1",
                        evidence_requirement="Signed scheduler config diff",
                        priority="high",
                    )
                ],
            )
        ]
    )


async def test_recurrence_rule_passed_through_unmodified(deps, fake_llm_provider):
    await _seed_upstream(deps)
    output = _plan_output()
    fake_llm_provider.queue(output)

    await evidence_implementation_plan_agent(WorkflowState(workflow_id=WORKFLOW_ID), deps)

    document = await deps.workflow_service.get_document(WORKFLOW_ID)
    stored = document.swd.agent_outputs["evidence_implementation_plan_agent"]
    assert stored["plans"][0]["tasks"][0]["recurrence_rule"] == "FREQ=YEARLY;INTERVAL=1"


async def test_advances_to_pending_approval_2(deps, fake_llm_provider):
    await _seed_upstream(deps)
    fake_llm_provider.queue(_plan_output())

    await evidence_implementation_plan_agent(WorkflowState(workflow_id=WORKFLOW_ID), deps)

    document = await deps.workflow_service.get_document(WORKFLOW_ID)
    assert document.status == WorkflowStatus.pending_approval_2
    assert document.current_stage == "gate_2"
