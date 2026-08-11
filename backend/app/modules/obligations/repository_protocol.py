from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.adapters.memory.store import ObligationRow

class ObligationRepository(Protocol):
    async def list(self, obligation_ids: list[UUID] | None = None) -> list[ObligationRow]: ...

    async def update_owner_department(self, obligation_id: UUID, department_id: UUID) -> None: ...
