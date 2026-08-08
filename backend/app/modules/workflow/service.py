"""Workflow Service — merged implementation containing both HEAD methods and their methods."""

from __future__ import annotations

import uuid
from typing import Dict, Any
from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.workflow.repository import workflow_repository, WorkflowRepository
from app.modules.obligations.repository import obligation_repository
from app.modules.tasks.repository import task_repository

from app.modules.workflow.schemas import (
    AgentTask,
    ExecutionHistoryEntry,
    GateApproval,
    SWDPayload,
    WorkflowDocument,
    WorkflowStatus,
)


class WorkflowService:
    def __init__(self, repository: WorkflowRepository | None = None) -> None:
        self._repository = repository

    async def save_pipeline_results(self, db: AsyncSession, document_id: str, results: Dict[str, Any]):
        """
        Saves the pipeline results (obligations, tasks, applicability, ambiguity)
        to the database within a single transaction context.
        """
        try:
            doc_uuid = uuid.UUID(document_id)
        except ValueError:
            doc_uuid = uuid.uuid5(uuid.NAMESPACE_URL, document_id)
        
        # 1. Get or create workflow document
        workflow = await workflow_repository.get_or_create_workflow(db, doc_uuid)
        
        # 2. Update SWD with applicability and ambiguity
        swd_updates = {}
        if "applicability" in results:
            swd_updates["applicability"] = results["applicability"]
        if "ambiguity" in results:
            swd_updates["ambiguity"] = results["ambiguity"]
            
        if swd_updates:
            await workflow_repository.update_swd(db, workflow.id, swd_updates)
            
        # 3. Upsert obligations
        if "obligations" in results:
            await obligation_repository.upsert_obligations(db, workflow.id, results["obligations"])
            
        # 4. Upsert tasks
        if "tasks" in results:
            await task_repository.upsert_tasks(db, workflow.id, results["tasks"])
            
        # The calling code (router or orchestrator) must call db.commit() to finalize.

    async def update_status(self, db: AsyncSession, document_id: str, stage: str, status: str, progress: int):
        """
        Updates the pipeline status.
        """
        try:
            doc_uuid = uuid.UUID(document_id)
        except ValueError:
            doc_uuid = uuid.uuid5(uuid.NAMESPACE_URL, document_id)
            
        workflow = await workflow_repository.get_or_create_workflow(db, doc_uuid)
        await workflow_repository.update_workflow_stage(db, workflow.id, stage=stage, status=status, progress=progress)

    # Agent node contract methods
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

workflow_service = WorkflowService()
