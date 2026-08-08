from __future__ import annotations

from uuid import UUID

from app.adapters.memory.store import InMemoryOrgStore, ObligationRow

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
