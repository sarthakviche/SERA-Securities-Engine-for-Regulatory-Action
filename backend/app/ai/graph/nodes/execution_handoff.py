"""execution_handoff — TRD §8.1's deterministic final node, "hands off to
Task Service". Spec detailed in sera_three_agents_workflow_and_plan.md §3:
the ONLY place `org_sops`/`obligations`/`tasks`/`audit_log` get real rows.

Runs inside a single transaction (`InMemoryOrgStore.begin()` in this slice —
see adapters/memory/store.py for why the real Postgres adapter MUST make
this an actual DB transaction): update obligation status, insert/amend SOPs,
bulk-insert tasks, write one audit_log entry. Any exception rolls the whole
thing back — the SWD stays at `pending_approval_2`, nothing partial lands
(fail closed, TRD §1 principle 7).
"""

from __future__ import annotations

from uuid import uuid4

from app.adapters.memory.store import TaskRow
from app.ai.graph.deps import NodeDeps
from app.ai.graph.schemas.implementation_plan import ImplementationPlanOutput
from app.ai.graph.schemas.sop_generation import SOPGenerationOutput
from app.ai.graph.state import WorkflowState
from app.core.events import DomainEvent
from app.modules.workflow.schemas import WorkflowStatus

AGENT_NAME = "execution_handoff"


async def handoff_to_execution_engine(state: WorkflowState, deps: NodeDeps) -> WorkflowState:
    document = await deps.workflow_service.get_document(state.workflow_id)

    sop_output = SOPGenerationOutput.model_validate(document.swd.agent_outputs["sop_generation_agent"])
    plan_output = ImplementationPlanOutput.model_validate(document.swd.agent_outputs["evidence_implementation_plan_agent"])

    async with deps.org_store.begin() as tx:
        for obligation_plan in plan_output.plans:
            await tx.update_obligation_status(obligation_plan.obligation_id, "approved")

        for draft in sop_output.sop_drafts:
            await tx.insert_or_amend_sop(
                organization_id=document.organization_id,
                based_on_existing_sop_id=draft.based_on_existing_sop_id,
                department_id=draft.department_id,
                title=draft.title,
                content=draft.content,
            )

        task_rows = [
            TaskRow(
                id=uuid4(),
                workflow_id=state.workflow_id,
                obligation_id=obligation_plan.obligation_id,
                organization_id=document.organization_id,
                title=task.title,
                description=task.description,
                owner_department_id=task.owner_department_id,
                assignee_user_id=task.suggested_assignee_id,
                due_date=None,  # resolved from due_date_rule by whichever service owns due-date computation
                status="open",
                evidence_requirement=task.evidence_requirement,
                priority=task.priority,
                recurrence_rule=task.recurrence_rule,
            )
            for obligation_plan in plan_output.plans
            for task in obligation_plan.tasks
        ]
        await tx.bulk_insert_tasks(task_rows)

        await tx.insert_audit_log(
            organization_id=document.organization_id,
            workflow_id=state.workflow_id,
            actor_type="system",
            actor_id=AGENT_NAME,
            action="materialize_workflow",
            entity_type="workflow_document",
            entity_id=str(state.workflow_id),
            before=None,
            after={"sop_count": len(sop_output.sop_drafts), "task_count": len(task_rows)},
        )
        # No exception raised above -> __aexit__ commits (swaps the live tables).
        # Any exception here propagates, __aexit__ discards the scratch copy,
        # and `document.swd` (already at pending_approval_2) is left untouched.

    await deps.workflow_service.append_execution_history(state.workflow_id, AGENT_NAME, "completed")
    await deps.event_publisher.publish(
        DomainEvent(
            event_type="workflow.stage_completed",
            organization_id=document.organization_id,
            workflow_id=state.workflow_id,
            payload={"agent_name": AGENT_NAME},
        )
    )
    await deps.workflow_service.advance_status(state.workflow_id, WorkflowStatus.executing, "execution_handoff")

    return state.advance()
