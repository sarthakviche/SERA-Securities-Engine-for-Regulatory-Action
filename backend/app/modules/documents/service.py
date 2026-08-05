import logging
from typing import List, Dict, Any, Tuple
from datetime import datetime
import uuid

from app.modules.documents.schemas import Document, ChangeReport, CircularResponse

logger = logging.getLogger(__name__)

class DocumentService:
    @staticmethod
    def calculate_risk(title: str, category: str) -> str:
        """Heuristic-based risk calculation."""
        title_lower = title.lower()
        category_lower = category.lower()
        
        # High Risk Keywords
        high_risk_keywords = ["cybersecurity", "fraud", "penalty", "violation", "breach", "strict"]
        if any(kw in title_lower for kw in high_risk_keywords):
            return "HIGH"
            
        # Medium Risk Keywords
        if "master circular" in title_lower or "guidelines" in title_lower:
            return "MEDIUM"
            
        # Default
        return "LOW"

    @staticmethod
    def map_to_circular_response(doc: Document) -> CircularResponse:
        """Maps a Document to the CircularResponse shape expected by the frontend."""
        
        # Map statuses based on backend state
        stage = "RECEIVED"
        processing_status = "Pending"
        
        if doc.status == "new":
            stage = "RECEIVED"
            processing_status = "Analyzing"
        elif doc.status == "updated":
            stage = "ANALYSING"
            processing_status = "Flagged"
        elif doc.status == "existing":
            # For mockup purposes, existing documents might be further along
            stage = "MONITORING"
            processing_status = "Completed"

        return CircularResponse(
            id=doc.document_id,
            reference=doc.document_id, # Fallback to document_id if ref is not distinct
            title=doc.title,
            summary=f"Category: {doc.type}. Published: {doc.publication_date}",
            source="SEBI",
            receivedAt=datetime.utcnow().isoformat(), # Ideally this is when it was first seen
            stage=stage,
            processingStatus=processing_status,
            risk=DocumentService.calculate_risk(doc.title, doc.type),
            owner="System"
        )

    def diff_documents(self, old_docs: List[Document], scraped_data: List[Dict[str, Any]]) -> Tuple[List[Document], ChangeReport]:
        """
        Compares old stored documents with newly scraped data.
        Returns the updated complete list of documents and a ChangeReport.
        """
        old_doc_map = {doc.document_id: doc for doc in old_docs}
        new_doc_map = {}
        
        report = ChangeReport()
        updated_docs = []
        
        for data in scraped_data:
            doc_id = data.get("reference")
            if not doc_id:
                 continue
                 
            new_doc = Document(
                document_id=doc_id,
                title=data.get("title", ""),
                category=data.get("category", ""),
                publication_date=data.get("publication_date", ""),
                pdf_url=data.get("pdf_url"),
                detail_url=data.get("detail_url")
            )
            
            new_doc_map[doc_id] = new_doc
            
            if doc_id not in old_doc_map:
                # Completely new document
                new_doc.status = "new"
                report.new_documents.append(new_doc)
            else:
                old_doc = old_doc_map[doc_id]
                # Check for updates (e.g., title change, category change)
                if old_doc.title != new_doc.title or old_doc.type != new_doc.type:
                    new_doc.status = "updated"
                    report.updated_documents.append(new_doc)
                else:
                    new_doc.status = "existing"
                    
                # Preserve local path if it exists
                new_doc.local_pdf_path = old_doc.local_pdf_path
                    
            updated_docs.append(new_doc)
            
        # Detect removed documents
        for doc_id, old_doc in old_doc_map.items():
            if doc_id not in new_doc_map:
                old_doc.status = "removed"
                report.removed_documents.append(old_doc)
                # We might want to keep it in the DB but marked as removed, 
                # but for simplicity in this diff we just append it with 'removed' status
                updated_docs.append(old_doc)
                
        return updated_docs, report
