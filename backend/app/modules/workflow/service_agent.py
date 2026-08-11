from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel

from app.modules.workflow.repository_protocol import WorkflowRepository
from app.modules.workflow.schemas import (
    AgentTask,
    ExecutionHistoryEntry,
    GateApproval,
    SWDPayload,
    WorkflowDocument,
    WorkflowStatus,
)

class AgentWorkflowService:
    def __init__(self, repository: WorkflowRepository) -> None:
        self._repository = repository

    async def get_document(self, workflow_id: UUID) -> WorkflowDocument:
        return await self._repository.get(workflow_id)

    async def get_swd(self, workflow_id: UUID) -> SWDPayload:
        return (await self._repository.get(workflow_id)).swd

    async def write_agent_output(self, workflow_id: UUID, agent_name: str, output: BaseModel) -> WorkflowDocument:
        return await self._repository.update_swd_fields(
            workflow_id, agent_outputs={agent_name: output.model_dump(mode="json")}
        )

    async def append_execution_history(
        self, workflow_id: UUID, agent_name: str, status: str, detail: str | None = None
    ) -> WorkflowDocument:
        swd = await self.get_swd(workflow_id)
        entry = ExecutionHistoryEntry(
            agent_name=agent_name,
            timestamp=datetime.now(timezone.utc),
            status=status,
            detail=detail,
        )
        return await self._repository.update_swd_fields(
            workflow_id, execution_history=[*swd.execution_history, entry]
        )

    async def add_agent_task(
        self, workflow_id: UUID, *, raised_by_agent: str, reason: str, context: dict | None = None
    ) -> AgentTask:
        swd = await self.get_swd(workflow_id)
        task = AgentTask(
            id=uuid4(),
            raised_by_agent=raised_by_agent,
            reason=reason,
            context=context or {},
            created_at=datetime.now(timezone.utc),
        )
        await self._repository.update_swd_fields(workflow_id, agent_tasks=[*swd.agent_tasks, task])
        return task

    async def record_gate_approval(self, workflow_id: UUID, gate_name: str, approval: GateApproval) -> WorkflowDocument:
        return await self._repository.update_swd_fields(workflow_id, human_approvals={gate_name: approval})

    async def clear_gate_approval(self, workflow_id: UUID, gate_name: str) -> WorkflowDocument:
        """Removes a previously-recorded gate decision — used by
        sop_generation_agent after consuming a gate_2 rejection's feedback
        for a re-draft, so the next pass through gate_2 pauses fresh instead
        of finding the stale rejection and looping forever.
        """
        return await self._repository.clear_human_approval(workflow_id, gate_name)

    async def advance_status(self, workflow_id: UUID, status: WorkflowStatus, current_stage: str) -> WorkflowDocument:
        return await self._repository.update_status(workflow_id, status, current_stage)
