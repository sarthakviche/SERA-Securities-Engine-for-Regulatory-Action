"""
NotificationAwareEventPublisher

Wraps InMemoryEventPublisher (for log/test visibility) and additionally:

1. Maps the DomainEvent type to a human-readable title/body (no LLM).
2. Writes an in-app notification row to Postgres (idempotent).
3. Reads user preferences; if email_enabled, sends via Resend.
4. Pushes the new notification JSON into the SSE broadcast queue so
   connected clients receive it without a page refresh.

Failure rules (spec §7):
- Email failures are caught and logged; in-app notification is unaffected.
- Notification creation failure is caught and logged; the underlying
  compliance operation (task creation, evidence processing, etc.) must
  never fail because a notification could not be written.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import DomainEvent, InMemoryEventPublisher
from app.core.config import settings

logger = logging.getLogger("sera.notifications.publisher")

# ── Default MVP user ────────────────────────────────────────────────────────
# The system is currently single-tenant.  All notifications are addressed to
# this constant user ID until a proper users table exists.
DEFAULT_USER_ID = UUID("00000000-0000-0000-0000-000000000001")

# ── SSE broadcast registry ──────────────────────────────────────────────────
# Maps user_id → set of asyncio.Queue instances (one per open browser tab).
# This lives in process memory; restarting the server clears it (acceptable
# for MVP — clients reconnect and re-fetch via REST on reconnect).
SSE_CONNECTIONS: dict[UUID, set[asyncio.Queue]] = {}


def register_sse_queue(user_id: UUID, queue: asyncio.Queue) -> None:
    SSE_CONNECTIONS.setdefault(user_id, set()).add(queue)


def deregister_sse_queue(user_id: UUID, queue: asyncio.Queue) -> None:
    if user_id in SSE_CONNECTIONS:
        SSE_CONNECTIONS[user_id].discard(queue)


def broadcast_to_user(user_id: UUID, payload: dict[str, Any]) -> None:
    """Push a notification payload to all SSE queues for a user."""
    for q in SSE_CONNECTIONS.get(user_id, set()):
        try:
            q.put_nowait(payload)
        except asyncio.QueueFull:
            logger.warning("SSE queue full for user=%s, dropping notification", user_id)


# ── Event-to-notification mapping ───────────────────────────────────────────
# Deterministic — no LLM involved.

def _build_notification_content(
    event: DomainEvent,
) -> Optional[tuple[str, str, str | None, str | None]]:
    """
    Returns (title, body, resource_type, resource_id_str) or None if the
    event type should not generate a notification.
    """
    p = event.payload
    wid = str(event.workflow_id) if event.workflow_id else None

    mapping: dict[str, tuple[str, str, str | None]] = {
        "task.created": (
            "Task Assigned",
            f"{p.get('task_title', 'A task')} assigned to {p.get('owner', 'team')}",
            "task",
        ),
        "task.overdue": (
            "Task Overdue",
            f"{p.get('task_title', 'A task')} was due {p.get('due_date', 'recently')}",
            "task",
        ),
        "task.completed": (
            "Task Completed",
            f"{p.get('task_title', 'A task')} has been marked complete",
            "task",
        ),
        "evidence.submitted": (
            "Evidence Submitted",
            f"Evidence uploaded for {p.get('task_title', 'a task')}",
            "task",
        ),
        "evidence.rejected": (
            "Evidence Rejected",
            f"Evidence for {p.get('task_title', 'a task')} was rejected. "
            f"{p.get('reason', '')}",
            "task",
        ),
        "evidence.accepted": (
            "Evidence Accepted",
            f"Evidence for {p.get('task_title', 'a task')} has been approved",
            "task",
        ),
        "compliance.gap_detected": (
            "Compliance Gap Detected",
            f"Gap identified: {p.get('description', 'review required')}",
            "obligation",
        ),
        "compliance.verified": (
            "Compliance Verified",
            f"{p.get('obligation_title', 'An obligation')} is now marked compliant",
            "obligation",
        ),
        "escalation.triggered": (
            "Escalation Triggered",
            f"{p.get('task_title', 'A task')} has been escalated to management",
            "task",
        ),
        "gate_2.rejected": (
            "Approval Required",
            "The implementation plan was rejected and requires revision. "
            f"{p.get('comment', '')}",
            "workflow",
        ),
        "workflow.stage_completed": (
            "Implementation Tasks Created",
            f"Tasks are ready for execution (agent: {p.get('agent_name', '')})",
            "workflow",
        ),
    }

    if event.event_type not in mapping:
        return None

    title, body, resource_type = mapping[event.event_type]
    resource_id = p.get("task_id") or p.get("obligation_id") or wid
    return title, body, resource_type, resource_id


class NotificationAwareEventPublisher:
    """
    Production EventPublisher that persists notifications and sends emails.

    Requires a live AsyncSession so it can write to Postgres.
    The session is obtained fresh from AsyncSessionLocal for each publish()
    call so that a notification failure cannot roll back an unrelated
    compliance transaction.
    """

    def __init__(self, db_session: Optional[AsyncSession] = None) -> None:
        self._inner = InMemoryEventPublisher()
        self._db_session = db_session  # may be None; then we open our own

    async def publish(self, event: DomainEvent) -> None:
        # Always delegate to inner publisher (logging + test compatibility)
        await self._inner.publish(event)

        content = _build_notification_content(event)
        if content is None:
            return

        title, body, resource_type, resource_id_str = content

        # Resolve resource_id to UUID if possible
        resource_id: Optional[UUID] = None
        if resource_id_str:
            try:
                resource_id = UUID(str(resource_id_str))
            except (ValueError, AttributeError):
                pass

        # Build frontend URL for the CTA button in the email
        resource_url = _build_resource_url(resource_type, resource_id, event.workflow_id)

        user_id = DEFAULT_USER_ID

        await self._persist_and_notify(
            event=event,
            user_id=user_id,
            title=title,
            body=body,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_url=resource_url,
        )

    async def _persist_and_notify(
        self,
        *,
        event: DomainEvent,
        user_id: UUID,
        title: str,
        body: str,
        resource_type: Optional[str],
        resource_id: Optional[UUID],
        resource_url: Optional[str],
    ) -> None:
        from app.core.db import AsyncSessionLocal
        from app.modules.notifications.repository_sql import notification_repository
        from app.modules.notifications.email_service import email_service

        try:
            async with AsyncSessionLocal() as db:
                # 1. Write in-app notification (idempotent)
                notification = await notification_repository.create_notification(
                    db,
                    user_id=user_id,
                    event_type=event.event_type,
                    title=title,
                    body=body,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    idempotency_key=event.idempotency_key,
                )
                await db.commit()

                # 2. Push to SSE broadcast queue (real-time)
                if notification:
                    payload = {
                        "id": str(notification.id),
                        "event_type": notification.event_type,
                        "title": notification.title,
                        "body": notification.body,
                        "resource_type": notification.resource_type,
                        "resource_id": str(notification.resource_id) if notification.resource_id else None,
                        "is_read": False,
                        "idempotency_key": notification.idempotency_key,
                        "created_at": notification.created_at.isoformat(),
                    }
                    broadcast_to_user(user_id, payload)

                # 3. Check email preference and send
                prefs = await notification_repository.get_preferences(db, user_id)
                email_enabled = (
                    prefs.email_enabled if prefs is not None else True
                )

        except Exception as exc:  # noqa: BLE001
            logger.error(
                "notification persistence failed (event=%s key=%s): %s — "
                "compliance operation continues",
                event.event_type,
                event.idempotency_key,
                exc,
            )
            return

        # 4. Send email outside the DB session (failure must not affect in-app)
        if email_enabled:
            email_service.send_notification_email(
                event_type=event.event_type,
                title=title,
                body=body,
                resource_url=resource_url,
            )


def _build_resource_url(
    resource_type: Optional[str],
    resource_id: Optional[UUID],
    workflow_id: Optional[UUID],
) -> Optional[str]:
    base = settings.FRONTEND_URL.rstrip("/")
    if resource_type == "task":
        # Deep-link to the implementation tracker
        return f"{base}/implementation-tracker"
    if resource_type == "workflow" and workflow_id:
        return f"{base}/workspace"
    if resource_type == "obligation":
        return f"{base}/obligations"
    return f"{base}/"
