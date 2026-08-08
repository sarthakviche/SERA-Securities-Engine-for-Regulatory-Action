from __future__ import annotations

import copy
import uuid
from typing import Any, Dict, Optional
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
    def __init__(self, db: AsyncSession | None = None) -> None:
        self.db = db

    async def get_workflow_by_document(self, db: AsyncSession, document_id: uuid.UUID) -> Optional[DbWorkflowDocument]:
        stmt = select(DbWorkflowDocument).where(DbWorkflowDocument.document_id == document_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
        
    async def get_or_create_workflow(self, db: AsyncSession, organization_id: uuid.UUID, document_id: uuid.UUID) -> DbWorkflowDocument:
        workflow = await self.get_workflow_by_document(db, document_id)
        if workflow is None:
            workflow = DbWorkflowDocument(
                organization_id=organization_id,
                document_id=document_id,
                status="created",
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

    # --- Agent Protocol Methods ---
    # These rely on self.db being set

    async def get(self, workflow_id: UUID) -> SchemaWorkflowDocument:
        if not self.db:
            raise RuntimeError("Database session not initialized")
        workflow = await self.get_workflow(self.db, workflow_id)
        if not workflow:
            raise KeyError(f"workflow_document {workflow_id} not found")
        
        swd = workflow.swd or {}
        return SchemaWorkflowDocument(
            id=workflow.id,
            document_id=workflow.document_id,
            organization_id=workflow.organization_id,
            status=workflow.status,
            current_stage=workflow.current_stage or "",
            swd=swd
        )

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
        if not self.db:
            raise RuntimeError("Database session not initialized")
            
        workflow = await self.get_workflow(self.db, workflow_id)
        if not workflow:
            raise KeyError(f"workflow_document {workflow_id} not found")
            
        swd = dict(workflow.swd) if workflow.swd else {}
        
        if agent_outputs is not None:
            existing = dict(swd.get("agent_outputs", {}))
            existing.update(agent_outputs)
            swd["agent_outputs"] = existing

        if human_approvals is not None:
            existing = dict(swd.get("human_approvals", {}))
            # Convert GateApproval objects to dicts for JSONB
            approvals_dict = {k: v.model_dump(mode="json") if hasattr(v, "model_dump") else v for k, v in human_approvals.items()}
            existing.update(approvals_dict)
            swd["human_approvals"] = existing

        if execution_history is not None:
            swd["execution_history"] = [e.model_dump(mode="json") if hasattr(e, "model_dump") else e for e in execution_history]

        if agent_tasks is not None:
            swd["agent_tasks"] = [t.model_dump(mode="json") if hasattr(t, "model_dump") else t for t in agent_tasks]

        if document_metadata is not None:
            existing = dict(swd.get("document_metadata", {}))
            existing.update(document_metadata)
            swd["document_metadata"] = existing

        workflow.swd = swd
        await self.db.flush()
        
        return SchemaWorkflowDocument(
            id=workflow.id,
            document_id=workflow.document_id,
            organization_id=workflow.organization_id,
            status=workflow.status,
            current_stage=workflow.current_stage or "",
            swd=workflow.swd
        )

    async def update_status(
        self, workflow_id: UUID, status: WorkflowStatus, current_stage: str
    ) -> SchemaWorkflowDocument:
        if not self.db:
            raise RuntimeError("Database session not initialized")
            
        workflow = await self.get_workflow(self.db, workflow_id)
        if not workflow:
            raise KeyError(f"workflow_document {workflow_id} not found")
            
        workflow.status = status
        workflow.current_stage = current_stage
        await self.db.flush()
        
        return SchemaWorkflowDocument(
            id=workflow.id,
            document_id=workflow.document_id,
            organization_id=workflow.organization_id,
            status=workflow.status,
            current_stage=workflow.current_stage or "",
            swd=workflow.swd or {}
        )

    async def clear_human_approval(self, workflow_id: UUID, gate_name: str) -> SchemaWorkflowDocument:
        if not self.db:
            raise RuntimeError("Database session not initialized")
            
        workflow = await self.get_workflow(self.db, workflow_id)
        if not workflow:
            raise KeyError(f"workflow_document {workflow_id} not found")
            
        swd = dict(workflow.swd) if workflow.swd else {}
        if "human_approvals" in swd and gate_name in swd["human_approvals"]:
            del swd["human_approvals"][gate_name]
            workflow.swd = swd
            await self.db.flush()
            
        return SchemaWorkflowDocument(
            id=workflow.id,
            document_id=workflow.document_id,
            organization_id=workflow.organization_id,
            status=workflow.status,
            current_stage=workflow.current_stage or "",
            swd=workflow.swd or {}
        )


workflow_repository = SQLAlchemyWorkflowRepository()
