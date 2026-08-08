"""
SERA Ingestion Pipeline — Module 2: Layout Analysis
=====================================================

Responsibility
--------------
Take the raw spans from Module 1 and reconstruct layout blocks.
Identify basic page regions and text alignment using deterministic rules.

Rules
-----
- Group spans by `(page, block)` ID.
- Calculate overall bounding box for the block.
- Reconstruct text by joining spans (with a space if they are on the same line,
  or a newline/space if they break lines, but for simplicity here we just join with spaces).
- Determine Region Type:
    - Header: y0 < 80
    - Footer: y1 > 760
    - Page Number: Header or Footer block containing only digits or "page X of Y"
    - Note: Text starts with "Note:" or "Notes:"
    - Bullet List: Text starts with standard bullet chars (•, ▪, -, *, etc.)
    - Paragraph / Indented Block: Everything else.
- Calculate Indentation:
    - Base margin is roughly 72 points (1 inch).
    - Each 18 points (0.25 inches) beyond the margin is 1 indent level.
- Calculate Alignment (assuming A4 page 595 width):
    - Center: Midpoint of bbox is near 297.5
    - Right: x1 is near 595 - 72 = 523
    - Justify: x0 near 72 AND x1 near 523
    - Left: default
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from app.ingestion.models import (
    BoundingBox,
    LayoutBlock,
    LayoutCollection,
    RawSpan,
    RawSpanCollection,
    RegionType,
)

logger = logging.getLogger(__name__)

# Constants for A4 page size in points
PAGE_WIDTH = 595.0
PAGE_HEIGHT = 842.0

BASE_MARGIN_X = 72.0
INDENT_STEP = 18.0

HEADER_Y = 80.0
FOOTER_Y = 760.0

PAGE_NUM_RE = re.compile(r"^\s*(?:page\s*)?(?:\d+|[ivx]+)(?:\s*of\s*\d+)?\s*$", re.IGNORECASE)
NOTE_RE = re.compile(r"^\s*note\s*s?\s*:", re.IGNORECASE)
BULLET_RE = re.compile(r"^\s*[•▪\-\*oO]\s+")


class LayoutAnalyzer:
    """
    Groups RawSpans into LayoutBlocks and applies deterministic classification.
    """

    def __init__(self, raw_collection: RawSpanCollection) -> None:
        self.collection = raw_collection

    def _group_spans(self) -> Dict[Tuple[int, int], List[RawSpan]]:
        """Groups spans by (page, block)."""
        groups: Dict[Tuple[int, int], List[RawSpan]] = {}
        for span in self.collection.spans:
            key = (span.page, span.block)
            if key not in groups:
                groups[key] = []
            groups[key].append(span)
        return groups

    def _calculate_bbox(self, spans: List[RawSpan]) -> BoundingBox:
        """Calculates the bounding box that encompasses all spans in the block."""
        x0 = min(s.bbox.x0 for s in spans)
        y0 = min(s.bbox.y0 for s in spans)
        x1 = max(s.bbox.x1 for s in spans)
        y1 = max(s.bbox.y1 for s in spans)
        return BoundingBox(x0=x0, y0=y0, x1=x1, y1=y1)

    def _reconstruct_text(self, spans: List[RawSpan]) -> str:
        """Reconstructs the block's text by joining spans with spaces."""
        # Simple join for now. Module 1 normalized whitespaces within spans.
        return " ".join(s.text for s in spans).strip()

    def _determine_region_type(self, bbox: BoundingBox, text: str) -> RegionType:
        """Deterministically classifies the region type based on position and text."""
        # Header / Footer
        if bbox.y0 < HEADER_Y:
            if PAGE_NUM_RE.match(text):
                return "page_number"
            return "header"
        
        if bbox.y1 > FOOTER_Y:
            if PAGE_NUM_RE.match(text):
                return "page_number"
            return "footer"

        # Note
        if NOTE_RE.match(text):
            return "note"

        # Bullet List (only visual bullets, numbering is Module 4)
        if BULLET_RE.match(text):
            return "bullet_list"

        # Default Paragraph
        return "paragraph"

    def _calculate_indent_level(self, bbox: BoundingBox) -> int:
        """Calculates indentation level based on x0 position."""
        if bbox.x0 <= BASE_MARGIN_X:
            return 0
        
        # Calculate how far past the margin it is
        excess = bbox.x0 - BASE_MARGIN_X
        level = int(round(excess / INDENT_STEP))
        return max(0, level)

    def _determine_alignment(self, bbox: BoundingBox) -> str:
        """Determines alignment based on x0, x1 and page width."""
        width = bbox.width
        midpoint = bbox.x0 + (width / 2.0)
        
        page_center = PAGE_WIDTH / 2.0
        right_margin = PAGE_WIDTH - BASE_MARGIN_X

        is_left_aligned = bbox.x0 <= BASE_MARGIN_X + 5
        is_right_aligned = bbox.x1 >= right_margin - 5

        if is_left_aligned and is_right_aligned:
            return "justify"
        elif is_right_aligned:
            return "right"
        elif abs(midpoint - page_center) < 15:
            return "center"
        else:
            return "left"

    def analyze(self) -> LayoutCollection:
        """
        Executes the layout analysis on the provided RawSpanCollection.
        """
        logger.info(f"Analyzing layout for {self.collection.document_path}")
        groups = self._group_spans()
        
        blocks: List[LayoutBlock] = []
        global_span_index = 0
        
        # Ensure we process pages in order, and blocks in order
        for (page, block_idx) in sorted(groups.keys()):
            spans = groups[(page, block_idx)]
            
            bbox = self._calculate_bbox(spans)
            text = self._reconstruct_text(spans)
            region_type = self._determine_region_type(bbox, text)
            indent_level = self._calculate_indent_level(bbox)
            alignment = self._determine_alignment(bbox)
            
            # Map the span indices for traceability
            span_indices = list(range(global_span_index, global_span_index + len(spans)))
            global_span_index += len(spans)
            
            # If it's a paragraph but indented, refine the type
            if region_type == "paragraph" and indent_level > 0:
                region_type = "indented_block"

            block_id = f"p{page}_b{block_idx}"
            
            block = LayoutBlock(
                block_id=block_id,
                page=page,
                region_type=region_type,
                bbox=bbox,
                indent_level=indent_level,
                alignment=alignment,
                span_indices=span_indices,
                text=text
            )
            blocks.append(block)

        collection = LayoutCollection(
            document_path=self.collection.document_path,
            page_count=self.collection.page_count,
            total_blocks=len(blocks),
            blocks=blocks
        )
        
        logger.info(f"Layout analysis complete — {len(blocks)} blocks identified")
        return collection

    def analyze_to_file(self, output_path: Optional[Path] = None) -> Path:
        """
        Execute analysis and write layout.json to disk.
        """
        collection = self.analyze()
        
        if output_path is None:
            base = Path(__file__).resolve().parent.parent.parent / "data" / "pipeline_output"
            # Get the stem from the document path
            stem = Path(self.collection.document_path).stem
            output_path = base / stem / "layout.json"
            
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            collection.model_dump_json(indent=2), encoding="utf-8"
        )
        logger.info(f"layout.json written to: {output_path}")
        return output_path


