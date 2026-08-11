"""Runs a fixture WorkflowDocument (seeded as if gate_1 already approved,
per sera_three_agents_workflow_and_plan.md's own test-order recommendation)
through the full compiled graph for this slice: impact_mapping ->
sop_generation -> evidence_implementation_plan -> gate_2 (interrupt/resume)
-> execution_handoff. Asserts final SWD shape, the obligations
.owner_department_id update, and that org_sops/tasks/audit_log got real
rows only after gate_2 approval.
"""

from __future__ import annotations

from langgraph.types import Command

from app.adapters.memory.seed_data import DEPT_COMPLIANCE, OBLIGATION_AUDIT_LOG, OBLIGATION_REVERIFICATION, WORKFLOW_ID
from app.ai.graph.build_graph import build_graph
from app.ai.graph.schemas.impact_mapping import DepartmentImpact, ImpactMappingOutput, ObligationImpact
from app.ai.graph.schemas.implementation_plan import ImplementationPlanOutput, ObligationPlan, ProposedTask
from app.ai.graph.schemas.sop_generation import SOPDraft, SOPGenerationOutput
from app.ai.graph.state import WorkflowState
from app.modules.workflow.schemas import WorkflowStatus


def _impact_mapping_output() -> ImpactMappingOutput:
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
                    DepartmentImpact(department_id=DEPT_COMPLIANCE, department_name_suggested="Compliance", role="contributor")
                ],
                affected_systems=[],
                impact_severity="medium",
                dependencies=[OBLIGATION_REVERIFICATION],
                rationale="audit log obligation depends on re-verification",
                confidence=0.8,
            ),
        ]
    )


def _sop_output() -> SOPGenerationOutput:
    return SOPGenerationOutput(
        sop_drafts=[
            SOPDraft(
                obligation_ids=[OBLIGATION_REVERIFICATION],
                department_id=DEPT_COMPLIANCE,
                title="Client Mobile Verification SOP",
                content="Re-verify every 12 months via authenticated OTP.",
                based_on_existing_sop_id=None,
                change_type="new",
                diff_summary=None,
                confidence=0.75,
            )
        ]
    )


def _plan_output() -> ImplementationPlanOutput:
    return ImplementationPlanOutput(
        plans=[
            ObligationPlan(
                obligation_id=OBLIGATION_REVERIFICATION,
                tasks=[
                    ProposedTask(
                        title="Reconfigure re-verification scheduler",
                        description="Change interval from 24 to 12 months",
                        owner_department_id=DEPT_COMPLIANCE,
                        suggested_assignee_id=None,
                        due_date_rule="T+30d from gate_2 approval",
                        recurrence_rule="FREQ=YEARLY;INTERVAL=1",
                        evidence_requirement="Signed scheduler config diff",
                        priority="high",
                    )
                ],
            ),
            ObligationPlan(obligation_id=OBLIGATION_AUDIT_LOG, tasks=[]),
        ]
    )


async def test_full_slice_pauses_at_gate_2_then_materializes_on_approval(deps, fake_llm_provider, store):
    sops_before = len(store.tables.sops)  # seed_data.build_store() already seeds 1 SOP
    tasks_before = len(store.tables.tasks)
    audit_before = len(store.tables.audit_log)

    fake_llm_provider.queue(_impact_mapping_output())
    fake_llm_provider.queue(_sop_output())
    fake_llm_provider.queue(_plan_output())

    graph = build_graph(deps)
    config = {"configurable": {"thread_id": str(WORKFLOW_ID)}}

    paused = await graph.ainvoke(WorkflowState(workflow_id=WORKFLOW_ID), config=config)
    assert "__interrupt__" in paused

    document = await deps.workflow_service.get_document(WORKFLOW_ID)
    assert document.status == WorkflowStatus.pending_approval_2
    assert set(document.swd.agent_outputs.keys()) >= {
        "impact_mapping_agent",
        "sop_generation_agent",
        "evidence_implementation_plan_agent",
    }
    # nothing materialized yet — still proposals
    assert len(store.tables.sops) == sops_before
    assert len(store.tables.tasks) == tasks_before

    await graph.ainvoke(Command(resume={"decision": "approved", "approved_by": None}), config=config)

    document = await deps.workflow_service.get_document(WORKFLOW_ID)
    assert document.status == WorkflowStatus.executing
    assert document.current_stage == "execution_handoff"

    obligations = await deps.obligation_repo.list()
    reverification = next(o for o in obligations if o.id == OBLIGATION_REVERIFICATION)
    assert reverification.owner_department_id == DEPT_COMPLIANCE
    assert reverification.status == "approved"

    assert len(store.tables.sops) == sops_before + 1
    assert len(store.tables.tasks) == tasks_before + 1
    assert len(store.tables.audit_log) == audit_before + 1


async def test_rejection_routes_back_to_sop_generation(deps, fake_llm_provider, store):
    sops_before = len(store.tables.sops)

    fake_llm_provider.queue(_impact_mapping_output())
    fake_llm_provider.queue(_sop_output())
    fake_llm_provider.queue(_plan_output())

    graph = build_graph(deps)
    config = {"configurable": {"thread_id": str(WORKFLOW_ID)}}

    await graph.ainvoke(WorkflowState(workflow_id=WORKFLOW_ID), config=config)

    # queue exactly one re-draft round for the loop-back: sop_generation and
    # evidence_implementation_plan each run once more, then gate_2 must pause
    # FRESH (not immediately re-reject on the stale prior decision — see the
    # clear_gate_approval() call in sop_generation_agent.py).
    fake_llm_provider.queue(_sop_output())
    fake_llm_provider.queue(_plan_output())

    resumed = await graph.ainvoke(
        Command(resume={"decision": "rejected", "comment": "Please cite section 4.2 explicitly."}),
        config=config,
    )

    event_types = [e.event_type for e in deps.event_publisher.published]
    assert event_types.count("gate_2.rejected") == 1

    # loop went back through sop_generation -> evidence_implementation_plan -> gate_2 again,
    # pausing fresh rather than looping forever on the stale rejection.
    assert "__interrupt__" in resumed
    assert len(store.tables.sops) == sops_before  # still nothing materialized

    document = await deps.workflow_service.get_document(WORKFLOW_ID)
    assert document.swd.human_approvals.get("gate_2") is None  # cleared, awaiting a fresh decision
