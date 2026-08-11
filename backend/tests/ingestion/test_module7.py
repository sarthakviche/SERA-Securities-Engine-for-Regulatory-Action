"""
Tests for Module 7 — Semantic Batching

Tests:
1. Batch breaks on token limits
2. Batch breaks on Chapter changes
3. Formatting includes path, context, and text
"""

from __future__ import annotations

import pytest

from app.ingestion.models import (
    ClauseCollection,
    ExtractedClause,
)
from app.ingestion.module7_batches import SemanticBatcher


def _make_clause(text: str, chapter: str = "CH 1") -> ExtractedClause:
    return ExtractedClause(
        clause_id="c1",
        chapter_title=chapter,
        section_title=None,
        subsection_title=None,
        clause_number=None,
        page_number=1,
        node_type="Paragraph",
        parent_text="Context Text",
        text=text,
        path="Path String"
    )

@pytest.fixture
def sample_clauses():
    return [
        _make_clause("A short clause.", "CH 1"),
        _make_clause("Another short one.", "CH 1"),
        # Huge clause to trigger overflow if limit is e.g. 5 tokens
        _make_clause("This is a very very very long text that will overflow.", "CH 1"),
        _make_clause("New chapter text.", "CH 2")
    ]

def test_batch_token_overflow(sample_clauses):
    coll = ClauseCollection(document_path="/tmp/fake.pdf", total_clauses=4, clauses=sample_clauses)
    
    # Very small limit to force a break
    batcher = SemanticBatcher(coll, max_tokens=10)
    batches = batcher.batch().batches
    
    # 1. "A short clause" + "Another short one" > 10 tokens (with path and context)
    # So they should end up in different batches.
    assert len(batches) > 1

def test_batch_chapter_break(sample_clauses):
    coll = ClauseCollection(document_path="/tmp/fake.pdf", total_clauses=4, clauses=sample_clauses)
    
    # Huge limit so tokens don't cause breaks
    batcher = SemanticBatcher(coll, max_tokens=10000)
    batches = batcher.batch().batches
    
    # Only break should be between CH 1 and CH 2
    assert len(batches) == 2
    
    # First batch has 3 clauses, second has 1
    assert len(batches[0].clause_ids) == 3
    assert len(batches[1].clause_ids) == 1

def test_batch_formatting(sample_clauses):
    coll = ClauseCollection(document_path="/tmp/fake.pdf", total_clauses=4, clauses=sample_clauses)
    batcher = SemanticBatcher(coll, max_tokens=10000)
    batches = batcher.batch().batches
    
    b1_text = batches[0].text
    assert "Location: Path String" in b1_text
    assert "Context: Context Text" in b1_text
    assert "Content: A short clause." in b1_text
