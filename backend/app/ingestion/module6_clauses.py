"""
SERA Ingestion Pipeline — Module 6: Clause Extraction
======================================================

Responsibility
--------------
Flatten the AST into a list of standalone ExtractedClause objects.
Each clause carries its full hierarchical context (Chapter, Section, etc.)
and the text of its immediate parent if it is a sub-element (like a bullet).

Algorithm
---------
1. Traverse the AST using Depth First Search (DFS).
2. Maintain a running context of the current Chapter, Section, SubSection,
   and current Clause number.
3. Keep track of `parent_text` (e.g., the text of the Clause that owns 
   a Paragraph or Bullet).
4. Emit an ExtractedClause for every substantive node:
   - Clause
   - Paragraph
   - Bullet / SubBullet
   - Note
   - Table
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import List, Optional

from app.ingestion.models import (
    ASTDocument,
    ASTNode,
    ClauseCollection,
    ExtractedClause,
)

logger = logging.getLogger(__name__)


class ClauseContext:
    """Mutable context passed down during DFS traversal."""
    def __init__(self):
        self.chapter_title: Optional[str] = None
        self.section_title: Optional[str] = None
        self.subsection_title: Optional[str] = None
        self.clause_number: Optional[str] = None
        self.parent_text: Optional[str] = None
        
    def clone(self) -> "ClauseContext":
        ctx = ClauseContext()
        ctx.chapter_title = self.chapter_title
        ctx.section_title = self.section_title
        ctx.subsection_title = self.subsection_title
        ctx.clause_number = self.clause_number
        ctx.parent_text = self.parent_text
        return ctx

    def build_path_string(self) -> str:
        parts = []
        if self.chapter_title:
            parts.append(f"[{self.chapter_title}]")
        if self.section_title:
            parts.append(f"[{self.section_title}]")
        if self.subsection_title:
            parts.append(f"[{self.subsection_title}]")
        if self.clause_number:
            parts.append(f"Clause {self.clause_number}")
        
        if not parts:
            return "Document Root"
        return " > ".join(parts)


class ClauseExtractor:
    def __init__(self, ast_document: ASTDocument) -> None:
        self.ast = ast_document
        self.clauses: List[ExtractedClause] = []

    def _traverse(self, node: ASTNode, ctx: ClauseContext):
        # 1. Update Context based on current node
        new_ctx = ctx.clone()
        
        if node.node_type == "Chapter" or node.node_type == "Part":
            new_ctx.chapter_title = node.text
            new_ctx.section_title = None
            new_ctx.subsection_title = None
            new_ctx.clause_number = None
            new_ctx.parent_text = None
        elif node.node_type == "Section":
            new_ctx.section_title = node.text
            new_ctx.subsection_title = None
            new_ctx.clause_number = None
            new_ctx.parent_text = None
        elif node.node_type == "SubSection":
            new_ctx.subsection_title = node.text
            new_ctx.clause_number = None
            new_ctx.parent_text = None
        elif node.node_type == "Clause":
            if node.numbering:
                new_ctx.clause_number = node.numbering
            # For clauses, we also want to set this node's text as parent_text
            # for any child paragraphs/bullets.
            new_ctx.parent_text = node.text

        # 2. Decide whether to emit an ExtractedClause
        # We emit for nodes that hold actual text substance
        substantive_types = {"Clause", "Paragraph", "Bullet", "Note", "Table"}
        
        if node.node_type in substantive_types and node.text.strip():
            clause_id = f"c_{len(self.clauses)}"
            
            # If the node itself is a Clause, its own text is the main text,
            # and its parent_text should be from the previous context level.
            # (But we already updated new_ctx.parent_text above, so we must use ctx for parent_text)
            actual_parent_text = ctx.parent_text if node.node_type == "Clause" else new_ctx.parent_text

            ec = ExtractedClause(
                clause_id=clause_id,
                chapter_title=new_ctx.chapter_title,
                section_title=new_ctx.section_title,
                subsection_title=new_ctx.subsection_title,
                clause_number=new_ctx.clause_number,
                page_number=node.page,
                node_type=node.node_type,
                parent_text=actual_parent_text,
                text=node.text,
                path=new_ctx.build_path_string()
            )
            self.clauses.append(ec)

            # If this is a substantive node (like a paragraph), it becomes the parent_text
            # for any nested sub-bullets underneath it.
            new_ctx.parent_text = node.text

        # 3. Recurse into children
        for child in node.children:
            self._traverse(child, new_ctx)

    def extract(self) -> ClauseCollection:
        logger.info(f"Extracting clauses from AST for {self.ast.document_path}")
        
        self.clauses = []
        initial_context = ClauseContext()
        self._traverse(self.ast.root, initial_context)
        
        collection = ClauseCollection(
            document_path=self.ast.document_path,
            total_clauses=len(self.clauses),
            clauses=self.clauses
        )
        
        logger.info(f"Clause extraction complete — {len(self.clauses)} substantive clauses extracted")
        return collection

    def extract_to_file(self, output_path: Optional[Path] = None) -> Path:
        collection = self.extract()

        if output_path is None:
            base = Path(__file__).resolve().parent.parent.parent / "data" / "pipeline_output"
            stem = Path(self.ast.document_path).stem
            output_path = base / stem / "clauses.json"

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            collection.model_dump_json(indent=2), encoding="utf-8"
        )
        logger.info(f"clauses.json written to: {output_path}")
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

    ast_path = target_dir / "ast.json"
    if not ast_path.exists():
        print(f"Missing ast.json in {target_dir}")
        sys.exit(1)

    ast_doc = ASTDocument.model_validate_json(ast_path.read_text(encoding="utf-8"))

    extractor = ClauseExtractor(ast_doc)
    out = extractor.extract_to_file()
    collection = extractor.extract()

    print(f"\n[OK] Extracted {collection.total_clauses} clauses")
    print(f"[OK] Output: {out}\n")
    print("-- First 5 Clauses ------------------------------------------------")
    for c in collection.clauses[:5]:
        safe_path = c.path.encode("ascii", "ignore").decode("ascii")
        safe_text = c.text[:60].replace("\n", " ").encode("ascii", "ignore").decode("ascii")
        print(f"  [{c.node_type:9s}] path: {safe_path}")
        print(f"            text: {safe_text}...")
