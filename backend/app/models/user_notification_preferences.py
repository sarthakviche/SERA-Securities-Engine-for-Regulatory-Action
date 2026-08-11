"""
UserNotificationPreferences SQLAlchemy Model

Maps to the `user_notification_preferences` table.

One row per user. Stores simple boolean flags controlling whether that user
receives in-app notifications and email notifications.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID

from app.core.db import Base


class UserNotificationPreferences(Base):
    __tablename__ = "user_notification_preferences"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    # One row per user — UNIQUE enforces that.
    user_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        unique=True,
        index=True,
    )

    # Whether in-app (SSE / panel) notifications are enabled for this user.
    in_app_enabled = Column(Boolean, nullable=False, default=True)

    # Whether transactional emails are sent for this user.
    email_enabled = Column(Boolean, nullable=False, default=True)

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return (
            f"<UserNotificationPreferences user={self.user_id} "
            f"in_app={self.in_app_enabled} email={self.email_enabled}>"
        )
