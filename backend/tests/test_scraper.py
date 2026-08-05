import pytest
from unittest.mock import patch, MagicMock
from app.scraper.sebi_scraper import SEBIScraper

@pytest.fixture
def scraper():
    return SEBIScraper()

def test_parse_date(scraper):
    assert scraper.parse_date("Jul 14, 2026") == "2026-07-14"
    assert scraper.parse_date("Jan 01, 2024") == "2024-01-01"
    # Fallback to string if unparseable
    assert scraper.parse_date("Invalid Date") == "Invalid Date"

@patch('app.scraper.sebi_scraper.requests.get')
def test_scrape_success(mock_get, scraper):
    mock_html = """
    <html>
        <body>
            <div class="table-responsive">
                <table>
                    <tr><th>Date</th><th>Title</th><th>Department</th></tr>
                    <tr>
                        <td>Jul 14, 2026</td>
                        <td><a href="/test/url/SEBI/HO/MIRSD/2026/104.html">Circular SEBI/HO/MIRSD/2026/104 regarding mobile verification</a></td>
                        <td>Market Intermediaries Regulation</td>
                    </tr>
                    <tr>
                        <td>Jul 15, 2026</td>
                        <td><a href="http://sebi.gov.in/test.pdf">Another Circular without ref in title</a></td>
                        <td>Corporate Finance</td>
                    </tr>
                </table>
            </div>
        </body>
    </html>
    """
    mock_response = MagicMock()
    mock_response.text = mock_html
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    results = scraper.scrape()
    
    assert len(results) == 2
    
    assert results[0]['publication_date'] == "2026-07-14"
    assert results[0]['reference'] == "SEBI/HO/MIRSD/2026/104"
    assert results[0]['category'] == "Market Intermediaries Regulation"
    assert results[0]['detail_url'].startswith("http")
    
    assert results[1]['publication_date'] == "2026-07-15"
    assert results[1]['reference'] != None  # Should fallback to generated or slug
    assert results[1]['category'] == "Corporate Finance"

@patch('app.scraper.sebi_scraper.requests.get')
def test_scrape_failure(mock_get, scraper):
    mock_get.side_effect = Exception("Connection error")
    results = scraper.scrape()
    assert results == []
