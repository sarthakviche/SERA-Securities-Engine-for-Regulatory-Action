from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.modules.workflow.schemas import (
    AgentTask,
    ExecutionHistoryEntry,
    GateApproval,
    WorkflowDocument as SchemaWorkflowDocument,
    WorkflowStatus,
)


class WorkflowRepository(Protocol):
    async def get(self, workflow_id: UUID) -> SchemaWorkflowDocument: ...

    async def update_swd_fields(
        self,
        workflow_id: UUID,
        *,
        agent_outputs: dict[str, object] | None = None,
        human_approvals: dict[str, GateApproval] | None = None,
        execution_history: list[ExecutionHistoryEntry] | None = None,
        agent_tasks: list[AgentTask] | None = None,
        document_metadata: dict[str, object] | None = None,
    ) -> SchemaWorkflowDocument: ...

    async def update_status(
        self, workflow_id: UUID, status: WorkflowStatus, current_stage: str
    ) -> SchemaWorkflowDocument: ...

    async def clear_human_approval(self, workflow_id: UUID, gate_name: str) -> SchemaWorkflowDocument: ...
