"""
SERA Ingestion Pipeline — Module 1: PDF Extraction
====================================================

Responsibility
--------------
Open a SEBI circular PDF and extract every text span exactly as PyMuPDF
reports it. No interpretation, no merging, no classification.

Only operation permitted at this stage: whitespace normalization
  - strip leading/trailing whitespace from each span text
  - collapse internal sequences of whitespace to a single space

Output
------
raw_spans.json  — RawSpanCollection (see models.py)

Algorithm
---------
For each page p in document:
  For each block b in p.get_text("dict")["blocks"]:
    skip non-text blocks (images, etc.)
    For each line l in b["lines"]:
      For each span s in l["spans"]:
        decode font flags bitmask
        normalize whitespace
        emit RawSpan

Font flags bitmask (PyMuPDF):
  bit 0  (0x01) → superscript
  bit 1  (0x02) → italic
  bit 2  (0x04) → serifed
  bit 3  (0x08) → monospaced
  bit 4  (0x10) → bold

SOLID adherence
---------------
  S — PDFExtractor does exactly one thing: extract raw spans
  O — Output format is a Pydantic model; changing schema does not touch extractor
  L — PDFExtractor can substitute any fitz.Document source
  I — Extractor exposes a single public method: extract()
  D — Extractor depends on pathlib.Path and fitz.Document abstractions
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF

from app.ingestion.models import (
    BoundingBox,
    FontFlags,
    RawSpan,
    RawSpanCollection,
)

logger = logging.getLogger(__name__)

# PyMuPDF font flag bitmask positions
_FLAG_SUPERSCRIPT = 0x01
_FLAG_ITALIC      = 0x02
_FLAG_SERIFED     = 0x04
_FLAG_MONOSPACED  = 0x08
_FLAG_BOLD        = 0x10

_WHITESPACE_RE = re.compile(r"\s+")


def _decode_flags(flags_int: int) -> FontFlags:
    """Decode PyMuPDF's integer bitmask into a named FontFlags model."""
    return FontFlags(
        superscript=bool(flags_int & _FLAG_SUPERSCRIPT),
        italic=bool(flags_int & _FLAG_ITALIC),
        serifed=bool(flags_int & _FLAG_SERIFED),
        monospaced=bool(flags_int & _FLAG_MONOSPACED),
        bold=bool(flags_int & _FLAG_BOLD),
    )


def _normalize_text(text: str) -> str:
    """
    Only permissible transformation at extraction stage:
    strip + collapse internal whitespace sequences to a single space.
    Preserves meaningful newlines only indirectly (spans are line-level).
    """
    return _WHITESPACE_RE.sub(" ", text).strip()


class PDFExtractor:
    """
    Extracts raw text spans from a PDF file using PyMuPDF.

    Usage
    -----
    extractor = PDFExtractor(Path("downloads/SEBI-CIRC-2026-08-03-103314.pdf"))
    collection = extractor.extract()
    """

    def __init__(self, pdf_path: Path) -> None:
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        if pdf_path.suffix.lower() != ".pdf":
            raise ValueError(f"Expected a .pdf file, got: {pdf_path.suffix}")
        self._pdf_path = pdf_path

    def extract(self) -> RawSpanCollection:
        """
        Open the PDF and extract every span into a RawSpanCollection.

        Returns
        -------
        RawSpanCollection
            Complete structured extraction ready for serialisation to
            raw_spans.json.
        """
        logger.info(f"Opening PDF: {self._pdf_path}")
        doc = fitz.open(str(self._pdf_path))
        page_count = len(doc)
        logger.info(f"Page count: {page_count}")

        spans: list[RawSpan] = []
        span_global_idx = 0

        for page_num, page in enumerate(doc):
            # get_text("dict") returns the full layout dictionary
            page_dict = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)

            for block_idx, block in enumerate(page_dict["blocks"]):
                # Block type 0 = text, 1 = image — skip non-text
                if block.get("type") != 0:
                    logger.debug(
                        f"Skipping non-text block {block_idx} on page {page_num}"
                    )
                    continue

                for line_idx, line in enumerate(block.get("lines", [])):
                    for span_idx, raw_span in enumerate(line.get("spans", [])):
                        text = _normalize_text(raw_span.get("text", ""))

                        # Skip spans that are purely whitespace after normalization
                        if not text:
                            continue

                        origin = raw_span.get("origin", (0.0, 0.0))
                        bbox_tuple = raw_span.get("bbox", (0.0, 0.0, 0.0, 0.0))

                        span = RawSpan(
                            page=page_num,
                            block=block_idx,
                            line=line_idx,
                            span=span_idx,
                            text=text,
                            font=raw_span.get("font", ""),
                            size=round(raw_span.get("size", 0.0), 3),
                            flags=_decode_flags(raw_span.get("flags", 0)),
                            bbox=BoundingBox(
                                x0=round(bbox_tuple[0], 3),
                                y0=round(bbox_tuple[1], 3),
                                x1=round(bbox_tuple[2], 3),
                                y1=round(bbox_tuple[3], 3),
                            ),
                            color=raw_span.get("color", 0),
                            origin_x=round(origin[0], 3),
                            origin_y=round(origin[1], 3),
                        )
                        spans.append(span)
                        span_global_idx += 1

        doc.close()

        collection = RawSpanCollection(
            document_path=str(self._pdf_path.resolve()),
            page_count=page_count,
            total_spans=len(spans),
            spans=spans,
        )

        logger.info(
            f"Extraction complete — {len(spans)} spans across {page_count} pages"
        )
        return collection

    def extract_to_file(self, output_path: Optional[Path] = None) -> Path:
        """
        Extract and write raw_spans.json to disk.

        Parameters
        ----------
        output_path : Path, optional
            Destination file. Defaults to data/pipeline_output/<stem>/raw_spans.json.

        Returns
        -------
        Path
            Path to the written JSON file.
        """
        collection = self.extract()

        if output_path is None:
            base = Path(__file__).resolve().parent.parent.parent / "data" / "pipeline_output"
            output_path = base / self._pdf_path.stem / "raw_spans.json"

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            collection.model_dump_json(indent=2), encoding="utf-8"
        )
        logger.info(f"raw_spans.json written to: {output_path}")
        return output_path


if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    )

    # Default to the first PDF in downloads/ if no argument given
    if len(sys.argv) > 1:
        pdf_path = Path(sys.argv[1])
    else:
        downloads = Path(__file__).resolve().parent.parent.parent / "downloads"
        pdfs = sorted(downloads.glob("*.pdf"))
        if not pdfs:
            print("No PDFs found in downloads/")
            sys.exit(1)
        pdf_path = pdfs[0]

    extractor = PDFExtractor(pdf_path)
    out = extractor.extract_to_file()

    # Print a summary preview
    collection = PDFExtractor(pdf_path).extract()
    print(f"\n[OK] Extracted {collection.total_spans} spans from {collection.page_count} pages")
    print(f"[OK] Output: {out}\n")
    print("-- First 5 spans ---------------------------------------------------")
    for s in collection.spans[:5]:
        bold_marker = "[BOLD]" if s.flags.bold else "      "
        print(
            f"  p{s.page} b{s.block} l{s.line} s{s.span} "
            f"sz={s.size:.1f} {bold_marker} font={s.font!r:30s} text={s.text!r}"
        )
