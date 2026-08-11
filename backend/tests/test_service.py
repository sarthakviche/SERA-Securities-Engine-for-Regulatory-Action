import pytest
from app.modules.documents.service import DocumentService
from app.modules.documents.schemas import Document

@pytest.fixture
def service():
    return DocumentService()

def test_calculate_risk(service):
    assert service.calculate_risk("Severe penalty for cybersecurity breach", "General") == "HIGH"
    assert service.calculate_risk("Master Circular for Brokers", "Intermediaries") == "MEDIUM"
    assert service.calculate_risk("Routine update on holidays", "General") == "LOW"

def test_diff_documents_new(service):
    old_docs = []
    scraped_data = [
        {"reference": "REF1", "title": "New Doc", "category": "Test", "publication_date": "2026-01-01"}
    ]
    
    updated, report = service.diff_documents(old_docs, scraped_data)
    
    assert len(updated) == 1
    assert updated[0].status == "new"
    
    assert len(report.new_documents) == 1
    assert report.new_documents[0].document_id == "REF1"
    assert len(report.updated_documents) == 0
    assert len(report.removed_documents) == 0

def test_diff_documents_updated(service):
    old_docs = [
        Document(document_id="REF1", title="Old Title", category="Test", publication_date="2026-01-01", status="existing")
    ]
    scraped_data = [
        {"reference": "REF1", "title": "New Title", "category": "Test", "publication_date": "2026-01-01"}
    ]
    
    updated, report = service.diff_documents(old_docs, scraped_data)
    
    assert len(updated) == 1
    assert updated[0].status == "updated"
    assert updated[0].title == "New Title"
    
    assert len(report.updated_documents) == 1
    assert len(report.new_documents) == 0

def test_diff_documents_removed(service):
    old_docs = [
        Document(document_id="REF1", title="Doc to remove", category="Test", publication_date="2026-01-01", status="existing")
    ]
    scraped_data = []
    
    updated, report = service.diff_documents(old_docs, scraped_data)
    
    assert len(updated) == 1
    assert updated[0].status == "removed"
    
    assert len(report.removed_documents) == 1
