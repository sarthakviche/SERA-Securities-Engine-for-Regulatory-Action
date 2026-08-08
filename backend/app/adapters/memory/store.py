"""In-memory backing store shared by the obligations/tasks/audit/organizational
repository fakes, plus the workflow-document store.

This file is NOT part of the TRD's own module tree (§3) — it's prototype-only
plumbing that lets `modules/obligations`, `modules/tasks`, `modules/audit` and
`modules/knowledge/organizational` each expose their real, TRD-shaped
Protocols today without a Postgres instance. A teammate replacing any one of
those modules with a real Postgres-backed repository does not need this file
at all; it only exists behind the fakes.

Rows are kept as plain dataclasses (not the Pydantic API schemas) since this
is meant to model relational tables, not request/response payloads.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4


@dataclass
class Department:
    id: UUID
    organization_id: UUID
    name: str
    head_user_id: UUID | None = None


@dataclass
class OrgSystem:
    id: UUID
    organization_id: UUID
    name: str
    owner_department_id: UUID | None = None


@dataclass
class OrgSOP:
    id: UUID
    organization_id: UUID
    department_id: UUID | None
    title: str
    content: str
    version: int = 1


@dataclass
class OrgSOPChunk:
    id: UUID
    sop_id: UUID
    organization_id: UUID
    chunk_text: str


@dataclass
class ObligationRow:
    id: UUID
    workflow_id: UUID
    organization_id: UUID
    description: str
    owner_department_id: UUID | None = None
    frequency: str | None = None
    evidence_type: str | None = None
    status: str = "proposed"  # proposed|approved|rejected|compliant|non_compliant
    confidence_score: float | None = None


@dataclass
class TaskRow:
    id: UUID
    workflow_id: UUID
    obligation_id: UUID
    organization_id: UUID
    title: str
    description: str | None
    owner_department_id: UUID | None
    assignee_user_id: UUID | None
    due_date: str | None  # ISO date string; due_date_rule is resolved before insert
    status: str = "open"
    evidence_requirement: str | None = None
    priority: str = "medium"
    recurrence_rule: str | None = None


@dataclass
class AuditLogRow:
    id: int
    organization_id: UUID
    workflow_id: UUID | None
    actor_type: str
    actor_id: str
    action: str
    entity_type: str
    entity_id: str
    before: dict[str, Any] | None
    after: dict[str, Any] | None
    created_at: datetime


@dataclass
class Tables:
    departments: list[Department] = field(default_factory=list)
    systems: list[OrgSystem] = field(default_factory=list)
    sops: list[OrgSOP] = field(default_factory=list)
    sop_chunks: list[OrgSOPChunk] = field(default_factory=list)
    obligations: list[ObligationRow] = field(default_factory=list)
    tasks: list[TaskRow] = field(default_factory=list)
    audit_log: list[AuditLogRow] = field(default_factory=list)


class InMemoryOrgStore:
    """Holds the "live" tables. Reads/immediate writes (e.g. impact_mapping's
    obligations.owner_department_id UPDATE) go straight through here. Only
    execution_handoff mutates via a transaction snapshot (see `begin()`).
    """

    def __init__(self, tables: Tables | None = None) -> None:
        self.tables = tables if tables is not None else Tables()

    def begin(self) -> "InMemoryExecutionTransaction":
        return InMemoryExecutionTransaction(self)


class InMemoryExecutionTransaction:
    """Copy-on-write simulated transaction: commit() swaps the scratch copy
    in atomically, any exception (or explicit rollback()) discards it,
    leaving `store.tables` completely untouched.

    This is a SIMULATION good enough to exercise execution_handoff's
    rollback-on-exception control flow. The real Postgres adapter MUST wrap
    this in an actual DB transaction (e.g. `async with session.begin():`) —
    execution_handoff's fail-closed guarantee depends on that, not on this
    in-memory copy trick.
    """

    def __init__(self, store: InMemoryOrgStore) -> None:
        self._store = store
        self._scratch: Tables | None = None

    async def __aenter__(self) -> "InMemoryExecutionTransaction":
        self._scratch = copy.deepcopy(self._store.tables)
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        if exc_type is None:
            self._store.tables = self._scratch
        self._scratch = None
        return False  # never suppress exceptions

    def _tables(self) -> Tables:
        assert self._scratch is not None, "transaction methods must be called inside 'async with'"
        return self._scratch

    async def update_obligation_status(self, obligation_id: UUID, status: str) -> None:
        for row in self._tables().obligations:
            if row.id == obligation_id:
                row.status = status
                return
        raise KeyError(f"obligation {obligation_id} not found")

    async def insert_or_amend_sop(
        self,
        *,
        organization_id: UUID,
        based_on_existing_sop_id: UUID | None,
        department_id: UUID | None,
        title: str,
        content: str,
    ) -> UUID:
        tables = self._tables()
        if based_on_existing_sop_id is not None:
            for row in tables.sops:
                if row.id == based_on_existing_sop_id:
                    row.content = content
                    row.title = title
                    row.version += 1
                    return row.id
            raise KeyError(f"sop {based_on_existing_sop_id} not found for amendment")
        new_id = uuid4()
        tables.sops.append(
            OrgSOP(
                id=new_id,
                organization_id=organization_id,
                department_id=department_id,
                title=title,
                content=content,
                version=1,
            )
        )
        return new_id

    async def bulk_insert_tasks(self, tasks: list[TaskRow]) -> None:
        self._tables().tasks.extend(tasks)

    async def insert_audit_log(
        self,
        *,
        organization_id: UUID,
        workflow_id: UUID | None,
        actor_type: str,
        actor_id: str,
        action: str,
        entity_type: str,
        entity_id: str,
        before: dict[str, Any] | None = None,
        after: dict[str, Any] | None = None,
    ) -> None:
        tables = self._tables()
        tables.audit_log.append(
            AuditLogRow(
                id=len(tables.audit_log) + 1,
                organization_id=organization_id,
                workflow_id=workflow_id,
                actor_type=actor_type,
                actor_id=actor_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                before=before,
                after=after,
                created_at=datetime.now(timezone.utc),
            )
        )
