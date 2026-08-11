from __future__ import annotations

from uuid import UUID

from app.adapters.memory.store import Department, InMemoryOrgStore, OrgSOP, OrgSystem

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
