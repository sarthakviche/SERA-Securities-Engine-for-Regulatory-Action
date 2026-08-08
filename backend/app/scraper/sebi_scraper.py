import logging
import re
from typing import List, Dict, Any
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from app.core.config import settings
from app.scraper.retry import retry

logger = logging.getLogger(__name__)

# SEBI's internal AJAX endpoint that powers the homepage "What's New" widget.
# It returns the last ~5 days of all document types (Circulars, Orders, etc.)
# as an HTML fragment, grouped by date (h3) and category (h4).
ENTRYLIST_URL = "https://www.sebi.gov.in/sebiweb/ajax/home/entrylist.jsp"
ENTRYLIST_HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Referer": "https://www.sebi.gov.in/",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
}


class SEBIScraper:
    def __init__(self):
        self.timeout = (settings.HTTP_TIMEOUT_CONNECT, settings.HTTP_TIMEOUT_READ)

    @retry(
        max_retries=settings.SCRAPER_MAX_RETRIES,
        base_delay=settings.SCRAPER_RETRY_DELAY,
        exceptions=(requests.RequestException,),
    )
    def _fetch_entrylist(self) -> str:
        """
        Calls SEBI's internal AJAX endpoint directly via a simple POST request.
        Returns the raw HTML fragment containing the latest entries.
        No headless browser required.
        """
        logger.info(f"Fetching SEBI entry list from {ENTRYLIST_URL}")
        response = requests.post(
            ENTRYLIST_URL,
            data="entryList=Y",
            headers=ENTRYLIST_HEADERS,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.text

    def parse_date(self, date_str: str) -> str:
        """Parses SEBI date format (e.g., 'Aug 05, 2026') to ISO 8601 (YYYY-MM-DD)."""
        try:
            dt = datetime.strptime(date_str.strip(), "%b %d, %Y")
            return dt.strftime("%Y-%m-%d")
        except ValueError as e:
            logger.warning(f"Could not parse date '{date_str}': {e}")
            return date_str.strip()

    @staticmethod
    def _build_reference(detail_url: str, publication_date: str) -> str:
        """
        Builds a clean, human-readable circular reference ID from the detail URL.

        SEBI URLs follow the pattern:
          .../legal/circulars/{mon-YYYY}/{slug}_{numeric_id}.html

        We extract the numeric SEBI document ID and combine it with the date:
          SEBI-CIRC-{YYYY-MM-DD}-{numeric_id}

        e.g.  SEBI-CIRC-2026-08-03-103314

        This is:
          - Stable and unique (SEBI numeric ID never changes)
          - Meaningful (includes source, type, date)
          - Clean for use as a filename or database key
        """
        slug = detail_url.rstrip("/").split("/")[-1]  # e.g. "some-title_103314.html"
        slug_no_ext = slug.rsplit(".", 1)[0]           # e.g. "some-title_103314"
        # The numeric SEBI ID is always the last underscore-separated segment
        parts = slug_no_ext.rsplit("_", 1)
        numeric_id = parts[-1] if parts[-1].isdigit() else slug_no_ext
        return f"SEBI-CIRC-{publication_date}-{numeric_id}"

    def scrape(self) -> List[Dict[str, Any]]:
        """
        Fetches and parses the SEBI entry list, returning only 'Circulars'
        as a list of dicts. Returns empty list on failure.

        The HTML structure is:
            <h3>Aug 05, 2026</h3>
            <h4>Circulars</h4>
            <ul>
                <li><a href="...">Circular title</a></li>
            </ul>
        """
        try:
            html = self._fetch_entrylist()
            soup = BeautifulSoup(html, "lxml")

            circulars = []
            current_date = None

            for tag in soup.find_all(["h3", "h4", "ul"]):
                if tag.name == "h3":
                    # Date header
                    current_date = self.parse_date(tag.text.strip())

                elif tag.name == "h4" and tag.text.strip().lower() == "circulars":
                    # Found a Circulars section — grab the next <ul>
                    ul = tag.find_next_sibling("ul")
                    if ul and current_date:
                        for li in ul.find_all("li"):
                            a = li.find("a")
                            if not a:
                                continue

                            title = a.text.strip()
                            detail_url = a.get("href", "")

                            # Build a clean, stable reference ID from the URL
                            ref_number = self._build_reference(detail_url, current_date)

                            circulars.append(
                                {
                                    "reference": ref_number,
                                    "title": title,
                                    "publication_date": current_date,
                                    "category": "Circulars",
                                    "pdf_url": detail_url,
                                    "detail_url": detail_url,
                                }
                            )

            logger.info(f"Successfully scraped {len(circulars)} circulars.")
            return circulars

        except Exception as e:
            logger.error(f"Failed to scrape SEBI circulars: {e}", exc_info=True)
            return []


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scraper = SEBIScraper()
    docs = scraper.scrape()
    if docs:
        print(f"\nFound {len(docs)} circulars:\n")
        for d in docs:
            print(f"  [{d['publication_date']}] {d['title']}")
            print(f"   URL: {d['detail_url']}")
            print()
    else:
        print("No circulars scraped.")
