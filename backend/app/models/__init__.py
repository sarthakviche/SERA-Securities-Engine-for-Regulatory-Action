"""
SERA Database Models — Package Init

Importing all models here ensures Alembic's target_metadata sees
every table when running autogenerate.
"""

from app.models.regulatory_document import RegulatoryDocument
from app.models.workflow_document import WorkflowDocument
from app.models.obligation import Obligation
from app.models.task import Task
from app.models.notification import Notification
from app.models.user_notification_preferences import UserNotificationPreferences

__all__ = [
    "RegulatoryDocument",
    "WorkflowDocument",
    "Obligation",
    "Task",
    "Notification",
    "UserNotificationPreferences",
]
