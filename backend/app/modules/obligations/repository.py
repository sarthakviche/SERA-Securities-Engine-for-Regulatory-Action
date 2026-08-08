"""Obligation Repository — merged file for both HEAD and their branches."""

from __future__ import annotations

import uuid
from typing import List, Dict, Any, Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.obligation import Obligation

from app.adapters.memory.store import InMemoryOrgStore, ObligationRow

class SQLAlchemyObligationRepository:
    
    async def get_by_workflow(self, db: AsyncSession, workflow_id: uuid.UUID) -> List[Obligation]:
        stmt = select(Obligation).where(Obligation.workflow_id == workflow_id)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def upsert_obligations(
        self, 
        db: AsyncSession, 
        workflow_id: uuid.UUID, 
        obligations_data: List[Dict[str, Any]]
    ) -> List[Obligation]:
        """
        Upserts obligations for a workflow. For simplicity in the prototype,
        we rely on the workflow_id to prevent duplicate creation if the pipeline
        is run multiple times, by clearing existing obligations for this workflow
        and recreating them.
        """
        # Fetch existing obligations for this workflow
        existing_stmt = select(Obligation).where(Obligation.workflow_id == workflow_id)
        result = await db.execute(existing_stmt)
        existing_obligations = list(result.scalars().all())
        
        # Delete existing ones to ensure idempotency for the prototype
        for obs in existing_obligations:
            await db.delete(obs)
            
        await db.flush()

        new_obligations = []
        for obs_data in obligations_data:
            # Only map fields that actually exist in the mock outputs
            title = obs_data.get("title", "")
            category = obs_data.get("category")
            
            # Ensure title is present as it's not nullable in the model
            if not title:
                continue
                
            obl_id_str = obs_data.get("id")
            obl_id = uuid.UUID(obl_id_str) if obl_id_str else uuid.uuid4()
                
            obligation = Obligation(
                id=obl_id,
                workflow_id=workflow_id,
                title=title,
                category=category,
                status="pending"
            )
            db.add(obligation)
            new_obligations.append(obligation)
            
        await db.flush()
        return new_obligations

obligation_repository = SQLAlchemyObligationRepository()


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
