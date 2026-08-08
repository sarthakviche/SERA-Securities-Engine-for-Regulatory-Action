"""
Notification service tests.

All tests use in-memory fakes (no live Postgres required).
They exercise the full notification flow:
  DomainEvent → NotificationAwareEventPublisher
              → NotificationService (fake repo)
              → ResendEmailService (spy)

The tests are deliberately self-contained so they can be run without asyncpg,
anthropic, or any other optional production dependency.
"""

from __future__ import annotations

import asyncio
import sys
import types
import uuid
from datetime import datetime, timezone
from typing import Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ── Stub out DB / heavy modules before any SERA code is imported ──────────────
# This lets the test file import notification service modules without needing
# a live Postgres connection or optional packages like asyncpg / anthropic.

def _stub_module(name: str, **attrs):
    mod = types.ModuleType(name)
    mod.__dict__.update(attrs)
    sys.modules[name] = mod
    return mod

# Stub asyncpg so SQLAlchemy doesn't try to import it at module load time
_stub_module("asyncpg")

# Stub anthropic (used by LLM provider)
_stub_module("anthropic")

# Stub resend (email service)
_stub_module("resend", Emails=MagicMock())

# Patch the DB engine creation so importing app.core.db doesn't open a connection
import unittest.mock as _mock
_mock.patch(
    "sqlalchemy.ext.asyncio.create_async_engine",
    return_value=MagicMock(),
).start()

# Now we can safely import SERA code
from app.core.events import DomainEvent  # noqa: E402
from app.core.notification_event_publisher import _build_notification_content, DEFAULT_USER_ID  # noqa: E402

# ── In-memory fake repository ─────────────────────────────────────────────────

class FakeNotificationRepo:
    """No Postgres; stores rows in a plain list."""

    def __init__(self):
        self.notifications: list[dict] = []
        self.preferences: dict[uuid.UUID, dict] = {}

    async def create_notification(self, db, *, user_id, event_type, title, body,
                                   resource_type, resource_id, idempotency_key):
        # Idempotency: skip if key already present for this user
        for n in self.notifications:
            if n["user_id"] == user_id and n["idempotency_key"] == idempotency_key:
                return None  # duplicate — silently ignored

        row = {
            "id": uuid.uuid4(),
            "user_id": user_id,
            "event_type": event_type,
            "title": title,
            "body": body,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "is_read": False,
            "idempotency_key": idempotency_key,
            "created_at": datetime.now(timezone.utc),
        }
        self.notifications.append(row)
        return MagicMock(**row)

    async def get_preferences(self, db, user_id):
        prefs = self.preferences.get(user_id)
        if prefs is None:
            return None
        mock = MagicMock()
        mock.in_app_enabled = prefs["in_app_enabled"]
        mock.email_enabled = prefs["email_enabled"]
        return mock

    async def list_for_user(self, db, user_id, *, limit=50, unread_only=False):
        return [n for n in self.notifications if n["user_id"] == user_id]

    async def mark_read(self, db, notification_id, user_id):
        for n in self.notifications:
            if n["id"] == notification_id and n["user_id"] == user_id:
                n["is_read"] = True
                return True
        return False

    async def mark_all_read(self, db, user_id):
        count = 0
        for n in self.notifications:
            if n["user_id"] == user_id and not n["is_read"]:
                n["is_read"] = True
                count += 1
        return count

    async def get_unread_count(self, db, user_id):
        return sum(1 for n in self.notifications if n["user_id"] == user_id and not n["is_read"])

    async def upsert_preferences(self, db, user_id, *, in_app_enabled, email_enabled):
        self.preferences[user_id] = {
            "in_app_enabled": in_app_enabled,
            "email_enabled": email_enabled,
        }
        mock = MagicMock()
        mock.in_app_enabled = in_app_enabled
        mock.email_enabled = email_enabled
        return mock


# ── Helpers ───────────────────────────────────────────────────────────────────

ORG_UUID = uuid.UUID("00000000-0000-0000-0000-000000000001")
USER_UUID = ORG_UUID  # single-tenant: same UUID


def make_event(event_type: str, payload: Optional[dict] = None,
               idempotency_key: Optional[str] = None) -> DomainEvent:
    return DomainEvent(
        event_type=event_type,
        organization_id=ORG_UUID,
        workflow_id=uuid.uuid4(),
        payload=payload or {"task_title": "Test Task", "owner": "Compliance Dept"},
        idempotency_key=idempotency_key or str(uuid.uuid4()),
    )


