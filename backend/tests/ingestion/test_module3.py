"""
Tests for Module 3 — Heading Detection

Tests:
1. is_bold calculation (>50% characters must be bold).
2. is_uppercase calculation.
3. document_title classification.
4. part / chapter classification via regex.
5. size-based hierarchy (section > subsection > clause_heading).
6. Non-bold, non-uppercase paragraphs are ignored.
"""

from __future__ import annotations

import pytest

from app.ingestion.models import (
    BoundingBox,
    FontFlags,
    LayoutBlock,
    LayoutCollection,
    RawSpan,
    RawSpanCollection,
)
from app.ingestion.module3_headings import HeadingDetector


def _make_span(text: str, size: float, bold: bool) -> RawSpan:
    flags = FontFlags(bold=bold)
    return RawSpan(
        page=0, block=0, line=0, span=0, text=text,
        font="Arial", size=size, flags=flags,
        bbox=BoundingBox(x0=0, y0=0, x1=10, y1=10),
        color=0, origin_x=0, origin_y=0
    )


def _make_block(block_id: str, text: str, span_indices: list[int], page: int = 0, align: str = "left", region_type: str = "paragraph") -> LayoutBlock:
    return LayoutBlock(
        block_id=block_id, page=page, region_type=region_type,
        bbox=BoundingBox(x0=0, y0=0, x1=100, y1=20),
        indent_level=0, alignment=align,
        span_indices=span_indices, text=text
    )


@pytest.fixture
def test_data():
    spans = [
        _make_span("MASTER CIRCULAR", 16.0, True),  # 0
        _make_span("PART I", 14.0, True),           # 1
        _make_span("CHAPTER 1", 14.0, True),        # 2
        _make_span("Applicability", 12.0, True),    # 3
        _make_span("General info", 10.0, False),    # 4 (normal text)
        _make_span("Sub-heading", 11.0, True),      # 5
    ]
    raw_coll = RawSpanCollection(
        document_path="/tmp/fake.pdf", page_count=1,
        total_spans=len(spans), spans=spans
    )
    
    blocks = [
        _make_block("b0", "MASTER CIRCULAR", [0], align="center"),
        _make_block("b1", "PART I", [1]),
        _make_block("b2", "CHAPTER 1", [2]),
        _make_block("b3", "Applicability", [3]),
        _make_block("b4", "General info", [4]),
        _make_block("b5", "Sub-heading", [5]),
    ]
    layout_coll = LayoutCollection(
        document_path="/tmp/fake.pdf", page_count=1,
        total_blocks=len(blocks), blocks=blocks
    )
    
    return layout_coll, raw_coll


def test_document_title_detection(test_data):
    layout_coll, raw_coll = test_data
    detector = HeadingDetector(layout_coll, raw_coll)
    headings = detector.detect().headings
    
    doc_title = [h for h in headings if h.block_id == "b0"][0]
    assert doc_title.level == "document_title"
    assert doc_title.is_bold is True


def test_part_and_chapter_detection(test_data):
    layout_coll, raw_coll = test_data
    detector = HeadingDetector(layout_coll, raw_coll)
    headings = detector.detect().headings
    
    part = [h for h in headings if h.block_id == "b1"][0]
    assert part.level == "part"
    
    chapter = [h for h in headings if h.block_id == "b2"][0]
    assert chapter.level == "chapter"


def test_hierarchy_ranking_by_size(test_data):
    layout_coll, raw_coll = test_data
    detector = HeadingDetector(layout_coll, raw_coll)
    headings = detector.detect().headings
    
    # "Applicability" is size 12.0, "Sub-heading" is size 11.0
    # So 12.0 -> section, 11.0 -> subsection
    sec = [h for h in headings if h.block_id == "b3"][0]
    subsec = [h for h in headings if h.block_id == "b5"][0]
    
    assert sec.level == "section"
    assert subsec.level == "subsection"


def test_normal_text_is_ignored(test_data):
    layout_coll, raw_coll = test_data
    detector = HeadingDetector(layout_coll, raw_coll)
    headings = detector.detect().headings
    
    # Block b4 ("General info") should NOT be in headings
    ids = [h.block_id for h in headings]
    assert "b4" not in ids


def test_is_bold_calculation():
    spans = [
        _make_span("BoldText", 10.0, True),   # len 8
        _make_span("NormalText", 10.0, False) # len 10
    ]
    raw_coll = RawSpanCollection(
        document_path="/tmp/fake.pdf", page_count=1,
        total_spans=2, spans=spans
    )
    # block mostly normal -> not bold
    b1 = _make_block("b1", "BoldTextNormalText", [0, 1])
    # block entirely bold -> bold
    b2 = _make_block("b2", "BoldText", [0])
    
    layout_coll = LayoutCollection(
        document_path="/tmp/fake.pdf", page_count=1,
        total_blocks=2, blocks=[b1, b2]
    )
    
    detector = HeadingDetector(layout_coll, raw_coll)
    assert detector._analyze_block_font(b1)[0] is False
    assert detector._analyze_block_font(b2)[0] is True
