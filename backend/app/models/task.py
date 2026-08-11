"""
Task SQLAlchemy Model

Maps to the `tasks` table.
Fields are driven by the mocked pipeline runner output in
app/pipeline/runner.py:

    tasks: [{"id": "tsk-1", "title": "...", "status": "Pending"}]

The model extends that shape with fields from the TRD that the Task
Generation Agent will eventually populate. Only fields plausibly
supportable by the current or near-future agent output are included.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    Date,
    ForeignKey,
    Enum as SAEnum,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.db import Base

TaskStatus = SAEnum(
    "Pending",
    "In Progress",
    "Completed",
    "Overdue",
    "Blocked",
    name="task_status_enum",
)

TaskPriority = SAEnum(
    "LOW",
    "MEDIUM",
    "HIGH",
    "CRITICAL",
    name="task_priority_enum",
)


class Task(Base):
    __tablename__ = "tasks"

    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    # FK → workflow_documents (the pipeline run that generated this task)
    workflow_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workflow_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="FK to workflow_documents.id",
    )

    # FK → obligations (nullable — a task may relate to a specific obligation)
    obligation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("obligations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="FK to obligations.id",
    )

    # Short title for the task — maps to "title" in runner mock output
    title = Column(String(500), nullable=False)

    # Optional longer description of what needs to be done
    description = Column(Text, nullable=True)

    # Lifecycle status — maps to "status" in runner mock output
    status = Column(
        TaskStatus,
        nullable=False,
        default="Pending",
        index=True,
    )

    # Priority level for urgency ordering
    priority = Column(
        TaskPriority,
        nullable=True,
        default="MEDIUM",
    )

    # Target completion date (date-only, no time component)
    due_date = Column(Date, nullable=True)

    # What evidence must be submitted when the task is marked complete
    evidence_requirement = Column(Text, nullable=True)

    # iCalendar RRULE string for recurring tasks, e.g. "FREQ=MONTHLY;BYMONTHDAY=15"
    recurrence_rule = Column(String(255), nullable=True)

    # Audit timestamps (UTC)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    workflow_document = relationship(
        "WorkflowDocument",
        back_populates="tasks",
    )
    obligation = relationship(
        "Obligation",
        back_populates="tasks",
    )

    def __repr__(self) -> str:
        return f"<Task id={self.id} title={self.title!r} status={self.status!r}>"
