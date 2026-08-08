from pydantic import BaseModel
from typing import Optional, Any, Dict, List

class PipelineStatus(BaseModel):
    job_id: str
    document_id: str
    status: str  # PENDING, RUNNING, COMPLETED, FAILED
    current_stage: Optional[str] = None
    progress: int = 0
    error: Optional[str] = None

class PipelineResponse(BaseModel):
    job_id: str
    message: str

class PipelineResult(BaseModel):
    job_id: str
    document_id: str
    obligations: List[Dict[str, Any]] = []
    tasks: List[Dict[str, Any]] = []
    applicability: Dict[str, Any] = {}
    ambiguity: Dict[str, Any] = {}
