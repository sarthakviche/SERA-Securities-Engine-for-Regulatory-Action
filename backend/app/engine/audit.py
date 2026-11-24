"""Append-only, SHA-256 hash-chained audit log.

hash_n = sha256(prev_hash || canonical_json(event_n)). Editing or deleting any
row breaks every later hash, which /api/v2/audit/verify detects.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_event import AuditEvent

GENESIS = "0" * 64


def _canonical(ev: dict[str, Any]) -> str:
    return json.dumps(ev, sort_keys=True, separators=(",", ":"), default=str)


def compute_hash(prev_hash: str, *, workflow_id, kind, title, detail, actor, payload, created_at) -> str:
    body = {
        "workflow_id": str(workflow_id) if workflow_id else None,
        "kind": kind,
        "title": title,
        "detail": detail,
        "actor": actor,
        "payload": payload,
        "created_at": created_at.astimezone(timezone.utc).isoformat(),
    }
    return hashlib.sha256((prev_hash + _canonical(body)).encode("utf-8")).hexdigest()


async def record(
    db: AsyncSession,
    *,
    kind: str,
    title: str,
    actor: str = "SERA Engine",
    detail: str | None = None,
    workflow_id: UUID | None = None,
    payload: dict[str, Any] | None = None,
) -> AuditEvent:
    # serialize writers on the chain head
    last = (await db.execute(select(AuditEvent).order_by(AuditEvent.id.desc()).limit(1).with_for_update())).scalar_one_or_none()
    prev = last.hash if last else GENESIS
    now = datetime.now(timezone.utc).replace(microsecond=0)
    payload = json.loads(_canonical(payload)) if payload else None
    h = compute_hash(prev, workflow_id=workflow_id, kind=kind, title=title, detail=detail, actor=actor,
                     payload=payload, created_at=now)
    ev = AuditEvent(workflow_id=workflow_id, kind=kind, title=title, detail=detail, actor=actor, payload=payload,
                    prev_hash=prev, hash=h, created_at=now)
    db.add(ev)
    await db.flush()
    return ev


async def verify(db: AsyncSession) -> dict[str, Any]:
    rows = (await db.execute(select(AuditEvent).order_by(AuditEvent.id))).scalars().all()
    prev = GENESIS
    for r in rows:
        expected = compute_hash(prev, workflow_id=r.workflow_id, kind=r.kind, title=r.title, detail=r.detail,
                                actor=r.actor, payload=r.payload, created_at=r.created_at)
        if r.prev_hash != prev or r.hash != expected:
            return {"valid": False, "checked": len(rows), "broken_at": r.id, "title": r.title}
        prev = r.hash
    return {"valid": True, "checked": len(rows), "head": prev}
