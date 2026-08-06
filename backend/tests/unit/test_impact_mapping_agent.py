from __future__ import annotations

from app.adapters.memory.seed_data import DEPT_COMPLIANCE, OBLIGATION_AUDIT_LOG, OBLIGATION_REVERIFICATION, WORKFLOW_ID
from app.ai.graph.nodes.impact_mapping_agent import impact_mapping_agent
from app.ai.graph.schemas.impact_mapping import DepartmentImpact, ImpactMappingOutput, ObligationImpact
from app.ai.graph.state import WorkflowState


def _output() -> ImpactMappingOutput:
    return ImpactMappingOutput(
        mappings=[
            ObligationImpact(
                obligation_id=OBLIGATION_REVERIFICATION,
                affected_departments=[
                    DepartmentImpact(department_id=DEPT_COMPLIANCE, department_name_suggested="Compliance", role="primary_owner")
                ],
                affected_systems=["CRM Client Records"],
                impact_severity="high",
                dependencies=[],
                rationale="matches obligation text",
                confidence=0.9,
            ),
            ObligationImpact(
                obligation_id=OBLIGATION_AUDIT_LOG,
                affected_departments=[
                    DepartmentImpact(department_id=None, department_name_suggested="Unknown Dept", role="informed")
                ],
                affected_systems=[],
                impact_severity="medium",
                dependencies=[OBLIGATION_REVERIFICATION],
                rationale="uncertain match",
                confidence=0.35,
            ),
        ]
    )


async def test_confident_mapping_updates_owner_department(deps, fake_llm_provider):
    fake_llm_provider.queue(_output())

    await impact_mapping_agent(WorkflowState(workflow_id=WORKFLOW_ID), deps)

    obligations = await deps.obligation_repo.list()
    by_id = {o.id: o for o in obligations}
    assert by_id[OBLIGATION_REVERIFICATION].owner_department_id == DEPT_COMPLIANCE


async def test_unresolved_department_does_not_guess_and_raises_agent_task(deps, fake_llm_provider):
    fake_llm_provider.queue(_output())

    await impact_mapping_agent(WorkflowState(workflow_id=WORKFLOW_ID), deps)

    obligations = await deps.obligation_repo.list()
    by_id = {o.id: o for o in obligations}
    assert by_id[OBLIGATION_AUDIT_LOG].owner_department_id is None

    document = await deps.workflow_service.get_document(WORKFLOW_ID)
    assert len(document.swd.agent_tasks) == 1
    assert document.swd.agent_tasks[0].raised_by_agent == "impact_mapping_agent"
    assert "Unknown Dept" in document.swd.agent_tasks[0].reason


async def test_publishes_both_events_and_writes_output(deps, fake_llm_provider):
    fake_llm_provider.queue(_output())

    await impact_mapping_agent(WorkflowState(workflow_id=WORKFLOW_ID), deps)

    event_types = [e.event_type for e in deps.event_publisher.published]
    assert event_types == ["impact_mapping.completed", "workflow.stage_completed"]

    document = await deps.workflow_service.get_document(WORKFLOW_ID)
    assert "impact_mapping_agent" in document.swd.agent_outputs
    assert document.current_stage == "sop_generation"
    assert document.swd.execution_history[-1].status == "completed"
