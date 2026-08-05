import os
import requests
import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re

from app.core.config import settings
from app.scraper.retry import retry

logger = logging.getLogger(__name__)

class PDFDownloader:
    def __init__(self):
        self.download_dir = settings.DOWNLOADS_DIR
        self.timeout = (settings.HTTP_TIMEOUT_CONNECT, settings.HTTP_TIMEOUT_READ)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def _sanitize_filename(self, reference: str) -> str:
        """
        Converts a reference like 'SEBI-CIRC-2026-08-03-103314' into a safe
        filename: 'SEBI-CIRC-2026-08-03-103314.pdf'
        Strips any characters that are not alphanumeric or hyphens.
        """
        safe_name = re.sub(r"[^a-zA-Z0-9\-]", "-", reference)
        # Collapse multiple consecutive hyphens
        safe_name = re.sub(r"-{2,}", "-", safe_name).strip("-")
        return f"{safe_name}.pdf"

    def _extract_pdf_url_from_detail_page(self, detail_url: str) -> str | None:
        """
        SEBI circular detail pages embed the PDF inside an <iframe>, not as a
        direct <a href> link. This function fetches the detail page and checks:
          1. <iframe src="...?file=https://...sebi_data/...pdf"> (primary pattern)
          2. <a href="...pdf"> links (fallback for older pages)
        Returns the absolute PDF URL if found, else None.
        """
        try:
            response = requests.get(detail_url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")

            # Primary: SEBI embeds PDFs in an iframe whose src contains a ?file= param
            # e.g. src="../../../web/?file=https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/xyz.pdf"
            for iframe in soup.find_all("iframe", src=True):
                src = iframe["src"]
                # Extract the ?file= value which is the real PDF URL
                if "sebi_data" in src and ".pdf" in src.lower():
                    # The URL is everything after "?file="
                    if "?file=" in src:
                        pdf_url = src.split("?file=")[-1]
                    else:
                        # Could be a direct iframe src pointing at the PDF
                        pdf_url = urljoin(detail_url, src)
                    logger.info(f"Found PDF via iframe: {pdf_url}")
                    return pdf_url

            # Fallback: look for <a href="...pdf"> links (older SEBI pages)
            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]
                if href.lower().endswith(".pdf"):
                    pdf_url = urljoin(detail_url, href)
                    logger.info(f"Found PDF via anchor link: {pdf_url}")
                    return pdf_url

            logger.warning(f"Could not find PDF link on detail page: {detail_url}")
            return None
        except Exception as e:
            logger.error(f"Error extracting PDF from detail page {detail_url}: {e}")
            return None

    @retry(max_retries=settings.SCRAPER_MAX_RETRIES, base_delay=settings.SCRAPER_RETRY_DELAY, exceptions=(requests.RequestException,))
    def download_pdf(self, reference: str, pdf_or_detail_url: str) -> str | None:
        """
        Downloads a PDF file for a given circular reference.
        Returns the local filepath if successful or already exists, None if failed.
        """
        if not pdf_or_detail_url:
            logger.warning(f"No URL provided for {reference}")
            return None
            
        filename = self._sanitize_filename(reference)
        filepath = os.path.join(self.download_dir, filename)
        
        # Idempotent: skip if already downloaded
        if os.path.exists(filepath):
            logger.info(f"PDF for {reference} already exists at {filepath}")
            return filepath
            
        # Determine actual PDF URL
        actual_pdf_url = pdf_or_detail_url
        if not pdf_or_detail_url.lower().endswith('.pdf'):
            logger.info(f"URL for {reference} might be a detail page. Attempting to extract PDF link...")
            extracted_url = self._extract_pdf_url_from_detail_page(pdf_or_detail_url)
            if extracted_url:
                actual_pdf_url = extracted_url
            else:
                logger.error(f"Could not resolve actual PDF URL for {reference}")
                return None
                
        logger.info(f"Downloading PDF for {reference} from {actual_pdf_url}")
        
        try:
            # Stream the download to handle large files
            with requests.get(actual_pdf_url, headers=self.headers, stream=True, timeout=self.timeout) as response:
                response.raise_for_status()
                
                # Check Content-Type just to be safe
                content_type = response.headers.get('content-type', '')
                if 'pdf' not in content_type.lower() and 'application/octet-stream' not in content_type.lower():
                     logger.warning(f"Downloaded content for {reference} might not be a PDF. Content-Type: {content_type}")
                
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                        
            logger.info(f"Successfully downloaded {reference} to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to download PDF for {reference}: {e}", exc_info=True)
            # Clean up partial file if it exists
            if os.path.exists(filepath):
                os.remove(filepath)
            return None
