"""Task Repository — TRD §3 names `modules/tasks/`; added here (repository
layer only) because `execution_handoff` needs to read back what it wrote for
tests/demo purposes. The actual bulk-insert happens transactionally via
`InMemoryExecutionTransaction.bulk_insert_tasks` (adapters/memory/store.py),
not through this repository — this is a read-only view for convenience.
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.adapters.memory.store import InMemoryOrgStore, TaskRow


class TaskRepository(Protocol):
    async def list_for_workflow(self, workflow_id: UUID) -> list[TaskRow]: ...


class InMemoryTaskRepository:
    def __init__(self, store: InMemoryOrgStore) -> None:
        self._store = store

    async def list_for_workflow(self, workflow_id: UUID) -> list[TaskRow]:
        return [row for row in self._store.tables.tasks if row.workflow_id == workflow_id]