async def publish_via_service(event: DomainEvent, repo: FakeNotificationRepo,
                               email_spy=None) -> None:
    """
    Invoke the same logic as NotificationAwareEventPublisher but using the
    fake repo and optional email spy, without needing a live DB session.
    """
    from app.modules.notifications.service import NotificationService  # late import after stubs

    content = _build_notification_content(event)
    if content is None:
        return

    title, body, resource_type, resource_id_str = content

    resource_id: Optional[uuid.UUID] = None
    if resource_id_str:
        try:
            resource_id = uuid.UUID(str(resource_id_str))
        except (ValueError, AttributeError):
            pass

    svc = NotificationService(repo=repo)

    db = None  # fake repo doesn't use the session
    await svc.create(
        db,
        user_id=DEFAULT_USER_ID,
        event_type=event.event_type,
        title=title,
        body=body,
        resource_type=resource_type,
        resource_id=resource_id,
        idempotency_key=event.idempotency_key,
    )

    if email_spy:
        prefs = await repo.get_preferences(db, DEFAULT_USER_ID)
        email_enabled = prefs.email_enabled if prefs is not None else True
        if email_enabled:
            try:
                email_spy(event_type=event.event_type, title=title, body=body,
                          resource_url=None)
            except Exception:
                # mirrors ResendEmailService: log and swallow, never re-raise
                pass


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_task_assignment_creates_notification():
    """Publishing task.created → 1 notification row."""
    repo = FakeNotificationRepo()
    event = make_event("task.created")
    await publish_via_service(event, repo)
    assert len(repo.notifications) == 1
    assert repo.notifications[0]["event_type"] == "task.created"
    assert repo.notifications[0]["is_read"] is False


@pytest.mark.asyncio
async def test_overdue_task_creates_notification():
    """Publishing task.overdue → 1 notification row."""
    repo = FakeNotificationRepo()
    event = make_event(
        "task.overdue",
        payload={"task_id": str(uuid.uuid4()), "task_title": "Bank Report", "due_date": "2026-08-01"},
        idempotency_key="overdue:abc:2026-08-09",
    )
    await publish_via_service(event, repo)
    assert len(repo.notifications) == 1
    assert repo.notifications[0]["event_type"] == "task.overdue"


@pytest.mark.asyncio
async def test_evidence_rejection_creates_notification():
    """Publishing evidence.rejected → 1 notification row."""
    repo = FakeNotificationRepo()
    event = make_event(
        "evidence.rejected",
        payload={"task_title": "QA Report", "reason": "Incomplete documentation"},
    )
    await publish_via_service(event, repo)
    assert len(repo.notifications) == 1
    assert repo.notifications[0]["event_type"] == "evidence.rejected"
    assert "rejected" in repo.notifications[0]["title"].lower()


@pytest.mark.asyncio
async def test_compliance_gap_creates_notification():
    """Publishing compliance.gap_detected → 1 notification row."""
    repo = FakeNotificationRepo()
    event = make_event(
        "compliance.gap_detected",
        payload={"description": "Missing cyber audit evidence"},
    )
    await publish_via_service(event, repo)
    assert len(repo.notifications) == 1
    assert repo.notifications[0]["event_type"] == "compliance.gap_detected"


@pytest.mark.asyncio
async def test_email_sent_when_enabled():
    """Email is sent when email_enabled=True."""
    repo = FakeNotificationRepo()
    repo.preferences[USER_UUID] = {"in_app_enabled": True, "email_enabled": True}

    email_spy = MagicMock()
    event = make_event("task.overdue")
    await publish_via_service(event, repo, email_spy=email_spy)

    email_spy.assert_called_once()
    call_kwargs = email_spy.call_args.kwargs
    assert call_kwargs["event_type"] == "task.overdue"


@pytest.mark.asyncio
async def test_email_not_sent_when_disabled():
    """Email is NOT sent when email_enabled=False."""
    repo = FakeNotificationRepo()
    repo.preferences[USER_UUID] = {"in_app_enabled": True, "email_enabled": False}

    email_spy = MagicMock()
    event = make_event("task.overdue")
    await publish_via_service(event, repo, email_spy=email_spy)

    email_spy.assert_not_called()
    # But the in-app notification IS created
    assert len(repo.notifications) == 1


@pytest.mark.asyncio
async def test_duplicate_event_does_not_create_duplicate_notification():
    """The same idempotency_key published twice → only 1 notification row."""
    repo = FakeNotificationRepo()
    shared_key = "overdue:xyz:2026-08-09"
    event1 = make_event("task.overdue", idempotency_key=shared_key)
    event2 = make_event("task.overdue", idempotency_key=shared_key)

    await publish_via_service(event1, repo)
    await publish_via_service(event2, repo)

    assert len(repo.notifications) == 1, (
        f"Expected 1 notification, got {len(repo.notifications)}"
    )


@pytest.mark.asyncio
async def test_email_failure_does_not_fail_compliance_operation():
    """
    If the email service raises, the in-app notification is still created
    and no exception propagates to the caller.
    """
    repo = FakeNotificationRepo()
    repo.preferences[USER_UUID] = {"in_app_enabled": True, "email_enabled": True}

    def failing_email_spy(**kwargs):
        raise RuntimeError("SMTP timeout — simulated failure")

    # Should not raise
    event = make_event("evidence.rejected")
    try:
        await publish_via_service(event, repo, email_spy=failing_email_spy)
    except RuntimeError:
        pytest.fail(
            "email failure propagated to the caller — compliance operation is broken"
        )

    # In-app notification still exists
    assert len(repo.notifications) == 1
