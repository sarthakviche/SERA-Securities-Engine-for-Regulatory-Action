import requests
from bs4 import BeautifulSoup
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.core.config import settings
from app.scraper.retry import retry

logger = logging.getLogger(__name__)

class SEBIScraper:
    def __init__(self):
        self.base_url = settings.SEBI_BASE_URL
        self.circulars_url = settings.SEBI_CIRCULARS_URL
        self.timeout = (settings.HTTP_TIMEOUT_CONNECT, settings.HTTP_TIMEOUT_READ)
        # Use a standard user agent to avoid basic blocking
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    @retry(max_retries=settings.SCRAPER_MAX_RETRIES, base_delay=settings.SCRAPER_RETRY_DELAY, exceptions=(requests.RequestException,))
    def fetch_circulars_page(self) -> str:
        """Fetches the HTML content of the SEBI circulars page."""
        logger.info(f"Fetching SEBI circulars from {self.circulars_url}")
        response = requests.get(
            self.circulars_url, 
            headers=self.headers, 
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.text

    def parse_date(self, date_str: str) -> str:
        """Parses SEBI date format (e.g., 'Jul 14, 2026') to ISO 8601 (YYYY-MM-DD)."""
        try:
            # Try to parse the date, removing any extra whitespace
            dt = datetime.strptime(date_str.strip(), "%b %d, %Y")
            return dt.strftime("%Y-%m-%d")
        except ValueError as e:
            logger.warning(f"Could not parse date '{date_str}': {e}")
            return date_str.strip()

    def scrape(self) -> List[Dict[str, Any]]:
        """
        Scrapes the SEBI circulars page and returns a list of dictionaries containing metadata.
        Returns empty list on failure.
        """
        try:
            html_content = self.fetch_circulars_page()
            soup = BeautifulSoup(html_content, "lxml")
            
            scraped_data = []
            
            # The data is typically in a table format. We need to find the specific table rows.
            # On the provided SEBI URL structure, the table is usually within a specific div or id.
            # Using a generic approach based on standard HTML table structures for this initial implementation.
            # If SEBI changes their DOM, this will need an update.
            
            # Look for the table container. Often SEBI uses 'table-responsive' or similar classes.
            table_container = soup.find("div", class_="table-responsive") or soup
            table = table_container.find("table")
            
            if not table:
                logger.error("Could not find the data table on the SEBI page.")
                return []
                
            rows = table.find_all("tr")
            
            for row in rows[1:]:  # Skip header row
                cols = row.find_all("td")
                
                # Expected structure: Date, Title (link to details), Department/Category
                if len(cols) >= 3:
                    date_col = cols[0].text.strip()
                    title_col = cols[1]
                    dept_col = cols[2].text.strip()
                    
                    # Extract title and link
                    a_tag = title_col.find("a")
                    if a_tag:
                        title = a_tag.text.strip()
                        detail_url = a_tag.get("href")
                        if detail_url and not detail_url.startswith("http"):
                            detail_url = self.base_url + detail_url
                            
                        # The reference number is often within the title or requires visiting the detail page.
                        # For Phase 1, we will attempt to extract it if it looks like a ref number, 
                        # or use a hash of the title/url if absent, to ensure a unique ID.
                        # Real SEBI circulars often start with "SEBI/HO/..."
                        
                        # Let's extract the reference if it's explicitly available, else fallback
                        ref_number = None
                        
                        # Sometimes SEBI has a 4th column for reference, or it's embedded in the title text
                        # We will make a best effort to find something that looks like a reference
                        import re
                        ref_match = re.search(r'(SEBI/[A-Z0-9/]+)', title)
                        if ref_match:
                            ref_number = ref_match.group(1)
                        else:
                            # Use a slug of the URL as a fallback reference if no obvious ref number is found
                            ref_number = detail_url.split("/")[-1].split(".")[0] if detail_url else f"REF-{hash(title)}"
                            
                        # We also need the PDF URL. Often, the detail URL leads to a page WITH the PDF.
                        # Or sometimes the link itself IS the PDF.
                        pdf_url = detail_url
                        
                        # If the detail_url is not a PDF, we technically need to scrape the detail page.
                        # For Phase 1 optimization, we'll store the detail URL. The downloader can handle logic if needed,
                        # or we assume SEBI provides direct PDF links or we just store the detail link for now.
                        
                        doc = {
                            "reference": ref_number,
                            "title": title,
                            "publication_date": self.parse_date(date_col),
                            "category": dept_col,
                            "pdf_url": pdf_url, # Might be a detail page url
                            "detail_url": detail_url
                        }
                        
                        scraped_data.append(doc)
            
            logger.info(f"Successfully scraped {len(scraped_data)} circulars.")
            return scraped_data

        except Exception as e:
            logger.error(f"Failed to scrape SEBI circulars: {e}", exc_info=True)
            return []

if __name__ == "__main__":
    # Simple manual test
    logging.basicConfig(level=logging.INFO)
    scraper = SEBIScraper()
    docs = scraper.scrape()
    for d in docs[:3]:
        print(d)
