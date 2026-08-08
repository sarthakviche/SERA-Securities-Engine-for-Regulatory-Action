"""Workflow Repository — handles DB operations for workflows.
Merged implementation containing both SQLAlchemy (HEAD) and InMemory (Theirs) repositories.
"""

from __future__ import annotations

import copy
import uuid
from typing import Any, Dict, Optional, Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workflow_document import WorkflowDocument as DbWorkflowDocument
from app.modules.workflow.schemas import (
    AgentTask,
    ExecutionHistoryEntry,
    GateApproval,
    WorkflowDocument as SchemaWorkflowDocument,
    WorkflowStatus,
)

class SQLAlchemyWorkflowRepository:
    async def get_workflow_by_document(self, db: AsyncSession, document_id: uuid.UUID) -> Optional[DbWorkflowDocument]:
        stmt = select(DbWorkflowDocument).where(DbWorkflowDocument.document_id == document_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
        
    async def get_or_create_workflow(self, db: AsyncSession, document_id: uuid.UUID) -> DbWorkflowDocument:
        workflow = await self.get_workflow_by_document(db, document_id)
        if workflow is None:
            workflow = DbWorkflowDocument(
                document_id=document_id,
                status="PENDING",
                progress=0,
                swd={}
            )
            db.add(workflow)
            await db.flush()
        return workflow

    async def get_workflow(self, db: AsyncSession, workflow_id: uuid.UUID) -> Optional[DbWorkflowDocument]:
        stmt = select(DbWorkflowDocument).where(DbWorkflowDocument.id == workflow_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_workflow_stage(
        self, 
        db: AsyncSession, 
        workflow_id: uuid.UUID, 
        stage: Optional[str] = None, 
        status: Optional[str] = None, 
        progress: Optional[int] = None
    ) -> Optional[DbWorkflowDocument]:
        workflow = await self.get_workflow(db, workflow_id)
        if workflow:
            if stage is not None:
                workflow.current_stage = stage
            if status is not None:
                workflow.status = status
            if progress is not None:
                workflow.progress = progress
            await db.flush()
        return workflow
        
    async def update_swd(
        self,
        db: AsyncSession,
        workflow_id: uuid.UUID,
        swd_updates: Dict[str, Any]
    ) -> Optional[DbWorkflowDocument]:
        workflow = await self.get_workflow(db, workflow_id)
        if workflow:
            # We copy the dictionary to ensure SQLAlchemy detects the JSONB change
            new_swd = dict(workflow.swd) if workflow.swd else {}
            new_swd.update(swd_updates)
            workflow.swd = new_swd
            await db.flush()
        return workflow

workflow_repository = SQLAlchemyWorkflowRepository()


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


class InMemoryWorkflowRepository:
    def __init__(self, documents: dict[UUID, SchemaWorkflowDocument] | None = None) -> None:
        self._documents: dict[UUID, SchemaWorkflowDocument] = documents or {}

    def seed(self, document: SchemaWorkflowDocument) -> None:
        self._documents[document.id] = document

    async def get(self, workflow_id: UUID) -> SchemaWorkflowDocument:
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
    ) -> SchemaWorkflowDocument:
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
    ) -> SchemaWorkflowDocument:
        current = self._documents[workflow_id]
        updated = current.model_copy(update={"status": status, "current_stage": current_stage})
        self._documents[workflow_id] = updated
        return updated.model_copy(deep=True)

    async def clear_human_approval(self, workflow_id: UUID, gate_name: str) -> SchemaWorkflowDocument:
        current = self._documents[workflow_id]
        remaining = {k: v for k, v in current.swd.human_approvals.items() if k != gate_name}
        swd = current.swd.model_copy(update={"human_approvals": remaining})
        updated = current.model_copy(update={"swd": swd})
        self._documents[workflow_id] = updated
        return updated.model_copy(deep=True)
