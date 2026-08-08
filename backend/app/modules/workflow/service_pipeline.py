from __future__ import annotations

import uuid
from typing import Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.workflow.repository_sql import workflow_repository
from app.modules.obligations.repository import obligation_repository
from app.modules.tasks.repository import task_repository

class PipelineWorkflowService:
    async def save_pipeline_results(self, db: AsyncSession, document_id: str, results: Dict[str, Any]):
        """
        Saves the pipeline results (obligations, tasks, applicability, ambiguity)
        to the database within a single transaction context.
        """
        try:
            doc_uuid = uuid.UUID(document_id)
        except ValueError:
            doc_uuid = uuid.uuid5(uuid.NAMESPACE_URL, document_id)
        
        # Org ID should be passed in a real system, but for pipeline runner mock we use a default
        org_id = uuid.UUID('00000000-0000-0000-0000-000000000001')
        
        # 1. Get or create workflow document
        workflow = await workflow_repository.get_or_create_workflow(db, org_id, doc_uuid)
        
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

    async def seed_swd_from_pipeline_results(self, db: AsyncSession, document_id: str, results: Dict[str, Any]):
        """
        Bridges the pipeline results into the SWD fields expected by the LangGraph agents.
        """
        try:
            doc_uuid = uuid.UUID(document_id)
        except ValueError:
            doc_uuid = uuid.uuid5(uuid.NAMESPACE_URL, document_id)
            
        org_id = uuid.UUID('00000000-0000-0000-0000-000000000001')
        workflow = await workflow_repository.get_or_create_workflow(db, org_id, doc_uuid)
        
        swd_updates = {}
        # Seed applicability into document_metadata
        if "applicability" in results:
            swd_updates["document_metadata"] = {"applicability": results["applicability"]}
            
        # Seed agents
        agent_outputs = {}
        if "obligations" in results:
            agent_outputs["obligation_extraction_agent"] = {"obligations": results["obligations"]}
        if "ambiguity" in results:
            agent_outputs["ambiguity_detection_agent"] = results["ambiguity"]
            
        if agent_outputs:
            swd_updates["agent_outputs"] = agent_outputs
            
        if swd_updates:
            await workflow_repository.update_swd(db, workflow.id, swd_updates)

    async def update_status(self, db: AsyncSession, document_id: str, stage: str, status: str, progress: int):
        """
        Updates the pipeline status.
        """
        try:
            doc_uuid = uuid.UUID(document_id)
        except ValueError:
            doc_uuid = uuid.uuid5(uuid.NAMESPACE_URL, document_id)
            
        org_id = uuid.UUID('00000000-0000-0000-0000-000000000001')
        workflow = await workflow_repository.get_or_create_workflow(db, org_id, doc_uuid)
        await workflow_repository.update_workflow_stage(db, workflow.id, stage=stage, status=status, progress=progress)

pipeline_workflow_service = PipelineWorkflowService()
