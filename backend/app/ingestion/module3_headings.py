"""
SERA Ingestion Pipeline — Module 3: Heading Detection
======================================================

Responsibility
--------------
Identify which layout blocks act as structural headings and classify
their hierarchical level (Part, Chapter, Section, etc.).

Rules
-----
1. A block is a candidate heading if:
   - It is relatively short (< 200 characters)
   - It is mostly bold OR entirely uppercase
   - It is not a page number or footer.
2. Cross-reference `span_indices` with the `RawSpanCollection` to determine:
   - is_bold (if >50% of text characters in the block are bold)
   - max_font_size
3. Level Classification:
   - document_title: The first large, centered, bold text on page 0.
   - part / chapter: Explicitly starts with "PART" or "CHAPTER".
   - section / subsection / clause_heading: Ranked by font size hierarchy.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional

from app.ingestion.models import (
    DetectedHeading,
    HeadingCollection,
    HeadingLevel,
    LayoutBlock,
    LayoutCollection,
    RawSpan,
    RawSpanCollection,
)

logger = logging.getLogger(__name__)

PART_RE = re.compile(r"^PART\s+[A-Z0-9]+", re.IGNORECASE)
CHAPTER_RE = re.compile(r"^CHAPTER\s+[A-Z0-9]+", re.IGNORECASE)


class HeadingDetector:
    def __init__(
        self, layout_collection: LayoutCollection, raw_collection: RawSpanCollection
    ) -> None:
        self.layout = layout_collection
        self.raw = raw_collection
        self.raw_spans = raw_collection.spans

    def _analyze_block_font(self, block: LayoutBlock) -> tuple[bool, float]:
        """Returns (is_bold, max_font_size) for the block."""
        if not block.span_indices:
            return False, 0.0

        total_chars = 0
        bold_chars = 0
        max_size = 0.0

        for idx in block.span_indices:
            span = self.raw_spans[idx]
            char_count = len(span.text)
            total_chars += char_count
            if span.flags.bold:
                bold_chars += char_count
            if span.size > max_size:
                max_size = span.size

        is_bold = (bold_chars / total_chars) >= 0.5 if total_chars > 0 else False
        return is_bold, max_size

    def _is_uppercase(self, text: str) -> bool:
        alpha_chars = [c for c in text if c.isalpha()]
        if not alpha_chars:
            return False
        return all(c.isupper() for c in alpha_chars)

    def detect(self) -> HeadingCollection:
        logger.info(f"Detecting headings for {self.layout.document_path}")

        candidates: List[DetectedHeading] = []
        doc_title_found = False

        for block in self.layout.blocks:
            if block.region_type in ("page_number", "footer", "note"):
                continue

            text = block.text.strip()
            if not text or len(text) > 200:
                continue

            is_bold, max_size = self._analyze_block_font(block)
            is_uppercase = self._is_uppercase(text)

            # Rule: Must be bold OR uppercase to be considered a heading
            if not (is_bold or is_uppercase):
                continue

            # Determine level
            level: HeadingLevel = "clause_heading"

            if not doc_title_found and block.page == 0 and block.alignment == "center" and is_bold:
                level = "document_title"
                doc_title_found = True
            elif PART_RE.match(text):
                level = "part"
            elif CHAPTER_RE.match(text):
                level = "chapter"
            else:
                # We defer section/subsection classification to a second pass
                # based on relative font sizes. For now, mark as "clause_heading".
                level = "clause_heading"

            heading = DetectedHeading(
                heading_id=f"h_{block.block_id}",
                page=block.page,
                level=level,
                text=text,
                block_id=block.block_id,
                bbox=block.bbox,
                font_size=max_size,
                is_bold=is_bold,
                is_uppercase=is_uppercase,
            )
            candidates.append(heading)

        # Second Pass: Rank generic headings by font size
        # Find all distinct font sizes among generic headings
        generic_headings = [h for h in candidates if h.level == "clause_heading"]
        if generic_headings:
            sizes = sorted(list(set(h.font_size for h in generic_headings)), reverse=True)
            
            # Map top sizes to hierarchical levels
            for h in generic_headings:
                size_rank = sizes.index(h.font_size)
                if size_rank == 0:
                    h.level = "section"
                elif size_rank == 1:
                    h.level = "subsection"
                else:
                    h.level = "clause_heading"

        collection = HeadingCollection(
            document_path=self.layout.document_path,
            total_headings=len(candidates),
            headings=candidates,
        )

        logger.info(f"Heading detection complete — {len(candidates)} headings found")
        return collection

    def detect_to_file(self, output_path: Optional[Path] = None) -> Path:
        collection = self.detect()

        if output_path is None:
            base = Path(__file__).resolve().parent.parent.parent / "data" / "pipeline_output"
            stem = Path(self.layout.document_path).stem
            output_path = base / stem / "headings.json"

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            collection.model_dump_json(indent=2), encoding="utf-8"
        )
        logger.info(f"headings.json written to: {output_path}")
        return output_path


if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    )

    base = Path(__file__).resolve().parent.parent.parent / "data" / "pipeline_output"
    
    if len(sys.argv) > 1:
        stem = Path(sys.argv[1]).stem
        target_dir = base / stem
    else:
        dirs = [d for d in base.iterdir() if d.is_dir()]
        if not dirs:
            print("No pipeline output found. Run module 2 first.")
            sys.exit(1)
        target_dir = sorted(dirs, key=lambda d: d.stat().st_mtime, reverse=True)[0]

    raw_path = target_dir / "raw_spans.json"
    layout_path = target_dir / "layout.json"

    if not raw_path.exists() or not layout_path.exists():
        print(f"Missing input JSONs in {target_dir}")
        sys.exit(1)

    raw_coll = RawSpanCollection.model_validate_json(raw_path.read_text(encoding="utf-8"))
    layout_coll = LayoutCollection.model_validate_json(layout_path.read_text(encoding="utf-8"))

    detector = HeadingDetector(layout_coll, raw_coll)
    out = detector.detect_to_file()
    collection = detector.detect()

    print(f"\n[OK] Detected {collection.total_headings} headings")
    print(f"[OK] Output: {out}\n")
    print("-- Headings --------------------------------------------------------")
    for h in collection.headings:
        print(f"  [{h.level:15s}] (size {h.font_size:4.1f}) {h.text}")
