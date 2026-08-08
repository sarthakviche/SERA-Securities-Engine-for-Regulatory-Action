from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.adapters.memory.store import TaskRow

class TaskRepository(Protocol):
    async def list_for_workflow(self, workflow_id: UUID) -> list[TaskRow]: ...
