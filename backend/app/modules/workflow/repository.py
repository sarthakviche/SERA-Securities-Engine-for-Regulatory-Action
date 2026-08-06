"""Workflow Repository — the ONLY place raw queries against
`workflow_documents` are meant to live (TRD §7.1 layering rule). This slice
ships `InMemoryWorkflowRepository`; a teammate's SQLAlchemy-backed repository
satisfies the same `WorkflowRepository` Protocol against the real table
(TRD §4.2), including the row-level security policy in §4.4.

`update_swd_fields` MERGES `agent_outputs`/`human_approvals` at the top
level rather than replacing the whole `swd` blob — each agent node only ever
writes its own key, so this is what keeps one agent's write from clobbering
another's. `execution_history`/`agent_tasks` are replaced wholesale per call
since callers already read-then-append (see workflow/service.py).
"""

from __future__ import annotations

import copy
from typing import Protocol
from uuid import UUID

from app.modules.workflow.schemas import (
    AgentTask,
    ExecutionHistoryEntry,
    GateApproval,
    WorkflowDocument,
    WorkflowStatus,
)


class WorkflowRepository(Protocol):
    async def get(self, workflow_id: UUID) -> WorkflowDocument: ...

    async def update_swd_fields(
        self,
        workflow_id: UUID,
        *,
        agent_outputs: dict[str, object] | None = None,
        human_approvals: dict[str, GateApproval] | None = None,
        execution_history: list[ExecutionHistoryEntry] | None = None,
        agent_tasks: list[AgentTask] | None = None,
        document_metadata: dict[str, object] | None = None,
    ) -> WorkflowDocument: ...

    async def update_status(
        self, workflow_id: UUID, status: WorkflowStatus, current_stage: str
    ) -> WorkflowDocument: ...

    async def clear_human_approval(self, workflow_id: UUID, gate_name: str) -> WorkflowDocument: ...


class InMemoryWorkflowRepository:
    def __init__(self, documents: dict[UUID, WorkflowDocument] | None = None) -> None:
        self._documents: dict[UUID, WorkflowDocument] = documents or {}

    def seed(self, document: WorkflowDocument) -> None:
        self._documents[document.id] = document

    async def get(self, workflow_id: UUID) -> WorkflowDocument:
        try:
            return self._documents[workflow_id].model_copy(deep=True)
        except KeyError:
            raise KeyError(f"workflow_document {workflow_id} not found") from None

    async def update_swd_fields(
        self,
        workflow_id: UUID,
        *,
        agent_outputs: dict[str, object] | None = None,
        human_approvals: dict[str, GateApproval] | None = None,
        execution_history: list[ExecutionHistoryEntry] | None = None,
        agent_tasks: list[AgentTask] | None = None,
        document_metadata: dict[str, object] | None = None,
    ) -> WorkflowDocument:
        current = self._documents[workflow_id]
        swd = current.swd

        if agent_outputs is not None:
            merged_outputs = copy.deepcopy(swd.agent_outputs)
            merged_outputs.update(agent_outputs)
            swd = swd.model_copy(update={"agent_outputs": merged_outputs})

        if human_approvals is not None:
            merged_approvals = dict(swd.human_approvals)
            merged_approvals.update(human_approvals)
            swd = swd.model_copy(update={"human_approvals": merged_approvals})

        if execution_history is not None:
            swd = swd.model_copy(update={"execution_history": execution_history})

        if agent_tasks is not None:
            swd = swd.model_copy(update={"agent_tasks": agent_tasks})

        if document_metadata is not None:
            merged_metadata = copy.deepcopy(swd.document_metadata)
            merged_metadata.update(document_metadata)
            swd = swd.model_copy(update={"document_metadata": merged_metadata})

        updated = current.model_copy(update={"swd": swd})
        self._documents[workflow_id] = updated
        return updated.model_copy(deep=True)

    async def update_status(
        self, workflow_id: UUID, status: WorkflowStatus, current_stage: str
    ) -> WorkflowDocument:
        current = self._documents[workflow_id]
        updated = current.model_copy(update={"status": status, "current_stage": current_stage})
        self._documents[workflow_id] = updated
        return updated.model_copy(deep=True)

    async def clear_human_approval(self, workflow_id: UUID, gate_name: str) -> WorkflowDocument:
        current = self._documents[workflow_id]
        remaining = {k: v for k, v in current.swd.human_approvals.items() if k != gate_name}
        swd = current.swd.model_copy(update={"human_approvals": remaining})
        updated = current.model_copy(update={"swd": swd})
        self._documents[workflow_id] = updated
        return updated.model_copy(deep=True)
