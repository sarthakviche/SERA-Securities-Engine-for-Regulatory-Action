from __future__ import annotations

from uuid import UUID

from app.adapters.memory.store import AuditLogRow, InMemoryOrgStore

class InMemoryAuditRepository:
    def __init__(self, store: InMemoryOrgStore) -> None:
        self._store = store

    async def list_for_workflow(self, workflow_id: UUID) -> list[AuditLogRow]:
        return [row for row in self._store.tables.audit_log if row.workflow_id == workflow_id]
