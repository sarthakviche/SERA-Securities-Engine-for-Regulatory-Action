"""
Notification SQLAlchemy Model

Maps to the `notifications` table.

Each row is one in-app notification for a user, created when a DomainEvent
fires. The `idempotency_key` column is unique-per-user so that retrying the
same event never produces a duplicate notification.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID

from app.core.db import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    # The user this notification belongs to.
    # In the current single-tenant MVP this is always the org's default user ID.
    user_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    # The domain event type that triggered this notification.
    # e.g. "task.created", "task.overdue", "evidence.rejected"
    event_type = Column(String(100), nullable=False)

    # Short human-readable title shown in the notification panel header.
    title = Column(String(255), nullable=False)

    # One-line body text shown below the title.
    body = Column(Text, nullable=True)

    # The type of entity this notification links to (task, workflow, obligation).
    resource_type = Column(String(50), nullable=True)

    # UUID of the specific entity record.
    resource_id = Column(UUID(as_uuid=True), nullable=True)

    # False until the user marks this notification as read.
    is_read = Column(Boolean, nullable=False, default=False)

    # Copied verbatim from DomainEvent.idempotency_key.
    # The UNIQUE constraint (user_id, idempotency_key) prevents duplicate rows
    # if the same event is processed more than once.
    idempotency_key = Column(String(255), nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        UniqueConstraint("user_id", "idempotency_key", name="uq_notification_user_idem"),
        Index("ix_notifications_user_unread", "user_id", "is_read"),
    )

    def __repr__(self) -> str:
        return (
            f"<Notification id={self.id} user={self.user_id} "
            f"event={self.event_type!r} read={self.is_read}>"
        )
