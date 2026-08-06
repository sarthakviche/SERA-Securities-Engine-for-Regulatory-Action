"""Obligation Repository — TRD §3 names this module (`modules/obligations/`)
but the scaffold hadn't created it yet; added here because
`impact_mapping_agent` needs a real UPDATE of `obligations.owner_department_id`
and `execution_handoff` needs to flip obligation status on gate_2 approval.

Only the repository layer is added in this slice (no router.py/service.py —
nothing calls obligations over HTTP yet). `InMemoryObligationRepository` is
the prototype fake; a teammate's Postgres implementation satisfies the same
`ObligationRepository` Protocol structurally, no inheritance required.
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.adapters.memory.store import InMemoryOrgStore, ObligationRow


class ObligationRepository(Protocol):
    async def list(self, obligation_ids: list[UUID] | None = None) -> list[ObligationRow]: ...

    async def update_owner_department(self, obligation_id: UUID, department_id: UUID) -> None: ...


class InMemoryObligationRepository:
    def __init__(self, store: InMemoryOrgStore) -> None:
        self._store = store

    async def list(self, obligation_ids: list[UUID] | None = None) -> list[ObligationRow]:
        rows = self._store.tables.obligations
        if obligation_ids is None:
            return list(rows)
        wanted = set(obligation_ids)
        return [row for row in rows if row.id in wanted]

    async def update_owner_department(self, obligation_id: UUID, department_id: UUID) -> None:
        for row in self._store.tables.obligations:
            if row.id == obligation_id:
                row.owner_department_id = department_id
                return
        raise KeyError(f"obligation {obligation_id} not found")
