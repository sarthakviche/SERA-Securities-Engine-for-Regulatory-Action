from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.adapters.memory.store import Department, OrgSOP, OrgSystem

class OrganizationalRepository(Protocol):
    async def get_departments(self) -> list[Department]: ...

    async def get_systems(self) -> list[OrgSystem]: ...

    async def get_sop_by_id(self, sop_id: UUID) -> OrgSOP | None: ...

    async def list_sops_for_departments(self, department_ids: list[UUID]) -> list[OrgSOP]: ...
