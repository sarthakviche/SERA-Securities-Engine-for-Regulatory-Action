"""
SERA Ingestion Pipeline — Module 7: Semantic Batches
======================================================

Responsibility
--------------
Group sequentially extracted clauses into semantic batches of a 
target token size. Respects structural boundaries (e.g. Chapter changes)
to ensure semantic coherence within the batch.

Algorithm
---------
1. Read ExtractedClauses.
2. Estimate tokens = word_count * 1.3
3. Accumulate clauses into a batch.
4. Break batch if:
   - Token limit exceeded (e.g. > 500 tokens)
   - Structural boundary crossed (e.g. Chapter changes)
5. Format the final batch text to include the hierarchical path and
   parent context, so the chunk is fully self-contained.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import List, Optional

from app.ingestion.models import (
    ClauseCollection,
    ExtractedClause,
    SemanticBatch,
    SemanticBatchCollection,
)

logger = logging.getLogger(__name__)

# Heuristic: 1 word ~ 1.3 tokens for typical English text
TOKEN_RATIO = 1.3
MAX_TOKENS_PER_BATCH = 500


class SemanticBatcher:
    def __init__(self, clause_collection: ClauseCollection, max_tokens: int = MAX_TOKENS_PER_BATCH) -> None:
        self.collection = clause_collection
        self.max_tokens = max_tokens
        self.batches: List[SemanticBatch] = []

    def _estimate_tokens(self, text: str) -> int:
        if not text:
            return 0
        words = len(text.split())
        return int(words * TOKEN_RATIO)

    def _format_clause_for_batch(self, clause: ExtractedClause) -> str:
        """
        Formats a single clause into a self-contained text block.
        Includes path and parent text for context.
        """
        parts = []
        parts.append(f"Location: {clause.path}")
        if clause.parent_text and clause.parent_text != clause.text:
            parts.append(f"Context: {clause.parent_text}")
        parts.append(f"Content: {clause.text}")
        return "\n".join(parts)

    def _finalize_batch(self, current_clauses: List[ExtractedClause]) -> None:
        if not current_clauses:
            return

        batch_id = f"b_{len(self.batches)}"
        clause_ids = [c.clause_id for c in current_clauses]
        pages = [c.page_number for c in current_clauses]
        page_range = [min(pages), max(pages)]
        
        # Path prefix (simplistic: use path of the first clause)
        path_prefix = current_clauses[0].path

        # Concatenate formatted text
        formatted_texts = [self._format_clause_for_batch(c) for c in current_clauses]
        full_text = "\n\n---\n\n".join(formatted_texts)
        
        tokens = self._estimate_tokens(full_text)

        batch = SemanticBatch(
            batch_id=batch_id,
            clause_ids=clause_ids,
            page_range=page_range,
            path_prefix=path_prefix,
            estimated_tokens=tokens,
            text=full_text
        )
        self.batches.append(batch)

    def batch(self) -> SemanticBatchCollection:
        logger.info(f"Building semantic batches for {self.collection.document_path}")
        self.batches = []
        
        current_clauses: List[ExtractedClause] = []
        current_tokens = 0
        current_chapter = None

        for clause in self.collection.clauses:
            formatted_text = self._format_clause_for_batch(clause)
            tokens = self._estimate_tokens(formatted_text)

            # Check boundaries
            chapter_changed = (clause.chapter_title != current_chapter) and (current_chapter is not None)
            token_overflow = (current_tokens + tokens) > self.max_tokens

            if current_clauses and (chapter_changed or token_overflow):
                self._finalize_batch(current_clauses)
                current_clauses = []
                current_tokens = 0

            current_clauses.append(clause)
            current_tokens += tokens
            current_chapter = clause.chapter_title

        # Finalize remaining
        if current_clauses:
            self._finalize_batch(current_clauses)

        collection = SemanticBatchCollection(
            document_path=self.collection.document_path,
            total_batches=len(self.batches),
            total_clauses_batched=len(self.collection.clauses),
            batches=self.batches
        )
        
        logger.info(f"Semantic batching complete — {len(self.batches)} batches created")
        return collection

    def batch_to_file(self, output_path: Optional[Path] = None) -> Path:
        collection = self.batch()

        if output_path is None:
            base = Path(__file__).resolve().parent.parent.parent / "data" / "pipeline_output"
            stem = Path(self.collection.document_path).stem
            output_path = base / stem / "semantic_batches.json"

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            collection.model_dump_json(indent=2), encoding="utf-8"
        )
        logger.info(f"semantic_batches.json written to: {output_path}")
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
            print("No pipeline output found. Run previous modules first.")
            sys.exit(1)
        target_dir = sorted(dirs, key=lambda d: d.stat().st_mtime, reverse=True)[0]

    clauses_path = target_dir / "clauses.json"
    if not clauses_path.exists():
        print(f"Missing clauses.json in {target_dir}")
        sys.exit(1)

    clause_doc = ClauseCollection.model_validate_json(clauses_path.read_text(encoding="utf-8"))

    batcher = SemanticBatcher(clause_doc, max_tokens=150) # Use small max_tokens for demo
    out = batcher.batch_to_file()
    collection = batcher.batch()

    print(f"\n[OK] Created {collection.total_batches} batches")
    print(f"[OK] Output: {out}\n")
    print("-- First Batch ----------------------------------------------------")
    if collection.batches:
        b = collection.batches[0]
        print(f"ID: {b.batch_id}")
        print(f"Pages: {b.page_range}")
        print(f"Tokens: {b.estimated_tokens}")
        print("Text:\n")
        safe_text = b.text.encode("ascii", "ignore").decode("ascii")
        print(safe_text)
