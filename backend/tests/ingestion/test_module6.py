"""
Tests for Module 6 — Clause Extraction

Tests:
1. Context propagation (Chapter -> Section -> Clause -> Paragraph)
2. Parent text inheritance (Paragraph gets Clause's text as parent_text)
3. Filtering (only substantive nodes emit ExtractedClauses)
"""

from __future__ import annotations

import pytest

from app.ingestion.models import (
    ASTDocument,
    ASTNode,
)
from app.ingestion.module6_clauses import ClauseExtractor


@pytest.fixture
def sample_ast() -> ASTDocument:
    # Build a mock AST tree manually
    root = ASTNode(node_id="root", node_type="Document", text="Root", page=0)
    
    chapter = ASTNode(node_id="c1", node_type="Chapter", text="CHAPTER 1", page=1)
    root.children.append(chapter)
    
    sec = ASTNode(node_id="s1", node_type="Section", text="Section A", page=1)
    chapter.children.append(sec)
    
    clause_1 = ASTNode(node_id="cl1", node_type="Clause", text="1. Applicability", numbering="1", depth=1, page=1)
    sec.children.append(clause_1)
    
    para_1 = ASTNode(node_id="p1", node_type="Paragraph", text="This applies to everyone.", page=1)
    clause_1.children.append(para_1)
    
    bullet_1 = ASTNode(node_id="b1", node_type="Bullet", text="Except cats.", page=1)
    para_1.children.append(bullet_1)
    
    return ASTDocument(document_path="/tmp/fake.pdf", root=root)


def test_clause_extraction_count(sample_ast):
    extractor = ClauseExtractor(sample_ast)
    clauses = extractor.extract().clauses
    
    # Substantive nodes:
    # 1. Clause: "1. Applicability"
    # 2. Paragraph: "This applies to everyone."
    # 3. Bullet: "Except cats."
    assert len(clauses) == 3


def test_context_propagation(sample_ast):
    extractor = ClauseExtractor(sample_ast)
    clauses = extractor.extract().clauses
    
    # The paragraph should inherit the Chapter, Section, and Clause Number
    para = clauses[1]
    assert para.node_type == "Paragraph"
    assert para.chapter_title == "CHAPTER 1"
    assert para.section_title == "Section A"
    assert para.clause_number == "1"


def test_parent_text_inheritance(sample_ast):
    extractor = ClauseExtractor(sample_ast)
    clauses = extractor.extract().clauses
    
    # 1. The clause itself should NOT have itself as parent text.
    # It inherits its parent text from whatever was before it (None in this case)
    clause = clauses[0]
    assert clause.parent_text is None
    
    # 2. The paragraph should have the clause's text as parent text
    para = clauses[1]
    assert para.parent_text == "1. Applicability"
    
    # 3. The bullet is a child of the paragraph, so it gets the paragraph's text
    bullet = clauses[2]
    assert bullet.parent_text == "This applies to everyone."


def test_path_string(sample_ast):
    extractor = ClauseExtractor(sample_ast)
    clauses = extractor.extract().clauses
    
    bullet = clauses[2]
    assert bullet.path == "[CHAPTER 1] > [Section A] > Clause 1"
