"""RAG / vector-search abstraction — TRD §5.4, reproduced close to verbatim.

Every agent calls this Protocol, never `regulatory_chunks`/`org_sop_chunks`
directly (TRD §5.4) — the seam that lets pgvector be swapped for a dedicated
vector store later without touching agent code.

Extension beyond the TRD's literal signature: `search_organizational` gains
an optional `department_ids` filter, keyword-only and defaulting to `None`
(fully backward compatible). The companion doc
(sera_three_agents_workflow_and_plan.md §2.2) requires sop_generation_agent
to scope its RAG search to the departments impact_mapping_agent identified —
the TRD predates that 3-way split and didn't anticipate the filter.
`InMemoryRetrievalProvider` honors it by pre-filtering chunks whose parent
SOP belongs to one of the given departments before scoring.
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from pydantic import BaseModel

from app.adapters.memory.store import InMemoryOrgStore


class RegulatoryFilters(BaseModel):
    category: str | None = None
    effective_after: str | None = None  # ISO date


class RetrievedChunk(BaseModel):
    chunk_id: UUID
    source_id: UUID  # document_id or sop_id
    text: str
    score: float


class RetrievalProvider(Protocol):
    async def search_regulatory(
        self, query: str, filters: RegulatoryFilters, top_k: int = 8
    ) -> list[RetrievedChunk]: ...

    async def search_organizational(
        self,
        query: str,
        organization_id: UUID,
        top_k: int = 8,
        *,
        department_ids: list[UUID] | None = None,
    ) -> list[RetrievedChunk]: ...


def _keyword_overlap_score(query: str, text: str) -> float:
    query_terms = {t.lower() for t in query.split() if t}
    text_terms = {t.lower() for t in text.split() if t}
    if not query_terms or not text_terms:
        return 0.0
    return len(query_terms & text_terms) / len(query_terms)


class InMemoryRetrievalProvider:
    """Naive keyword-overlap fake — stands in for pgvector's HNSW cosine
    search (TRD §5.3) until a teammate wires up real embeddings.
    """

    def __init__(self, store: InMemoryOrgStore) -> None:
        self._store = store

    async def search_regulatory(
        self, query: str, filters: RegulatoryFilters, top_k: int = 8
    ) -> list[RetrievedChunk]:
        # No regulatory_chunks seeded in this slice (owned by the
        # applicability/obligation_extraction agents' teammates) — always empty.
        return []

    async def search_organizational(
        self,
        query: str,
        organization_id: UUID,
        top_k: int = 8,
        *,
        department_ids: list[UUID] | None = None,
    ) -> list[RetrievedChunk]:
        sop_by_id = {sop.id: sop for sop in self._store.tables.sops}
        candidates = [
            chunk
            for chunk in self._store.tables.sop_chunks
            if chunk.organization_id == organization_id
        ]
        if department_ids is not None:
            wanted = set(department_ids)
            candidates = [
                chunk
                for chunk in candidates
                if sop_by_id.get(chunk.sop_id) is not None
                and sop_by_id[chunk.sop_id].department_id in wanted
            ]
        scored = [
            RetrievedChunk(
                chunk_id=chunk.id,
                source_id=chunk.sop_id,
                text=chunk.chunk_text,
                score=_keyword_overlap_score(query, chunk.chunk_text),
            )
            for chunk in candidates
        ]
        scored.sort(key=lambda c: c.score, reverse=True)
        return scored[:top_k]
