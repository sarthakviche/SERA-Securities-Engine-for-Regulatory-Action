"""Audit Repository — TRD §3 names `modules/audit/`; added here (repository
layer only), read-only for now. The actual append happens transactionally
via `InMemoryExecutionTransaction.insert_audit_log` (adapters/memory/store.py)
during `execution_handoff`.

Note for the real implementation: TRD §4.2 revokes UPDATE/DELETE on
`audit_log` for the app DB role — append-only, no exceptions.
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.adapters.memory.store import AuditLogRow, InMemoryOrgStore


class AuditRepository(Protocol):
    async def list_for_workflow(self, workflow_id: UUID) -> list[AuditLogRow]: ...


class InMemoryAuditRepository:
    def __init__(self, store: InMemoryOrgStore) -> None:
        self._store = store

    async def list_for_workflow(self, workflow_id: UUID) -> list[AuditLogRow]:
        return [row for row in self._store.tables.audit_log if row.workflow_id == workflow_id]
