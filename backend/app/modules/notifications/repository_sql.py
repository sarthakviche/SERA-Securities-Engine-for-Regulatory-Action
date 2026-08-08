"""
SQLAlchemy implementation of the notification repository.

All writes use INSERT … ON CONFLICT DO NOTHING so that retrying the same
DomainEvent never produces a duplicate notification row.
"""

from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID

from sqlalchemy import select, update, func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification
from app.models.user_notification_preferences import UserNotificationPreferences

logger = logging.getLogger("sera.notifications.repository")


class NotificationRepository:
    """Data-access layer for notifications and preferences."""

    # ── Notifications ─────────────────────────────────────────────────────────

    async def create_notification(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        event_type: str,
        title: str,
        body: Optional[str],
        resource_type: Optional[str],
        resource_id: Optional[UUID],
        idempotency_key: str,
    ) -> Optional[Notification]:
        """
        Insert a notification row.

        Uses INSERT … ON CONFLICT (user_id, idempotency_key) DO NOTHING so
        processing the same event twice is safe.  Returns the existing or
        newly created row, or None if idempotency check skipped the insert
        (caller should not care — the row already exists).
        """
        stmt = (
            pg_insert(Notification)
            .values(
                user_id=user_id,
                event_type=event_type,
                title=title,
                body=body,
                resource_type=resource_type,
                resource_id=resource_id,
                idempotency_key=idempotency_key,
                is_read=False,
            )
            .on_conflict_do_nothing(constraint="uq_notification_user_idem")
            .returning(Notification)
        )
        result = await db.execute(stmt)
        row = result.scalar_one_or_none()
        return row

    async def list_for_user(
        self,
        db: AsyncSession,
        user_id: UUID,
        *,
        limit: int = 50,
        unread_only: bool = False,
    ) -> list[Notification]:
        stmt = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
        )
        if unread_only:
            stmt = stmt.where(Notification.is_read.is_(False))
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def mark_read(
        self,
        db: AsyncSession,
        notification_id: UUID,
        user_id: UUID,
    ) -> bool:
        stmt = (
            update(Notification)
            .where(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
            .values(is_read=True)
        )
        result = await db.execute(stmt)
        return result.rowcount > 0

    async def mark_all_read(self, db: AsyncSession, user_id: UUID) -> int:
        stmt = (
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            )
            .values(is_read=True)
        )
        result = await db.execute(stmt)
        return result.rowcount

    async def get_unread_count(self, db: AsyncSession, user_id: UUID) -> int:
        stmt = select(func.count()).where(
            Notification.user_id == user_id,
            Notification.is_read.is_(False),
        )
        result = await db.execute(stmt)
        return result.scalar_one()

    # ── Preferences ───────────────────────────────────────────────────────────

    async def get_preferences(
        self,
        db: AsyncSession,
        user_id: UUID,
    ) -> Optional[UserNotificationPreferences]:
        stmt = select(UserNotificationPreferences).where(
            UserNotificationPreferences.user_id == user_id
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert_preferences(
        self,
        db: AsyncSession,
        user_id: UUID,
        *,
        in_app_enabled: bool,
        email_enabled: bool,
    ) -> UserNotificationPreferences:
        stmt = (
            pg_insert(UserNotificationPreferences)
            .values(
                user_id=user_id,
                in_app_enabled=in_app_enabled,
                email_enabled=email_enabled,
            )
            .on_conflict_do_update(
                index_elements=["user_id"],
                set_={
                    "in_app_enabled": in_app_enabled,
                    "email_enabled": email_enabled,
                },
            )
            .returning(UserNotificationPreferences)
        )
        result = await db.execute(stmt)
        return result.scalar_one()


# Module-level singleton
notification_repository = NotificationRepository()