if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    )

    if len(sys.argv) > 1:
        raw_spans_path = Path(sys.argv[1])
    else:
        # Default to the most recently generated raw_spans.json
        base = Path(__file__).resolve().parent.parent.parent / "data" / "pipeline_output"
        files = list(base.rglob("raw_spans.json"))
        if not files:
            print("No raw_spans.json found. Run module1_extractor.py first.")
            sys.exit(1)
        # Sort by modification time to get the latest
        raw_spans_path = sorted(files, key=lambda f: f.stat().st_mtime, reverse=True)[0]

    logger.info(f"Loading raw spans from {raw_spans_path}")
    raw_data = json.loads(raw_spans_path.read_text(encoding="utf-8"))
    raw_collection = RawSpanCollection.model_validate(raw_data)
    
    analyzer = LayoutAnalyzer(raw_collection)
    out = analyzer.analyze_to_file()
    
    collection = analyzer.analyze()
    print(f"\n[OK] Reconstructed {collection.total_blocks} layout blocks")
    print(f"[OK] Output: {out}\n")
    print("-- First 5 blocks --------------------------------------------------")
    for b in collection.blocks[:5]:
        print(
            f"  {b.block_id:6s} {b.region_type:15s} align={b.alignment:7s} "
            f"indent={b.indent_level} text={b.text[:50]!r}..."
        )
