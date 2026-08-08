from fastapi import APIRouter, BackgroundTasks, HTTPException
from .schemas import PipelineResponse, PipelineStatus, PipelineResult
from .store import job_store
from .runner import run_pipeline

router = APIRouter(prefix="/api/v1/pipeline", tags=["pipeline"])

@router.post("/process/{document_id}", response_model=PipelineResponse)
async def process_document(document_id: str, background_tasks: BackgroundTasks):
    job_id = await job_store.create_job(document_id)
    background_tasks.add_task(run_pipeline, job_id, document_id)
    return PipelineResponse(job_id=job_id, message="Pipeline started successfully")

@router.get("/jobs/{job_id}", response_model=PipelineStatus)
async def get_job_status(job_id: str):
    status = await job_store.get_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    return status

@router.get("/results/{job_id}", response_model=PipelineResult)
async def get_job_results(job_id: str):
    results = await job_store.get_results(job_id)
    if not results:
        raise HTTPException(status_code=404, detail="Results not found")
    return results
