import asyncio
import traceback
import uuid
import logging
from .store import job_store
from app.modules.workflow.service import workflow_service
from app.core.db import AsyncSessionLocal
from app.core.config import settings

from app.ai.agents.extraction.agent import extraction_agent
from app.ai.agents.applicability.agent import applicability_agent
from app.ai.agents.ambiguity.agent import ambiguity_agent
from app.ai.agents.obligation.agent import obligation_agent
from app.ai.agents.task_generation.agent import task_generation_agent

logger = logging.getLogger(__name__)

async def run_pipeline(job_id: str, document_id: str):
    try:
        # 1. Regulatory Fetching & Ingestion Pipeline (Already done externally, data exists in data_dir)
        await job_store.update_status(job_id, "RUNNING", "Initializing", 10)
        
        data_dir = settings.DATA_DIR
        
        # 3. LLM Extraction
        await job_store.update_status(job_id, "RUNNING", "LLM Extraction", 20)
        semantic_objects = await extraction_agent.run(document_id, data_dir)
        
        # 4. Applicability Agent
        await job_store.update_status(job_id, "RUNNING", "Applicability Agent", 40)
        applicability = await applicability_agent.run(document_id, semantic_objects, data_dir)
        
        # 5. Ambiguity Agent
        await job_store.update_status(job_id, "RUNNING", "Ambiguity Agent", 55)
        ambiguity = await ambiguity_agent.run(document_id, semantic_objects, applicability, data_dir)
        
        # 6. Obligation Agent
        await job_store.update_status(job_id, "RUNNING", "Obligation Agent", 70)
        obligations = await obligation_agent.run(document_id, semantic_objects, applicability, ambiguity, data_dir)
        
        # Assign UUIDs to obligations so that tasks can reference them correctly
        for ob in obligations.obligations:
            ob.id = str(uuid.uuid4())
        
        # 7. Task Generation Agent
        await job_store.update_status(job_id, "RUNNING", "Task Generation Agent", 85)
        tasks = await task_generation_agent.run(document_id, obligations, data_dir)
        
        # Map the real Pydantic output back into the generic dictionary format 
        # that the frontend and persistence layers currently expect for the prototype.
        results = {
            "obligations": [ob.model_dump() for ob in obligations.obligations],
            "tasks": [t.model_dump() for t in tasks.tasks],
            "applicability": applicability.model_dump(),
            "ambiguity": ambiguity.model_dump()
        }
        
        # Keep the existing JSON/in-memory store logic for the UI
        await job_store.save_results(job_id, results)

        # ---------------------------------------------------------
        # PERSIST TO POSTGRESQL
        # ---------------------------------------------------------
        await job_store.update_status(job_id, "RUNNING", "Persisting to PostgreSQL", 95)
        async with AsyncSessionLocal() as db:
            try:
                await workflow_service.save_pipeline_results(db, document_id, results)
                await workflow_service.seed_swd_from_pipeline_results(db, document_id, results)
                
                try:
                    doc_uuid = uuid.UUID(document_id)
                except ValueError:
                    doc_uuid = uuid.uuid5(uuid.NAMESPACE_URL, document_id)
                from app.modules.workflow.repository import workflow_repository
                workflow = await workflow_repository.get_or_create_workflow(db, doc_uuid)
                
                await workflow_repository.update_workflow_stage(
                    db, workflow_id=workflow.id, status="pending_approval_1", stage="gate_1"
                )
                
                await db.commit()
            except Exception as e:
                await db.rollback()
                raise e
                
        await job_store.update_status(job_id, "COMPLETED", "Completed", 100)

    except Exception as e:
        logger.error(f"Pipeline failed: {e}\n{traceback.format_exc()}")
        await job_store.update_status(job_id, "FAILED", error=str(e))
