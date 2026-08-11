"""
Tests for Module 4 — Numbering Detection

Tests:
1. decimal_dotted pattern (e.g. 1.1, 1.1.1)
2. decimal pattern (e.g. 1., 2.)
3. alpha_lower_paren (e.g. (a))
4. alpha_upper_paren (e.g. (A))
5. roman_lower_paren (e.g. (i), (iv))
6. roman_upper (e.g. I., IV.)
7. roman_lower (e.g. i., ii.)
8. appendix / schedule / annexure
9. Non-matching text is ignored
"""

from __future__ import annotations

import pytest

from app.ingestion.models import (
    BoundingBox,
    LayoutBlock,
    LayoutCollection,
)
from app.ingestion.module4_numbering import NumberingDetector


def _make_block(block_id: str, text: str) -> LayoutBlock:
    return LayoutBlock(
        block_id=block_id, page=0, region_type="paragraph",
        bbox=BoundingBox(x0=0, y0=0, x1=100, y1=20),
        text=text
    )


@pytest.fixture
def layout_collection():
    blocks = [
        _make_block("b1", "1.1.3 Some clause text"),
        _make_block("b2", "2. Another clause"),
        _make_block("b3", "(a) Sub-clause"),
        _make_block("b4", "(B) Upper alpha"),
        _make_block("b5", "(iv) Roman lower paren"),
        _make_block("b6", "IV. Roman upper"),
        _make_block("b7", "ix. Roman lower"),
        _make_block("b8", "Appendix A Details"),
        _make_block("b9", "Schedule 1 Table"),
        _make_block("b10", "Annexure II Form"),
        _make_block("b11", "Just normal text without numbering"),
        _make_block("b12", "1.1 "), # Edge case: just the number
    ]
    return LayoutCollection(
        document_path="/tmp/fake.pdf", page_count=1,
        total_blocks=len(blocks), blocks=blocks
    )


def test_decimal_dotted(layout_collection):
    detector = NumberingDetector(layout_collection)
    matches = detector.detect().matches
    
    m1 = [m for m in matches if m.block_id == "b1"][0]
    assert m1.scheme == "decimal_dotted"
    assert m1.raw_text == "1.1.3"
    assert m1.components == ["1", "1", "3"]
    assert m1.depth == 3
    
    m12 = [m for m in matches if m.block_id == "b12"][0]
    assert m12.scheme == "decimal_dotted"
    assert m12.components == ["1", "1"]


def test_decimal(layout_collection):
    detector = NumberingDetector(layout_collection)
    matches = detector.detect().matches
    
    m = [m for m in matches if m.block_id == "b2"][0]
    assert m.scheme == "decimal"
    assert m.raw_text == "2."
    assert m.components == ["2"]


def test_alpha_paren(layout_collection):
    detector = NumberingDetector(layout_collection)
    matches = detector.detect().matches
    
    ma = [m for m in matches if m.block_id == "b3"][0]
    assert ma.scheme == "alpha_lower_paren"
    assert ma.components == ["a"]

    mA = [m for m in matches if m.block_id == "b4"][0]
    assert mA.scheme == "alpha_upper_paren"
    assert mA.components == ["B"]


def test_roman_paren(layout_collection):
    detector = NumberingDetector(layout_collection)
    matches = detector.detect().matches
    
    m = [m for m in matches if m.block_id == "b5"][0]
    assert m.scheme == "roman_lower_paren"
    assert m.components == ["iv"]


def test_roman_dotted(layout_collection):
    detector = NumberingDetector(layout_collection)
    matches = detector.detect().matches
    
    upper = [m for m in matches if m.block_id == "b6"][0]
    assert upper.scheme == "roman_upper"
    assert upper.components == ["IV"]

    lower = [m for m in matches if m.block_id == "b7"][0]
    assert lower.scheme == "roman_lower"
    assert lower.components == ["ix"]


def test_appendix_schedule_annexure(layout_collection):
    detector = NumberingDetector(layout_collection)
    matches = detector.detect().matches
    
    app = [m for m in matches if m.block_id == "b8"][0]
    assert app.scheme == "appendix"
    assert app.components == ["A"]

    sch = [m for m in matches if m.block_id == "b9"][0]
    assert sch.scheme == "schedule"
    assert sch.components == ["1"]
    
    anx = [m for m in matches if m.block_id == "b10"][0]
    assert anx.scheme == "annexure"
    assert anx.components == ["II"]


def test_normal_text_ignored(layout_collection):
    detector = NumberingDetector(layout_collection)
    matches = detector.detect().matches
    
    ids = [m.block_id for m in matches]
    assert "b11" not in ids
