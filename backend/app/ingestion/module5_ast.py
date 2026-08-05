"""
SERA Ingestion Pipeline — Module 5: AST Builder
===============================================

Responsibility
--------------
Convert the flat list of layout blocks into a hierarchical tree (AST).

Algorithm
---------
1. Read Layout, Heading, and Numbering collections.
2. Maintain a stack of active parent nodes.
3. Determine the structural rank of each block:
    Root = 0
    Part = 10
    Chapter = 20
    Section = 30
    SubSection = 40
    ClauseHeading = 50
    Clause (depth N) = 60 + N
    Paragraph / Note / Bullet = 100
4. For each block:
    - Determine its rank.
    - Pop the stack until the top node has a rank strictly LESS than the new node.
    - Append the new node as a child of the top node.
    - Push the new node onto the stack.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from app.ingestion.models import (
    ASTDocument,
    ASTNode,
    HeadingCollection,
    LayoutCollection,
    NodeType,
    NumberingCollection,
)

logger = logging.getLogger(__name__)

# Structural Hierarchy Ranks (lower number = higher up in the tree)
RANK_ROOT = 0
RANK_DOCUMENT_TITLE = 5
RANK_PART = 10
RANK_CHAPTER = 20
RANK_SECTION = 30
RANK_SUBSECTION = 40
RANK_CLAUSE_HEADING = 50
RANK_CLAUSE_BASE = 60
RANK_LEAF = 100


class ASTBuilder:
    def __init__(
        self,
        layout: LayoutCollection,
        headings: HeadingCollection,
        numbering: NumberingCollection,
    ) -> None:
        self.layout = layout
        self.headings = {h.block_id: h for h in headings.headings}
        self.numbering = {n.block_id: n for n in numbering.matches}

    def _determine_node_props(self, block_id: str, text: str, region_type: str) -> tuple[NodeType, int, Optional[str], int]:
        """Returns (node_type, rank, numbering_str, depth)"""
        
        # 1. Is it a Heading?
        if block_id in self.headings:
            h = self.headings[block_id]
            if h.level == "document_title":
                return "Document", RANK_DOCUMENT_TITLE, None, 0
            elif h.level == "part":
                return "Part", RANK_PART, None, 0
            elif h.level == "chapter":
                return "Chapter", RANK_CHAPTER, None, 0
            elif h.level == "section":
                return "Section", RANK_SECTION, None, 0
            elif h.level == "subsection":
                return "SubSection", RANK_SUBSECTION, None, 0
            elif h.level == "clause_heading":
                return "Clause", RANK_CLAUSE_HEADING, None, 0

        # 2. Is it Numbered?
        if block_id in self.numbering:
            n = self.numbering[block_id]
            rank = RANK_CLAUSE_BASE + n.depth
            # Special top-level items
            if n.scheme in ("appendix", "annexure", "schedule"):
                if n.scheme == "appendix":
                    return "Appendix", RANK_CHAPTER, n.raw_text, 1
                elif n.scheme == "annexure":
                    return "Annexure", RANK_CHAPTER, n.raw_text, 1
                else:
                    return "Clause", RANK_CHAPTER, n.raw_text, 1 # Schedule as Chapter equivalent
            return "Clause", rank, n.raw_text, n.depth

        # 3. Fallback to Layout Region Type
        if region_type == "note":
            return "Note", RANK_LEAF, None, 0
        elif region_type == "bullet_list":
            return "Bullet", RANK_LEAF, None, 0
        elif region_type == "table":
            return "Table", RANK_LEAF, None, 0
            
        return "Paragraph", RANK_LEAF, None, 0

    def build(self) -> ASTDocument:
        logger.info(f"Building AST for {self.layout.document_path}")

        # Initialize the absolute root
        root = ASTNode(
            node_id="root",
            node_type="Document",
            text="Root",
            page=0
        )
        
        # Stack stores tuples of (node, rank)
        stack: List[tuple[ASTNode, int]] = [(root, RANK_ROOT)]

        for block in self.layout.blocks:
            # Skip pure headers, footers, page numbers in the AST
            if block.region_type in ("header", "footer", "page_number"):
                continue

            node_type, rank, num_str, depth = self._determine_node_props(
                block.block_id, block.text, block.region_type
            )

            # Pop the stack until we find a parent that strictly outranks us
            # (i.e. parent_rank < my_rank)
            while len(stack) > 1 and stack[-1][1] >= rank:
                stack.pop()

            parent_node = stack[-1][0]

            new_node = ASTNode(
                node_id=block.block_id,
                node_type=node_type,
                text=block.text,
                page=block.page,
                bbox=block.bbox,
                numbering=num_str,
                depth=depth
            )

            parent_node.children.append(new_node)
            stack.append((new_node, rank))

        doc = ASTDocument(
            document_path=self.layout.document_path,
            root=root
        )

        logger.info("AST build complete")
        return doc

    def build_to_file(self, output_path: Optional[Path] = None) -> Path:
        ast_doc = self.build()

        if output_path is None:
            base = Path(__file__).resolve().parent.parent.parent / "data" / "pipeline_output"
            stem = Path(self.layout.document_path).stem
            output_path = base / stem / "ast.json"

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            ast_doc.model_dump_json(indent=2, by_alias=True), encoding="utf-8"
        )
        logger.info(f"ast.json written to: {output_path}")
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

    layout_path = target_dir / "layout.json"
    headings_path = target_dir / "headings.json"
    numbering_path = target_dir / "numbering.json"

    if not all(p.exists() for p in [layout_path, headings_path, numbering_path]):
        print(f"Missing input JSONs in {target_dir}")
        sys.exit(1)

    layout_coll = LayoutCollection.model_validate_json(layout_path.read_text(encoding="utf-8"))
    headings_coll = HeadingCollection.model_validate_json(headings_path.read_text(encoding="utf-8"))
    num_coll = NumberingCollection.model_validate_json(numbering_path.read_text(encoding="utf-8"))

    builder = ASTBuilder(layout_coll, headings_coll, num_coll)
    out = builder.build_to_file()
    ast_doc = builder.build()

    # Recursive print helper
    def print_tree(node: ASTNode, indent: int = 0):
        prefix = "  " * indent
        num = f"[{node.numbering}] " if node.numbering else ""
        text = node.text.replace('\n', ' ')
        text = text[:40] + "..." if len(text) > 40 else text
        # Encode to ascii to prevent Windows console cp1252 print crashes
        safe_text = text.encode("ascii", "ignore").decode("ascii")
        print(f"{prefix}- {node.node_type}: {num}{safe_text}")
        for child in node.children:
            print_tree(child, indent + 1)

    print(f"\n[OK] AST Built Successfully")
    print(f"[OK] Output: {out}\n")
    print("-- AST Preview ----------------------------------------------------")
    print_tree(ast_doc.root)
