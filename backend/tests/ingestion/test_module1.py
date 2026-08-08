"""
Tests for Module 1 — PDF Extraction (PDFExtractor)

Strategy
--------
We test against a real minimal PDF generated in-memory with PyMuPDF itself.
This avoids any dependency on an external test fixture file while still
exercising the actual fitz extraction path.

Tests
-----
1. test_extract_returns_correct_type           — Output is RawSpanCollection
2. test_extract_span_count                     — Correct number of spans
3. test_extract_span_fields_present            — All required fields populated
4. test_whitespace_normalization               — Multiple spaces collapsed
5. test_blank_spans_skipped                    — Whitespace-only spans excluded
6. test_font_flags_bold_detection              — Bold flag decoded correctly
7. test_font_flags_italic_detection            — Italic flag decoded correctly
8. test_extract_to_file_creates_json           — JSON file written to disk
9. test_extract_to_file_valid_json             — Written file is valid JSON
10. test_file_not_found_raises                 — FileNotFoundError on bad path
11. test_non_pdf_raises                        — ValueError on wrong extension
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import fitz
import pytest

from app.ingestion.module1_extractor import PDFExtractor, _decode_flags, _normalize_text
from app.ingestion.models import RawSpanCollection


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

def _make_pdf(text_lines: list[tuple[str, str, float, bool]]) -> Path:
    """
    Create a minimal in-memory PDF with the given text lines and return
    its path inside a temporary directory.

    Parameters
    ----------
    text_lines : list of (text, font, size, bold)
    """
    tmp = tempfile.mkdtemp()
    pdf_path = Path(tmp) / "test_circular.pdf"

    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # A4

    y = 50.0
    for text, font_name, size, is_bold in text_lines:
        page.insert_text(
            (50, y),
            text,
            fontsize=size,
            fontname="helv",          # fitz built-in Helvetica
        )
        y += size + 6

    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


@pytest.fixture
def simple_pdf() -> Path:
    """A minimal 1-page PDF with known content."""
    return _make_pdf([
        ("SEBI Circular 104/2026", "helv", 14.0, True),
        ("This is a regulatory clause.", "helv", 10.0, False),
        ("  Extra   spaces   here  ", "helv", 10.0, False),
    ])


@pytest.fixture
def extractor(simple_pdf) -> PDFExtractor:
    return PDFExtractor(simple_pdf)


# ─────────────────────────────────────────────────────────────────────────────
# Unit tests — pure functions
# ─────────────────────────────────────────────────────────────────────────────

class TestDecodeFlags:
    def test_bold(self):
        flags = _decode_flags(0x10)
        assert flags.bold is True
        assert flags.italic is False

    def test_italic(self):
        flags = _decode_flags(0x02)
        assert flags.italic is True
        assert flags.bold is False

    def test_bold_and_italic(self):
        flags = _decode_flags(0x10 | 0x02)
        assert flags.bold is True
        assert flags.italic is True

    def test_all_false(self):
        flags = _decode_flags(0x00)
        assert not any([
            flags.superscript, flags.italic,
            flags.serifed, flags.monospaced, flags.bold
        ])

    def test_superscript(self):
        flags = _decode_flags(0x01)
        assert flags.superscript is True


class TestNormalizeText:
    def test_strips_leading_trailing(self):
        assert _normalize_text("  hello  ") == "hello"

    def test_collapses_internal_spaces(self):
        assert _normalize_text("hello   world") == "hello world"

    def test_collapses_tabs(self):
        assert _normalize_text("hello\t\tworld") == "hello world"

    def test_empty_string(self):
        assert _normalize_text("   ") == ""

    def test_no_change_needed(self):
        assert _normalize_text("hello world") == "hello world"


# ─────────────────────────────────────────────────────────────────────────────
# Integration tests — PDFExtractor
# ─────────────────────────────────────────────────────────────────────────────

class TestPDFExtractor:
    def test_extract_returns_correct_type(self, extractor):
        result = extractor.extract()
        assert isinstance(result, RawSpanCollection)

    def test_extract_page_count(self, extractor):
        result = extractor.extract()
        assert result.page_count == 1

    def test_extract_span_count_positive(self, extractor):
        result = extractor.extract()
        assert result.total_spans > 0

    def test_extract_total_spans_matches_list(self, extractor):
        result = extractor.extract()
        assert result.total_spans == len(result.spans)

    def test_span_fields_all_present(self, extractor):
        result = extractor.extract()
        span = result.spans[0]
        assert isinstance(span.page, int)
        assert isinstance(span.block, int)
        assert isinstance(span.line, int)
        assert isinstance(span.span, int)
        assert isinstance(span.text, str)
        assert isinstance(span.font, str)
        assert isinstance(span.size, float)
        assert span.bbox.x1 > span.bbox.x0
        assert span.bbox.y1 > span.bbox.y0

    def test_whitespace_normalization_applied(self, extractor):
        """Spans extracted from 'Extra   spaces   here' must have single spaces."""
        result = extractor.extract()
        texts = [s.text for s in result.spans]
        for text in texts:
            assert "  " not in text, f"Double space found in: {text!r}"

    def test_blank_spans_excluded(self, extractor):
        """No span should have empty text after normalization."""
        result = extractor.extract()
        for span in result.spans:
            assert span.text.strip() != ""

    def test_size_rounded_to_three_decimals(self, extractor):
        result = extractor.extract()
        for span in result.spans:
            assert span.size == round(span.size, 3)

    def test_extract_to_file_creates_json(self, extractor):
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "raw_spans.json"
            result_path = extractor.extract_to_file(out_path)
            assert result_path.exists()

    def test_extract_to_file_valid_json(self, extractor):
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "raw_spans.json"
            extractor.extract_to_file(out_path)
            data = json.loads(out_path.read_text(encoding="utf-8"))
            assert "spans" in data
            assert "total_spans" in data
            assert isinstance(data["spans"], list)

    def test_extract_to_file_json_schema(self, extractor):
        """Verify the JSON matches the RawSpanCollection schema."""
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "raw_spans.json"
            extractor.extract_to_file(out_path)
            data = json.loads(out_path.read_text(encoding="utf-8"))
            # Pydantic round-trip
            reloaded = RawSpanCollection.model_validate(data)
            assert reloaded.total_spans == len(reloaded.spans)


class TestPDFExtractorErrors:
    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            PDFExtractor(Path("/nonexistent/path/circular.pdf"))

    def test_wrong_extension(self):
        with tempfile.NamedTemporaryFile(suffix=".txt") as f:
            with pytest.raises(ValueError, match="Expected a .pdf file"):
                PDFExtractor(Path(f.name))
