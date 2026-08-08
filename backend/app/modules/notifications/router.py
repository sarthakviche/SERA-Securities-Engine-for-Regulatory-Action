"""
Notifications FastAPI Router

REST endpoints:
  GET  /api/v1/notifications                  List notifications
  POST /api/v1/notifications/{id}/read        Mark one read
  POST /api/v1/notifications/read-all         Mark all read
  GET  /api/v1/notifications/unread-count     Unread count
  GET  /api/v1/notifications/preferences      Get preferences
  PUT  /api/v1/notifications/preferences      Update preferences

SSE endpoint:
  GET  /api/v1/notifications/stream           Server-Sent Events stream
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import AsyncGenerator
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.core.db import AsyncSessionLocal
from app.core.notification_event_publisher import (
    DEFAULT_USER_ID,
    SSE_CONNECTIONS,
    deregister_sse_queue,
    register_sse_queue,
)
from app.modules.notifications.schemas import (
    NotificationListResponse,
    NotificationOut,
    PreferencesOut,
    PreferencesUpdate,
)
from app.modules.notifications.service import notification_service

logger = logging.getLogger("sera.notifications.router")

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


# ── Dependency ───────────────────────────────────────────────────────────────

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


def _current_user_id() -> UUID:
    """
    Returns the current user's UUID.
    Single-tenant MVP — always the default org user.
    """
    return DEFAULT_USER_ID


# ── REST endpoints ────────────────────────────────────────────────────────────

@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    unread_only: bool = False,
    limit: int = 50,
    db=Depends(get_db),
):
    user_id = _current_user_id()
    notifications = await notification_service.list_for_user(
        db, user_id, limit=limit, unread_only=unread_only
    )
    unread_count = await notification_service.get_unread_count(db, user_id)
    return NotificationListResponse(
        notifications=[NotificationOut.model_validate(n) for n in notifications],
        unread_count=unread_count,
    )


@router.get("/unread-count")
async def get_unread_count(db=Depends(get_db)):
    user_id = _current_user_id()
    count = await notification_service.get_unread_count(db, user_id)
    return {"unread_count": count}


@router.post("/read-all")
async def mark_all_read(db=Depends(get_db)):
    user_id = _current_user_id()
    count = await notification_service.mark_all_read(db, user_id)
    await db.commit()
    return {"marked_read": count}


@router.post("/{notification_id}/read")
async def mark_notification_read(notification_id: UUID, db=Depends(get_db)):
    user_id = _current_user_id()
    updated = await notification_service.mark_read(db, notification_id, user_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Notification not found")
    await db.commit()
    return {"ok": True}


@router.get("/preferences", response_model=PreferencesOut)
async def get_preferences(db=Depends(get_db)):
    user_id = _current_user_id()
    prefs = await notification_service.get_preferences(db, user_id)
    if prefs is None:
        # Return defaults if no row exists yet
        return PreferencesOut(
            user_id=user_id,
            in_app_enabled=True,
            email_enabled=True,
        )
    return PreferencesOut.model_validate(prefs)


@router.put("/preferences", response_model=PreferencesOut)
async def update_preferences(body: PreferencesUpdate, db=Depends(get_db)):
    user_id = _current_user_id()
    prefs = await notification_service.upsert_preferences(
        db,
        user_id,
        in_app_enabled=body.in_app_enabled,
        email_enabled=body.email_enabled,
    )
    await db.commit()
    return PreferencesOut.model_validate(prefs)


# ── SSE stream ────────────────────────────────────────────────────────────────

@router.get("/stream")
async def notification_stream():
    """
    Server-Sent Events endpoint.

    The client opens one long-lived GET connection here.  Whenever a new
    notification is published the server pushes a JSON event without the
    client needing to poll.

    Protocol:
      data: <json>\\n\\n    — new notification payload
      : keep-alive\\n\\n   — heartbeat every 25 seconds (prevents proxies
                             from closing idle connections)
    """
    user_id = _current_user_id()
    queue: asyncio.Queue = asyncio.Queue(maxsize=100)
    register_sse_queue(user_id, queue)

    async def event_generator() -> AsyncGenerator[str, None]:
        # Send an initial "connected" ping so the client knows the stream is up
        yield ": connected\n\n"
        try:
            while True:
                try:
                    # Wait up to 25 s for a notification; send keepalive if none
                    payload = await asyncio.wait_for(queue.get(), timeout=25.0)
                    data = json.dumps(payload)
                    yield f"event: notification\ndata: {data}\n\n"
                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"
        except asyncio.CancelledError:
            # Client disconnected
            pass
        finally:
            deregister_sse_queue(user_id, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # disable nginx buffering
        },
    )
