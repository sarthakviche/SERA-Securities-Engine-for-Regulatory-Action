"""
Pydantic schemas for the Notifications module.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class NotificationOut(BaseModel):
    """Serialised notification returned to the frontend."""
    id: UUID
    user_id: UUID
    event_type: str
    title: str
    body: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[UUID] = None
    is_read: bool
    idempotency_key: str
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationListResponse(BaseModel):
    notifications: list[NotificationOut]
    unread_count: int


class PreferencesOut(BaseModel):
    """Notification preferences for a user."""
    user_id: UUID
    in_app_enabled: bool
    email_enabled: bool

    model_config = {"from_attributes": True}


class PreferencesUpdate(BaseModel):
    """Request body for updating notification preferences."""
    in_app_enabled: bool
    email_enabled: bool
