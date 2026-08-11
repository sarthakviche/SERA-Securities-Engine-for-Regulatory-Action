"""
SERA Ingestion Pipeline — Module 4: Numbering Detection
=========================================================

Responsibility
--------------
Identify list and clause numbering markers at the beginning of layout blocks.

Supported Schemes
-----------------
- decimal: 1.
- decimal_dotted: 1.1, 1.1.1
- roman_upper: I., II.
- roman_lower: i., ii.
- alpha_lower_paren: (a), (b)
- alpha_upper_paren: (A), (B)
- roman_lower_paren: (i), (ii)
- appendix: Appendix A
- schedule: Schedule 1
- annexure: Annexure I

Output
------
NumberingCollection containing NumberingMatch objects.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import List, Optional

from app.ingestion.models import (
    LayoutCollection,
    NumberingCollection,
    NumberingMatch,
    NumberingScheme,
)

logger = logging.getLogger(__name__)

# Regex definitions for each scheme
# Using capturing groups for the core identifier(s)
SCHEME_PATTERNS = {
    # 1.1.1 or 1.1 (must have at least one dot)
    "decimal_dotted": re.compile(r"^\s*(\d+(?:\.\d+)+)[\.\s]"),
    
    # 1. or 2.
    "decimal": re.compile(r"^\s*(\d+)\."),
    
    # (a), (b)
    "alpha_lower_paren": re.compile(r"^\s*\(([a-z])\)"),
    
    # (A), (B)
    "alpha_upper_paren": re.compile(r"^\s*\(([A-Z])\)"),
    
    # (i), (ii), (iv)
    "roman_lower_paren": re.compile(r"^\s*\(([ivxlcdm]+)\)"),
    
    # I., II., IV. (Require a dot to avoid catching normal words like "I")
    "roman_upper": re.compile(r"^\s*([IVXLCDM]+)\."),
    
    # i., ii.
    "roman_lower": re.compile(r"^\s*([ivxlcdm]+)\."),
    
    # Appendix A, Appendix 1
    "appendix": re.compile(r"^\s*Appendix\s+([A-Z0-9]+)", re.IGNORECASE),
    
    # Schedule I, Schedule 1
    "schedule": re.compile(r"^\s*Schedule\s+([A-Z0-9]+)", re.IGNORECASE),
    
    # Annexure A, Annexure 1
    "annexure": re.compile(r"^\s*Annexure\s+([A-Z0-9]+)", re.IGNORECASE),
}


class NumberingDetector:
    def __init__(self, layout_collection: LayoutCollection) -> None:
        self.layout = layout_collection

    def _extract_components(self, scheme: NumberingScheme, match: re.Match) -> List[str]:
        """Extracts the structural components from the regex match."""
        raw_val = match.group(1)
        
        if scheme == "decimal_dotted":
            # "1.2.3" -> ["1", "2", "3"]
            return raw_val.split(".")
            
        # For everything else, it's a single level component
        # e.g., "A", "iv", "1"
        return [raw_val]

    def detect(self) -> NumberingCollection:
        logger.info(f"Detecting numbering for {self.layout.document_path}")

        matches: List[NumberingMatch] = []

        for block in self.layout.blocks:
            # Skip non-content regions
            if block.region_type in ("page_number", "header", "footer", "note"):
                continue

            text = block.text
            if not text:
                continue

            # Try to match patterns in order of specificity (most specific first)
            # dict keys order in Python 3.7+ is insertion order, so SCHEME_PATTERNS
            # is ordered correctly (e.g. decimal_dotted before decimal).
            for scheme_name, pattern in SCHEME_PATTERNS.items():
                match = pattern.match(text)
                if match:
                    components = self._extract_components(scheme_name, match) # type: ignore
                    
                    num_match = NumberingMatch(
                        block_id=block.block_id,
                        page=block.page,
                        raw_text=match.group(0).strip(),
                        scheme=scheme_name, # type: ignore
                        components=components,
                        depth=len(components)
                    )
                    matches.append(num_match)
                    break # Stop at first matching scheme

        collection = NumberingCollection(
            document_path=self.layout.document_path,
            total_matches=len(matches),
            matches=matches
        )

        logger.info(f"Numbering detection complete — {len(matches)} numbered blocks found")
        return collection

    def detect_to_file(self, output_path: Optional[Path] = None) -> Path:
        collection = self.detect()

        if output_path is None:
            base = Path(__file__).resolve().parent.parent.parent / "data" / "pipeline_output"
            stem = Path(self.layout.document_path).stem
            output_path = base / stem / "numbering.json"

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            collection.model_dump_json(indent=2), encoding="utf-8"
        )
        logger.info(f"numbering.json written to: {output_path}")
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

    layout_path = target_dir / "layout.json"

    if not layout_path.exists():
        print(f"Missing layout.json in {target_dir}")
        sys.exit(1)

    layout_coll = LayoutCollection.model_validate_json(layout_path.read_text(encoding="utf-8"))

    detector = NumberingDetector(layout_coll)
    out = detector.detect_to_file()
    collection = detector.detect()

    print(f"\n[OK] Detected {collection.total_matches} numbered blocks")
    print(f"[OK] Output: {out}\n")
    print("-- Matches --------------------------------------------------------")
    for m in collection.matches:
        print(f"  [{m.scheme:18s}] (depth {m.depth}) {m.raw_text:10s} -> {m.components}")
