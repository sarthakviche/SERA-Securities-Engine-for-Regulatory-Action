"""
SERA Ingestion Pipeline — Pydantic v2 Models

All models for all 7 pipeline stages are defined here.
Each stage imports only the models it needs.
"""

from __future__ import annotations

from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime


# ─────────────────────────────────────────────────────────────────────────────
# Shared primitives
# ─────────────────────────────────────────────────────────────────────────────

class BoundingBox(BaseModel):
    """Bounding box in PDF points (1 pt = 1/72 inch). Origin is top-left."""
    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        return self.y1 - self.y0

    @property
    def left(self) -> float:
        return self.x0

    @property
    def top(self) -> float:
        return self.y0


class FontFlags(BaseModel):
    """
    Decoded from PyMuPDF's integer bitmask.
    PyMuPDF flag bits:
      0 → superscript
      1 → italic
      2 → serifed
      3 → monospaced
      4 → bold
    """
    superscript: bool = False
    italic: bool = False
    serifed: bool = False
    monospaced: bool = False
    bold: bool = False


# ─────────────────────────────────────────────────────────────────────────────
# Module 1 — Raw Spans
# ─────────────────────────────────────────────────────────────────────────────

class RawSpan(BaseModel):
    """
    Atomic unit of extracted text. One RawSpan = one PyMuPDF span.
    No interpretation. No merging. Only whitespace normalization.
    """
    page: int = Field(..., description="0-indexed page number")
    block: int = Field(..., description="Block index within page")
    line: int = Field(..., description="Line index within block")
    span: int = Field(..., description="Span index within line")
    text: str = Field(..., description="Whitespace-normalized text content")
    font: str = Field(..., description="Font name as reported by PyMuPDF")
    size: float = Field(..., description="Font size in points")
    flags: FontFlags
    bbox: BoundingBox
    color: int = Field(..., description="Text color as 24-bit RGB integer")
    origin_x: float = Field(..., description="Baseline x-coordinate in points")
    origin_y: float = Field(..., description="Baseline y-coordinate in points")


class RawSpanCollection(BaseModel):
    """Top-level container for raw_spans.json"""
    document_path: str
    page_count: int
    total_spans: int
    extracted_at: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )
    spans: List[RawSpan]


# ─────────────────────────────────────────────────────────────────────────────
# Module 2 — Layout (placeholder — expanded in Module 2)
# ─────────────────────────────────────────────────────────────────────────────

RegionType = Literal[
    "paragraph", "heading", "table", "note", "header", "footer",
    "page_number", "indented_block", "bullet_list", "blank"
]


class LayoutBlock(BaseModel):
    block_id: str
    page: int
    region_type: RegionType
    bbox: BoundingBox
    indent_level: int = 0
    alignment: Literal["left", "center", "right", "justify", "unknown"] = "unknown"
    span_indices: List[int] = Field(default_factory=list)
    text: str = ""


class LayoutCollection(BaseModel):
    document_path: str
    page_count: int
    total_blocks: int
    analyzed_at: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )
    blocks: List[LayoutBlock]


# ─────────────────────────────────────────────────────────────────────────────
# Module 3 — Headings (placeholder)
# ─────────────────────────────────────────────────────────────────────────────

HeadingLevel = Literal[
    "document_title", "part", "chapter", "section",
    "subsection", "clause_heading"
]


class DetectedHeading(BaseModel):
    heading_id: str
    page: int
    level: HeadingLevel
    text: str
    block_id: str
    bbox: BoundingBox
    font_size: float
    is_bold: bool
    is_uppercase: bool
    numbering: Optional[str] = None


class HeadingCollection(BaseModel):
    document_path: str
    total_headings: int
    detected_at: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )
    headings: List[DetectedHeading]


# ─────────────────────────────────────────────────────────────────────────────
# Module 4 — Numbering (placeholder)
# ─────────────────────────────────────────────────────────────────────────────

NumberingScheme = Literal[
    "decimal",          # 1, 2, 3
    "decimal_dotted",   # 1.1, 1.1.1
    "roman_upper",      # I, II, III
    "roman_lower",      # i, ii, iii
    "alpha_lower_paren",# (a), (b)
    "alpha_upper_paren",# (A), (B)
    "roman_lower_paren",# (i), (ii)
    "appendix",         # Appendix A
    "schedule",         # Schedule I
    "annexure",         # Annexure 1
    "none",
]


class NumberingMatch(BaseModel):
    block_id: str
    page: int
    raw_text: str
    scheme: NumberingScheme
    components: List[str]     # e.g. ["1", "2", "3"] for "1.2.3"
    depth: int                # nesting depth


class NumberingCollection(BaseModel):
    document_path: str
    total_matches: int
    detected_at: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )
    matches: List[NumberingMatch]


# ─────────────────────────────────────────────────────────────────────────────
# Module 5 — AST (placeholder)
# ─────────────────────────────────────────────────────────────────────────────

NodeType = Literal[
    "Document", "Part", "Chapter", "Section", "SubSection",
    "Clause", "Paragraph", "Bullet", "SubBullet",
    "Table", "Note", "Appendix", "Annexure",
]


class ASTNode(BaseModel):
    node_id: str
    node_type: NodeType
    text: str
    page: int
    bbox: Optional[BoundingBox] = None
    numbering: Optional[str] = None
    depth: int = 0
    children: List["ASTNode"] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


ASTNode.model_rebuild()


class ASTDocument(BaseModel):
    document_path: str
    built_at: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )
    root: ASTNode


# ─────────────────────────────────────────────────────────────────────────────
# Module 6 — Clauses (placeholder)
# ─────────────────────────────────────────────────────────────────────────────

class ExtractedClause(BaseModel):
    clause_id: str
    chapter: Optional[str] = None
    chapter_title: Optional[str] = None
    section: Optional[str] = None
    section_title: Optional[str] = None
    subsection: Optional[str] = None
    clause_number: Optional[str] = None
    page_number: int
    node_type: NodeType
    parent_text: Optional[str] = None
    text: str
    path: str           # e.g. "Chapter 1 > Section 2 > Clause 3"


class ClauseCollection(BaseModel):
    document_path: str
    total_clauses: int
    extracted_at: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )
    clauses: List[ExtractedClause]


# ─────────────────────────────────────────────────────────────────────────────
# Module 7 — Semantic Batches (placeholder)
# ─────────────────────────────────────────────────────────────────────────────

class SemanticBatch(BaseModel):
    batch_id: str
    clause_ids: List[str]
    page_range: List[int]           # [first_page, last_page]
    path_prefix: str                # Common ancestor path
    estimated_tokens: int
    text: str                       # Concatenated text for this batch


class SemanticBatchCollection(BaseModel):
    document_path: str
    total_batches: int
    total_clauses_batched: int
    built_at: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )
    batches: List[SemanticBatch]
