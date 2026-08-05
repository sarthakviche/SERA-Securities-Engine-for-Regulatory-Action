import pytest
from unittest.mock import patch, MagicMock
from app.workers.monitor import run_monitoring_cycle
from app.modules.documents.schemas import Document

@patch('app.workers.monitor.SEBIScraper')
@patch('app.workers.monitor.PDFDownloader')
@patch('app.workers.monitor.DocumentRepository')
def test_run_monitoring_cycle_success(mock_repo_class, mock_downloader_class, mock_scraper_class):
    mock_scraper = mock_scraper_class.return_value
    mock_downloader = mock_downloader_class.return_value
    mock_repo = mock_repo_class.return_value
    
    # Setup mock returns
    mock_scraper.scrape.return_value = [
        {"reference": "REF1", "title": "New", "category": "Cat", "publication_date": "2026-01-01", "pdf_url": "http://test.pdf"}
    ]
    
    mock_repo.load_documents.return_value = []
    mock_downloader.download_pdf.return_value = "/local/path/REF1.pdf"
    
    # Run cycle
    report = run_monitoring_cycle()
    
    # Asserts
    mock_scraper.scrape.assert_called_once()
    mock_repo.load_documents.assert_called_once()
    mock_downloader.download_pdf.assert_called_once_with("REF1", "http://test.pdf")
    mock_repo.save_documents.assert_called_once()
    mock_repo.save_change_report.assert_called_once()
    
    assert len(report.new_documents) == 1
    assert len(report.downloaded_documents) == 1
    
@patch('app.workers.monitor.SEBIScraper')
@patch('app.workers.monitor.DocumentRepository')
def test_run_monitoring_cycle_no_data(mock_repo_class, mock_scraper_class):
    mock_scraper = mock_scraper_class.return_value
    mock_repo = mock_repo_class.return_value
    
    mock_scraper.scrape.return_value = []
    
    report = run_monitoring_cycle()
    
    mock_scraper.scrape.assert_called_once()
    mock_repo.load_documents.assert_not_called()
    mock_repo.save_change_report.assert_called_once()
    
    assert len(report.errors) > 0
