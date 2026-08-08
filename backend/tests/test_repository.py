import pytest
import os
import tempfile
from unittest.mock import patch
from app.modules.documents.repository import DocumentRepository
from app.modules.documents.schemas import Document, ChangeReport

@pytest.fixture
def repo():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Override settings for tests
        with patch('app.modules.documents.repository.settings.DOCUMENTS_FILE', os.path.join(tmpdir, "docs.json")), \
             patch('app.modules.documents.repository.settings.CHANGE_REPORT_FILE', os.path.join(tmpdir, "report.json")):
            yield DocumentRepository()

def test_save_and_load_documents(repo):
    # Should start empty
    assert repo.load_documents() == []
    
    docs = [
        Document(
            document_id="DOC1",
            title="Test Doc",
            category="Test",
            publication_date="2026-01-01",
            status="new"
        )
    ]
    
    repo.save_documents(docs)
    
    loaded = repo.load_documents()
    assert len(loaded) == 1
    assert loaded[0].document_id == "DOC1"
    assert loaded[0].status == "new"

def test_save_and_load_change_report(repo):
    assert repo.load_change_report() is None
    
    report = ChangeReport()
    report.errors.append("Test error")
    
    repo.save_change_report(report)
    
    loaded = repo.load_change_report()
    assert loaded is not None
    assert len(loaded.errors) == 1
    assert loaded.errors[0] == "Test error"
