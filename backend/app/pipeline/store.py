from typing import Dict, Any
import asyncio
from .schemas import PipelineStatus, PipelineResult

class JobStore:
    def __init__(self):
        self._jobs: Dict[str, PipelineStatus] = {}
        self._results: Dict[str, PipelineResult] = {}
        self._lock = asyncio.Lock()

    async def create_job(self, document_id: str) -> str:
        import uuid
        job_id = str(uuid.uuid4())
        async with self._lock:
            self._jobs[job_id] = PipelineStatus(
                job_id=job_id,
                document_id=document_id,
                status="PENDING",
            )
            self._results[job_id] = PipelineResult(
                job_id=job_id,
                document_id=document_id
            )
        return job_id

    async def get_status(self, job_id: str) -> PipelineStatus:
        async with self._lock:
            return self._jobs.get(job_id)

    async def update_status(self, job_id: str, status: str, current_stage: str = None, progress: int = None, error: str = None):
        async with self._lock:
            job = self._jobs.get(job_id)
            if job:
                job.status = status
                if current_stage is not None:
                    job.current_stage = current_stage
                if progress is not None:
                    job.progress = progress
                if error is not None:
                    job.error = error

    async def save_results(self, job_id: str, results: dict):
        async with self._lock:
            job_result = self._results.get(job_id)
            if job_result:
                if "obligations" in results:
                    job_result.obligations = results["obligations"]
                if "tasks" in results:
                    job_result.tasks = results["tasks"]
                if "applicability" in results:
                    job_result.applicability = results["applicability"]
                if "ambiguity" in results:
                    job_result.ambiguity = results["ambiguity"]

    async def get_results(self, job_id: str) -> PipelineResult:
        async with self._lock:
            return self._results.get(job_id)

job_store = JobStore()
