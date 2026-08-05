from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict, Any
import os

from app.modules.documents.schemas import CircularResponse, ChangeReport, DownloadInfo
from app.modules.documents.repository import DocumentRepository
from app.modules.documents.service import DocumentService
from app.core.config import settings
from app.workers import monitor

router = APIRouter(prefix="/api", tags=["documents"])
repo = DocumentRepository()
service = DocumentService()

@router.get("/circulars", response_model=List[CircularResponse])
async def get_circulars():
    """Returns all circulars mapped to the frontend's expected format."""
    docs = repo.load_documents()
    return [service.map_to_circular_response(doc) for doc in docs]

@router.get("/changes", response_model=ChangeReport)
async def get_changes():
    """Returns the most recent change report."""
    report = repo.load_change_report()
    if not report:
        raise HTTPException(status_code=404, detail="No change report found")
    return report

@router.post("/check-updates", response_model=Dict[str, Any])
async def check_updates(background_tasks: BackgroundTasks):
    """
    Triggers a scraping and diffing cycle.
    In a real system this might be fully async, but for phase 1 we'll run it and return status.
    """
    try:
        # We can either run it synchronously or in the background. 
        # Running sync for simplicity of testing in Phase 1, but we can move to background later.
        report = monitor.run_monitoring_cycle()
        return {
            "status": "success", 
            "message": "Update check completed", 
            "new_count": len(report.new_documents),
            "updated_count": len(report.updated_documents)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/downloads", response_model=List[DownloadInfo])
async def list_downloads():
    """Lists all downloaded PDF files."""
    downloads = []
    if os.path.exists(settings.DOWNLOADS_DIR):
        for filename in os.listdir(settings.DOWNLOADS_DIR):
            if filename.endswith(".pdf"):
                filepath = os.path.join(settings.DOWNLOADS_DIR, filename)
                size = os.path.getsize(filepath)
                downloads.append(DownloadInfo(filename=filename, path=filepath, size_bytes=size))
    return downloads

@router.get("/status")
async def get_status():
    """Returns system status."""
    docs = repo.load_documents()
    return {
        "status": "healthy",
        "document_count": len(docs),
        "service": settings.APP_NAME
    }
