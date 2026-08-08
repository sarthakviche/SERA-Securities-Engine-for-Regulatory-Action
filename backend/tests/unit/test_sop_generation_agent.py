from __future__ import annotations

from app.adapters.memory.seed_data import DEPT_COMPLIANCE, OBLIGATION_REVERIFICATION, WORKFLOW_ID
from app.ai.graph.nodes.sop_generation_agent import sop_generation_agent
from app.ai.graph.schemas.impact_mapping import DepartmentImpact, ImpactMappingOutput, ObligationImpact
from app.ai.graph.schemas.sop_generation import SOPDraft, SOPGenerationOutput
from app.ai.graph.state import WorkflowState
from app.modules.workflow.schemas import GateApproval, GateDecision


async def _seed_impact_mapping(deps) -> None:
    output = ImpactMappingOutput(
        mappings=[
            ObligationImpact(
                obligation_id=OBLIGATION_REVERIFICATION,
                affected_departments=[
                    DepartmentImpact(department_id=DEPT_COMPLIANCE, department_name_suggested="Compliance", role="primary_owner")
                ],
                affected_systems=[],
                impact_severity="high",
                dependencies=[],
                rationale="r",
                confidence=0.9,
            )
        ]
    )
    await deps.workflow_service.write_agent_output(WORKFLOW_ID, "impact_mapping_agent", output)


def _draft_output() -> SOPGenerationOutput:
    return SOPGenerationOutput(
        sop_drafts=[
            SOPDraft(
                obligation_ids=[OBLIGATION_REVERIFICATION],
                department_id=DEPT_COMPLIANCE,
                title="Amended SOP",
                content="new content",
                based_on_existing_sop_id=None,
                change_type="new",
                diff_summary=None,
                confidence=0.7,
            )
        ]
    )


async def test_never_writes_to_org_sops_table(deps, fake_llm_provider, store):
    await _seed_impact_mapping(deps)
    fake_llm_provider.queue(_draft_output())

    sops_before = list(store.tables.sops)
    await sop_generation_agent(WorkflowState(workflow_id=WORKFLOW_ID), deps)
    assert store.tables.sops == sops_before  # unchanged — proposal only, stays in SWD


async def test_writes_proposal_to_swd_and_advances_stage(deps, fake_llm_provider):
    await _seed_impact_mapping(deps)
    fake_llm_provider.queue(_draft_output())

    await sop_generation_agent(WorkflowState(workflow_id=WORKFLOW_ID), deps)

    document = await deps.workflow_service.get_document(WORKFLOW_ID)
    assert "sop_generation_agent" in document.swd.agent_outputs
    assert document.current_stage == "evidence_implementation_plan"
    event_types = [e.event_type for e in deps.event_publisher.published]
    assert event_types == ["workflow.stage_completed"]


async def test_rejection_feedback_included_in_prompt_on_loop_back(deps, fake_llm_provider):
    await _seed_impact_mapping(deps)
    await deps.workflow_service.record_gate_approval(
        WORKFLOW_ID, "gate_2", GateApproval(decision=GateDecision.rejected, comment="Please cite section 4.2 explicitly.")
    )
    fake_llm_provider.queue(_draft_output())

    await sop_generation_agent(WorkflowState(workflow_id=WORKFLOW_ID), deps)

    assert "Please cite section 4.2 explicitly." in fake_llm_provider.calls[0]["user_prompt"]
