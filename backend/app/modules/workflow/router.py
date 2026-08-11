from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, Optional
from uuid import UUID
from pydantic import BaseModel

from app.core.db import AsyncSessionLocal
from app.models.workflow_document import WorkflowDocument as DbWorkflowDocument
from app.models.regulatory_document import RegulatoryDocument
from app.modules.workflow.schemas import WorkflowDocument, SWDPayload
from app.modules.workflow.repository import workflow_repository
from app.core.config import settings
from sqlalchemy import select

router = APIRouter(prefix="/api/v1/workflows", tags=["workflows"])

def _db_to_schema(wf: DbWorkflowDocument) -> WorkflowDocument:
    """Convert a SQLAlchemy WorkflowDocument row to the Pydantic schema."""
    raw_swd = wf.swd if isinstance(wf.swd, dict) else {}
    swd = SWDPayload(
        document_metadata=raw_swd.get("document_metadata", {}),
        agent_outputs=raw_swd.get("agent_outputs", {}),
        human_approvals=raw_swd.get("human_approvals", {}),
        execution_history=raw_swd.get("execution_history", []),
        agent_tasks=raw_swd.get("agent_tasks", []),
    )
    return WorkflowDocument(
        id=wf.id,
        document_id=wf.document_id,
        organization_id=wf.organization_id,
        status=wf.status,
        current_stage=wf.current_stage or "",
        swd=swd,
        schema_version=wf.schema_version,
    )

# Dependency to get a db session
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

class CreateWorkflowRequest(BaseModel):
    document_id: str
    organization_id: Optional[UUID] = None

class WorkflowStatusResponse(BaseModel):
    workflow_id: UUID
    status: str
    current_stage: str
    has_agent_tasks: bool
    agent_tasks_count: int

class GateDecisionRequest(BaseModel):
    decision: str
    comment: Optional[str] = None
    approved_by: Optional[UUID] = None

@router.post("", response_model=WorkflowDocument)
async def create_workflow(request: CreateWorkflowRequest, db = Depends(get_db)):
    org_id = request.organization_id or UUID(settings.ORG_ID_DEFAULT)
    
    import uuid as _uuid
    try:
        doc_uuid = _uuid.UUID(request.document_id)
    except ValueError:
        doc_uuid = _uuid.uuid5(_uuid.NAMESPACE_URL, request.document_id)

    # Upsert a regulatory_documents row (FK requirement)
    # If the document_id string is not a real UUID we use it as a circular_number
    reg_doc = (await db.execute(
        select(RegulatoryDocument).where(RegulatoryDocument.id == doc_uuid)
    )).scalar_one_or_none()
    
    if reg_doc is None:
        reg_doc = RegulatoryDocument(
            id=doc_uuid,
            circular_number=request.document_id,
            title=f"Document {request.document_id}",
        )
        db.add(reg_doc)
        await db.flush()

    # create the workflow and seed with document metadata if needed
    wf = await workflow_repository.get_or_create_workflow(db, org_id, doc_uuid)
    await db.commit()
    await db.refresh(wf)
    return _db_to_schema(wf)

@router.get("/{workflow_id}", response_model=WorkflowDocument)
async def get_workflow(workflow_id: UUID, db = Depends(get_db)):
    wf = await workflow_repository.get_workflow(db, workflow_id)
    if not wf:
        raise HTTPException(404, detail="Workflow not found")
    return _db_to_schema(wf)

@router.get("/{workflow_id}/status", response_model=WorkflowStatusResponse)
async def get_workflow_status(workflow_id: UUID, db = Depends(get_db)):
    wf = await workflow_repository.get_workflow(db, workflow_id)
    if not wf:
        raise HTTPException(404, detail="Workflow not found")
    swd = wf.swd if isinstance(wf.swd, dict) else (wf.swd.model_dump() if hasattr(wf.swd, "model_dump") else {})
    agent_tasks = swd.get("agent_tasks", [])
    return WorkflowStatusResponse(
        workflow_id=wf.id,
        status=wf.status,
        current_stage=wf.current_stage or "",
        has_agent_tasks=bool(agent_tasks),
        agent_tasks_count=len(agent_tasks),
    )

@router.get("/{workflow_id}/agent-output/{agent_name}")
async def get_agent_output(workflow_id: UUID, agent_name: str, db = Depends(get_db)):
    wf = await workflow_repository.get_workflow(db, workflow_id)
    if not wf:
        raise HTTPException(404, detail="Workflow not found")
    swd = wf.swd if isinstance(wf.swd, dict) else (wf.swd.model_dump() if hasattr(wf.swd, "model_dump") else {})
    output = swd.get("agent_outputs", {}).get(agent_name)
    if output is None:
        raise HTTPException(404, detail=f"Agent output for '{agent_name}' not found")
    return output

@router.post("/{workflow_id}/gate/{gate_name}")
async def submit_gate_decision(
    workflow_id: UUID, 
    gate_name: str, 
    request: GateDecisionRequest, 
    db = Depends(get_db)
):
    wf = await workflow_repository.get_workflow(db, workflow_id)
    if not wf:
        raise HTTPException(404, detail="Workflow not found")

    from app.ai.graph.runner import invoke_graph, resume_graph
    import asyncio

    # Record the gate approval in the SWD via workflow_repository
    swd_updates = {
        "human_approvals": {
            gate_name: {
                "decision": request.decision,
                "comment": request.comment,
                "approved_by": str(request.approved_by) if request.approved_by else None,
            }
        }
    }
    await workflow_repository.update_swd(db, workflow_id, swd_updates)
    await db.commit()

    if gate_name == "gate_1" and request.decision == "approved":
        # Start the graph in the background
        asyncio.create_task(invoke_graph(workflow_id, wf.organization_id))
        return {"workflow_id": workflow_id, "status": "impact_mapping", "message": "Impact mapping pipeline started."}
    elif gate_name == "gate_2":
        # Resume the paused graph
        asyncio.create_task(resume_graph(workflow_id, gate_name, request.decision, request.comment))
        return {"workflow_id": workflow_id, "status": "executing", "message": "Execution pipeline resuming."}

    return {"workflow_id": workflow_id, "status": wf.status, "message": "Gate decision recorded."}
