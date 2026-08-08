from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime

# Domain model for stored documents (documents.json)
class Document(BaseModel):
    document_id: str
    title: str
    type: str = Field(alias="category")
    publication_date: str
    status: Literal["new", "existing", "updated", "removed"] = "existing"
    pdf_url: Optional[str] = None
    detail_url: Optional[str] = None
    local_pdf_path: Optional[str] = None
    
    class Config:
        populate_by_name = True

# API Response Models (Matching Frontend)
class CircularResponse(BaseModel):
    id: str
    reference: str
    title: str
    summary: str
    source: Literal["SEBI", "RBI", "IRDAI", "MCA", "FIU"]
    receivedAt: str
    stage: Literal["RECEIVED", "ANALYSING", "AWAITING_APPROVAL", "IMPLEMENTATION", "MONITORING"]
    processingStatus: Literal["Analyzing", "Flagged", "Completed", "Pending"]
    risk: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    owner: Optional[str] = None

# Change Report Models
class ChangeReport(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    new_documents: List[Document] = []
    updated_documents: List[Document] = []
    superseded_documents: List[Document] = []
    removed_documents: List[Document] = []
    downloaded_documents: List[Document] = []
    errors: List[str] = []

class DownloadInfo(BaseModel):
    filename: str
    path: str
    size_bytes: int
