"""
NotificationService — orchestrates in-app notification creation.

Keeps business logic out of the repository layer.
"""

from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification
from app.models.user_notification_preferences import UserNotificationPreferences
from app.modules.notifications.repository_sql import NotificationRepository

logger = logging.getLogger("sera.notifications.service")


class NotificationService:
    def __init__(self, repo: NotificationRepository) -> None:
        self._repo = repo

    async def create(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        event_type: str,
        title: str,
        body: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[UUID] = None,
        idempotency_key: str,
    ) -> Optional[Notification]:
        """
        Create an in-app notification.

        Idempotent: if a notification with the same (user_id, idempotency_key)
        already exists the database constraint silently ignores the insert.
        """
        notification = await self._repo.create_notification(
            db,
            user_id=user_id,
            event_type=event_type,
            title=title,
            body=body,
            resource_type=resource_type,
            resource_id=resource_id,
            idempotency_key=idempotency_key,
        )
        if notification:
            logger.info(
                "notification created: type=%s user=%s key=%s",
                event_type,
                user_id,
                idempotency_key,
            )
        else:
            logger.debug(
                "notification skipped (duplicate idempotency key): key=%s",
                idempotency_key,
            )
        return notification

    async def list_for_user(
        self,
        db: AsyncSession,
        user_id: UUID,
        limit: int = 50,
        unread_only: bool = False,
    ) -> list[Notification]:
        return await self._repo.list_for_user(
            db, user_id, limit=limit, unread_only=unread_only
        )

    async def mark_read(
        self, db: AsyncSession, notification_id: UUID, user_id: UUID
    ) -> bool:
        return await self._repo.mark_read(db, notification_id, user_id)

    async def mark_all_read(self, db: AsyncSession, user_id: UUID) -> int:
        count = await self._repo.mark_all_read(db, user_id)
        logger.info("marked %d notifications read for user=%s", count, user_id)
        return count

    async def get_unread_count(self, db: AsyncSession, user_id: UUID) -> int:
        return await self._repo.get_unread_count(db, user_id)

    async def get_preferences(
        self, db: AsyncSession, user_id: UUID
    ) -> Optional[UserNotificationPreferences]:
        return await self._repo.get_preferences(db, user_id)

    async def upsert_preferences(
        self,
        db: AsyncSession,
        user_id: UUID,
        *,
        in_app_enabled: bool,
        email_enabled: bool,
    ) -> UserNotificationPreferences:
        return await self._repo.upsert_preferences(
            db,
            user_id,
            in_app_enabled=in_app_enabled,
            email_enabled=email_enabled,
        )


# Module-level singleton wired to the SQL repository
notification_service = NotificationService(repo=NotificationRepository())
