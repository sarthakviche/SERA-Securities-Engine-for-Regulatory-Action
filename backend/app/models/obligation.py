"""
Obligation SQLAlchemy Model

Maps to the `obligations` table.
Fields are driven by the mocked pipeline runner output in
app/pipeline/runner.py:

    obligations: [{"id": "obl-1", "title": "...", "category": "..."}]

The model extends that minimal shape with fields from the TRD that the
Obligation Agent will eventually populate once the LLM layer is wired in.
Only fields that the current or near-future agent output can plausibly
provide are included here — no speculative columns.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    String,
    Text,
    Float,
    DateTime,
    ForeignKey,
    Enum as SAEnum,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.db import Base

ObligationStatus = SAEnum(
    "pending",
    "active",
    "waived",
    "completed",
    name="obligation_status_enum",
)


class Obligation(Base):
    __tablename__ = "obligations"

    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    # FK → workflow_documents
    workflow_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workflow_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="FK to workflow_documents.id",
    )

    # Short label for the obligation (maps to "title" in runner mock output)
    title = Column(String(500), nullable=False)

    # Full textual description of the obligation
    description = Column(Text, nullable=True)

    # Category/domain, e.g. "Security", "KYC", "Reporting"
    # Maps to "category" in runner mock output
    category = Column(String(100), nullable=True)

    # How often this obligation must be met, e.g. "Monthly", "Annually", "On-event"
    frequency = Column(String(100), nullable=True)

    # What evidence is needed to demonstrate compliance
    evidence_type = Column(String(255), nullable=True)

    # Lifecycle status of the obligation
    status = Column(
        ObligationStatus,
        nullable=False,
        default="pending",
    )

    # LLM extraction confidence (0.0 – 1.0), null until LLM stage runs
    confidence_score = Column(Float, nullable=True)

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
        back_populates="obligations",
    )
    tasks = relationship(
        "Task",
        back_populates="obligation",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Obligation id={self.id} title={self.title!r} status={self.status!r}>"
