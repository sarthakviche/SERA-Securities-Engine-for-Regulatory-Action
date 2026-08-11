"""
Tests for Module 5 — AST Builder

Tests:
1. Hierarchy enforcement: Section > Clause > Paragraph
2. Paragraphs become siblings under the same Clause
3. Depth enforcement: Clause (depth 1) > Clause (depth 2)
4. Headers and footers are omitted from the AST
"""

from __future__ import annotations

import pytest

from app.ingestion.models import (
    BoundingBox,
    DetectedHeading,
    HeadingCollection,
    LayoutBlock,
    LayoutCollection,
    NumberingCollection,
    NumberingMatch,
)
from app.ingestion.module5_ast import ASTBuilder


def _make_block(block_id: str, text: str, region: str = "paragraph") -> LayoutBlock:
    return LayoutBlock(
        block_id=block_id, page=0, region_type=region,
        bbox=BoundingBox(x0=0, y0=0, x1=100, y1=20),
        text=text
    )

def _make_heading(block_id: str, level: str) -> DetectedHeading:
    return DetectedHeading(
        heading_id=f"h_{block_id}", page=0, level=level, # type: ignore
        text="heading", block_id=block_id,
        bbox=BoundingBox(x0=0, y0=0, x1=10, y1=10),
        font_size=12.0, is_bold=True, is_uppercase=False
    )

def _make_num(block_id: str, scheme: str, depth: int) -> NumberingMatch:
    return NumberingMatch(
        block_id=block_id, page=0, raw_text="1.", scheme=scheme, # type: ignore
        components=["1"] * depth, depth=depth
    )


@pytest.fixture
def mock_collections():
    blocks = [
        _make_block("b1", "Header", region="header"),
        _make_block("b2", "CHAPTER 1"),
        _make_block("b3", "Section A"),
        _make_block("b4", "1. First clause"),
        _make_block("b5", "A normal paragraph"),
        _make_block("b6", "1.1 Sub-clause"),
        _make_block("b7", "Another paragraph"),
        _make_block("b8", "Footer", region="footer"),
    ]
    layout_coll = LayoutCollection(document_path="/tmp/fake.pdf", page_count=1, total_blocks=8, blocks=blocks)
    
    headings = [
        _make_heading("b2", "chapter"),
        _make_heading("b3", "section"),
    ]
    head_coll = HeadingCollection(document_path="/tmp/fake.pdf", total_headings=2, headings=headings)
    
    numbering = [
        _make_num("b4", "decimal", 1),
        _make_num("b6", "decimal_dotted", 2),
    ]
    num_coll = NumberingCollection(document_path="/tmp/fake.pdf", total_matches=2, matches=numbering)
    
    return layout_coll, head_coll, num_coll


def test_ast_hierarchy(mock_collections):
    layout_coll, head_coll, num_coll = mock_collections
    builder = ASTBuilder(layout_coll, head_coll, num_coll)
    ast = builder.build()
    
    root = ast.root
    assert len(root.children) == 1
    
    chapter = root.children[0]
    assert chapter.node_type == "Chapter"
    assert chapter.text == "CHAPTER 1"
    assert len(chapter.children) == 1
    
    section = chapter.children[0]
    assert section.node_type == "Section"
    assert section.text == "Section A"
    assert len(section.children) == 1
    
    clause_1 = section.children[0]
    assert clause_1.node_type == "Clause"
    assert clause_1.text == "1. First clause"
    # It has paragraph b5 AND sub-clause b6 as children
    assert len(clause_1.children) == 2
    
    para1 = clause_1.children[0]
    assert para1.node_type == "Paragraph"
    assert para1.text == "A normal paragraph"
    
    clause_1_1 = clause_1.children[1]
    assert clause_1_1.node_type == "Clause"
    assert clause_1_1.depth == 2
    assert clause_1_1.text == "1.1 Sub-clause"
    assert len(clause_1_1.children) == 1
    
    para2 = clause_1_1.children[0]
    assert para2.node_type == "Paragraph"
    assert para2.text == "Another paragraph"

def test_ast_skips_headers_footers(mock_collections):
    layout_coll, head_coll, num_coll = mock_collections
    builder = ASTBuilder(layout_coll, head_coll, num_coll)
    ast = builder.build()
    
    # Recursively check that no node has text "Header" or "Footer"
    def check_node(node):
        assert node.text != "Header"
        assert node.text != "Footer"
        for child in node.children:
            check_node(child)
            
    check_node(ast.root)
