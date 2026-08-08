"""Structured (non-vector) organizational reads — TRD §3 names
`knowledge/organizational/`; the scaffold only created the parent
`knowledge/` package with an (empty) `retrieval_provider.py`.

Deliberately separate from `retrieval_provider.py`: that file is the RAG /
vector-search Protocol (TRD §5.4). This one is for the "direct read, not
RAG" case the companion doc calls out — `org_departments`/`org_systems` are
small tables, fetched as full rows, not embedded/searched. `list_sops_for_departments`
and `get_sop_by_id` are the read-only lookups sop_generation_agent uses for
its amendment-vs-new match; it must never call a write method here (see
sop_generation_agent.py) — SOP finalization only happens inside
execution_handoff's transaction (adapters/memory/store.py).
"""

from app.modules.knowledge.organizational.repository_protocol import OrganizationalRepository
from app.modules.knowledge.organizational.repository_memory import InMemoryOrganizationalRepository

__all__ = [
    "OrganizationalRepository",
    "InMemoryOrganizationalRepository",
]
