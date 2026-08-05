import logging
from typing import List

from app.scraper.sebi_scraper import SEBIScraper
from app.downloader.pdf_downloader import PDFDownloader
from app.modules.documents.repository import DocumentRepository
from app.modules.documents.service import DocumentService
from app.modules.documents.schemas import ChangeReport

logger = logging.getLogger(__name__)

def run_monitoring_cycle() -> ChangeReport:
    """
    Executes a full monitoring cycle:
    1. Scrape SEBI for latest circulars
    2. Load existing state
    3. Diff to find new/updated/removed
    4. Download new PDFs
    5. Save updated state and report
    """
    logger.info("Starting monitoring cycle")
    
    scraper = SEBIScraper()
    downloader = PDFDownloader()
    repo = DocumentRepository()
    service = DocumentService()
    
    # 1. Scrape
    scraped_data = scraper.scrape()
    if not scraped_data:
        logger.warning("Scraper returned no data. Aborting cycle.")
        # Create an empty report with error
        error_report = ChangeReport()
        error_report.errors.append("Scraper returned no data")
        repo.save_change_report(error_report)
        return error_report
        
    # 2. Load existing
    old_docs = repo.load_documents()
    
    # 3. Diff
    updated_docs, report = service.diff_documents(old_docs, scraped_data)
    
    # 4. Download PDFs for new/updated documents
    docs_to_download = report.new_documents + report.updated_documents
    
    for doc in docs_to_download:
        url_to_download = doc.pdf_url or doc.detail_url
        if url_to_download:
            local_path = downloader.download_pdf(doc.document_id, url_to_download)
            if local_path:
                doc.local_pdf_path = local_path
                report.downloaded_documents.append(doc)
            else:
                report.errors.append(f"Failed to download PDF for {doc.document_id}")
                
    # 5. Save state
    repo.save_documents(updated_docs)
    repo.save_change_report(report)
    
    logger.info(f"Monitoring cycle complete. New: {len(report.new_documents)}, Updated: {len(report.updated_documents)}, Removed: {len(report.removed_documents)}")
    return report

if __name__ == "__main__":
    # Manual run support
    from app.core.logging import setup_logging
    setup_logging()
    run_monitoring_cycle()
