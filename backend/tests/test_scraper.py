import pytest
from unittest.mock import patch
from app.scraper.sebi_scraper import SEBIScraper


@pytest.fixture
def scraper():
    return SEBIScraper()


def test_parse_date(scraper):
    assert scraper.parse_date("Aug 05, 2026") == "2026-08-05"
    assert scraper.parse_date("Jan 01, 2024") == "2024-01-01"
    # Fallback to raw string if unparseable
    assert scraper.parse_date("Invalid Date") == "Invalid Date"


# Minimal HTML fragment matching the real SEBI entrylist.jsp structure
MOCK_HTML = """
<h3 class="new-head">Aug 03, 2026</h3>
<h4 class="new-sub-head">Orders</h4>
<ul>
    <li><a href="https://www.sebi.gov.in/enforcement/orders/aug-2026/some-order_001.html">Some Order</a></li>
</ul>
<h4 class="new-sub-head">Circulars</h4>
<ul>
    <li>
        <a href="https://www.sebi.gov.in/legal/circulars/aug-2026/circular-sebi-ho-mirsd-2026-104_103314.html">
            Extension of timeline for enrolment with PaRRVA as specified in SEBI Circular No. HO/38/14/2026
        </a>
    </li>
</ul>
<h3 class="new-head">Jul 31, 2026</h3>
<h4 class="new-sub-head">Circulars</h4>
<ul>
    <li>
        <a href="https://www.sebi.gov.in/legal/circulars/jul-2026/digital-accessibility-circulars_103277.html">
            Extension of timelines with respect to compliance of Digital Accessibility Circulars.
        </a>
    </li>
</ul>
<h4 class="new-sub-head">Orders</h4>
<ul>
    <li><a href="https://www.sebi.gov.in/enforcement/orders/jul-2026/some-order_002.html">Another Order</a></li>
</ul>
"""


@patch.object(SEBIScraper, "_fetch_entrylist", return_value=MOCK_HTML)
def test_scrape_only_returns_circulars(mock_fetch, scraper):
    """Ensures non-circular categories (Orders, etc.) are filtered out."""
    results = scraper.scrape()

    assert len(results) == 2
    for r in results:
        assert r["category"] == "Circulars"


@patch.object(SEBIScraper, "_fetch_entrylist", return_value=MOCK_HTML)
def test_scrape_dates_and_urls(mock_fetch, scraper):
    """Validates that dates and URLs are extracted correctly."""
    results = scraper.scrape()

    assert results[0]["publication_date"] == "2026-08-03"
    assert results[0]["detail_url"].startswith("https://")
    assert results[1]["publication_date"] == "2026-07-31"
    assert results[1]["detail_url"].startswith("https://")


@patch.object(SEBIScraper, "_fetch_entrylist", return_value=MOCK_HTML)
def test_scrape_reference_extraction(mock_fetch, scraper):
    """Validates reference number extraction from title or URL slug fallback."""
    results = scraper.scrape()
    # Both should have a non-None reference
    assert results[0]["reference"] is not None
    assert results[1]["reference"] is not None


@patch.object(SEBIScraper, "_fetch_entrylist", side_effect=Exception("Connection error"))
def test_scrape_failure_returns_empty(mock_fetch, scraper):
    """Ensures graceful failure — returns empty list instead of raising."""
    results = scraper.scrape()
    assert results == []


@patch.object(SEBIScraper, "_fetch_entrylist", return_value="<html><body>No data</body></html>")
def test_scrape_no_circulars(mock_fetch, scraper):
    """Handles a response with no circulars section gracefully."""
    results = scraper.scrape()
    assert results == []
