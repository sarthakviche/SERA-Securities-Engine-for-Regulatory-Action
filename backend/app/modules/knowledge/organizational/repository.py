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

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.adapters.memory.store import Department, InMemoryOrgStore, OrgSOP, OrgSystem


class OrganizationalRepository(Protocol):
    async def get_departments(self) -> list[Department]: ...

    async def get_systems(self) -> list[OrgSystem]: ...

    async def get_sop_by_id(self, sop_id: UUID) -> OrgSOP | None: ...

    async def list_sops_for_departments(self, department_ids: list[UUID]) -> list[OrgSOP]: ...


class InMemoryOrganizationalRepository:
    def __init__(self, store: InMemoryOrgStore) -> None:
        self._store = store

    async def get_departments(self) -> list[Department]:
        return list(self._store.tables.departments)

    async def get_systems(self) -> list[OrgSystem]:
        return list(self._store.tables.systems)

    async def get_sop_by_id(self, sop_id: UUID) -> OrgSOP | None:
        for row in self._store.tables.sops:
            if row.id == sop_id:
                return row
        return None

    async def list_sops_for_departments(self, department_ids: list[UUID]) -> list[OrgSOP]:
        wanted = set(department_ids)
        return [row for row in self._store.tables.sops if row.department_id in wanted]
