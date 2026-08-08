import uuid
from typing import Any, Dict, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.workflow_document import WorkflowDocument, WorkflowStatus

class WorkflowRepository:
    
    async def get_workflow_by_document(self, db: AsyncSession, document_id: uuid.UUID) -> Optional[WorkflowDocument]:
        stmt = select(WorkflowDocument).where(WorkflowDocument.document_id == document_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
        
    async def get_or_create_workflow(self, db: AsyncSession, document_id: uuid.UUID) -> WorkflowDocument:
        workflow = await self.get_workflow_by_document(db, document_id)
        if workflow is None:
            workflow = WorkflowDocument(
                document_id=document_id,
                status="PENDING",
                progress=0,
                swd={}
            )
            db.add(workflow)
            await db.flush()
        return workflow

    async def get_workflow(self, db: AsyncSession, workflow_id: uuid.UUID) -> Optional[WorkflowDocument]:
        stmt = select(WorkflowDocument).where(WorkflowDocument.id == workflow_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_workflow_stage(
        self, 
        db: AsyncSession, 
        workflow_id: uuid.UUID, 
        stage: Optional[str] = None, 
        status: Optional[str] = None, 
        progress: Optional[int] = None
    ) -> Optional[WorkflowDocument]:
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
    ) -> Optional[WorkflowDocument]:
        workflow = await self.get_workflow(db, workflow_id)
        if workflow:
            # We copy the dictionary to ensure SQLAlchemy detects the JSONB change
            new_swd = dict(workflow.swd) if workflow.swd else {}
            new_swd.update(swd_updates)
            workflow.swd = new_swd
            await db.flush()
        return workflow

workflow_repository = WorkflowRepository()
