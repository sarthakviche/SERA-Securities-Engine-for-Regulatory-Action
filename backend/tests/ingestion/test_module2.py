"""
Tests for Module 2 — Layout Analysis

Tests:
1. Block Grouping — Spans with same page/block ID are grouped correctly.
2. Text Reconstruction — Text is joined with spaces.
3. Bounding Box — Block bbox correctly encompasses all child span bboxes.
4. Header Classification — y0 < 80.
5. Footer Classification — y1 > 760.
6. Page Number Classification — Header/footer containing only digits/page pattern.
7. Note Classification — Text starting with "Note:".
8. Indentation Level — Calculates correctly based on 18pt intervals from 72pt margin.
9. Alignment — Left, Center, Right, Justify.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from datetime import datetime

import pytest

from app.ingestion.models import (
    BoundingBox,
    FontFlags,
    RawSpan,
    RawSpanCollection,
    LayoutCollection
)
from app.ingestion.module2_layout import LayoutAnalyzer

# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

def _make_span(
    page: int, block: int, span: int, text: str, 
    x0: float, y0: float, x1: float, y1: float
) -> RawSpan:
    return RawSpan(
        page=page, block=block, line=0, span=span,
        text=text, font="Arial", size=10.0,
        flags=FontFlags(),
        bbox=BoundingBox(x0=x0, y0=y0, x1=x1, y1=y1),
        color=0, origin_x=x0, origin_y=y1
    )

@pytest.fixture
def sample_raw_collection() -> RawSpanCollection:
    spans = [
        # Header (page number)
        _make_span(0, 0, 0, "Page 1 of 2", 500, 50, 560, 65),
        
        # Center Aligned Title
        _make_span(0, 1, 0, "MASTER CIRCULAR", 250, 100, 350, 120),
        
        # Standard Paragraph (2 spans)
        _make_span(0, 2, 0, "This is", 72, 150, 120, 160),
        _make_span(0, 2, 1, "a paragraph.", 125, 150, 200, 160),
        
        # Indented Block (Level 1 = 72 + 18 = 90)
        _make_span(0, 3, 0, "Indented text", 90, 200, 150, 210),
        
        # Note
        _make_span(0, 4, 0, "Note: This is important.", 72, 250, 250, 260),
        
        # Bullet List
        _make_span(0, 5, 0, "• Bullet item", 72, 300, 150, 310),
        
        # Footer
        _make_span(0, 6, 0, "Confidential", 72, 780, 150, 790),
    ]
    return RawSpanCollection(
        document_path="/tmp/fake.pdf",
        page_count=1,
        total_spans=len(spans),
        spans=spans
    )

@pytest.fixture
def analyzer(sample_raw_collection) -> LayoutAnalyzer:
    return LayoutAnalyzer(sample_raw_collection)

# ─────────────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_block_grouping_and_count(analyzer):
    collection = analyzer.analyze()
    assert collection.total_blocks == 7

def test_text_reconstruction(analyzer):
    collection = analyzer.analyze()
    # Block 2 has 2 spans
    block2 = collection.blocks[2]
    assert block2.text == "This is a paragraph."

def test_bounding_box_calculation(analyzer):
    collection = analyzer.analyze()
    block2 = collection.blocks[2]
    # min(72, 125) = 72
    # max(120, 200) = 200
    assert block2.bbox.x0 == 72
    assert block2.bbox.x1 == 200

def test_page_number_classification(analyzer):
    collection = analyzer.analyze()
    # Block 0 is "Page 1 of 2" at y=50 (< 80)
    assert collection.blocks[0].region_type == "page_number"

def test_footer_classification(analyzer):
    collection = analyzer.analyze()
    # Block 6 is at y=780 (> 760)
    assert collection.blocks[6].region_type == "footer"

def test_note_classification(analyzer):
    collection = analyzer.analyze()
    # Block 4 starts with "Note:"
    assert collection.blocks[4].region_type == "note"

def test_bullet_classification(analyzer):
    collection = analyzer.analyze()
    # Block 5 starts with "•"
    assert collection.blocks[5].region_type == "bullet_list"

def test_indentation_calculation(analyzer):
    collection = analyzer.analyze()
    # Block 2 is at 72 (Level 0)
    assert collection.blocks[2].indent_level == 0
    
    # Block 3 is at 90 (Level 1)
    assert collection.blocks[3].indent_level == 1
    assert collection.blocks[3].region_type == "indented_block"

def test_alignment_calculation(analyzer):
    collection = analyzer.analyze()
    
    # Block 1 is Center
    assert collection.blocks[1].alignment == "center"
    
    # Block 2 is Left
    assert collection.blocks[2].alignment == "left"

def test_extract_to_file(analyzer):
    with tempfile.TemporaryDirectory() as tmp:
        out_path = Path(tmp) / "layout.json"
        result_path = analyzer.analyze_to_file(out_path)
        assert result_path.exists()
        
        data = json.loads(result_path.read_text(encoding="utf-8"))
        assert "blocks" in data
        assert len(data["blocks"]) == 7
