"""
WorkflowDocument SQLAlchemy Model

Maps to the `workflow_documents` table.
One WorkflowDocument is created per pipeline run for a RegulatoryDocument.
The `swd` JSONB column holds the evolving Shared Workflow Document produced
by the multi-stage pipeline.

Status values mirror the PipelineStatus schema:
  PENDING → RUNNING → COMPLETED | FAILED
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    String,
    DateTime,
    Integer,
    ForeignKey,
    Enum as SAEnum,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.db import Base

WorkflowStatus = SAEnum(
    "PENDING",
    "RUNNING",
    "COMPLETED",
    "FAILED",
    name="workflow_status_enum",
)


class WorkflowDocument(Base):
    __tablename__ = "workflow_documents"

    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    # FK → regulatory_documents
    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("regulatory_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="FK to regulatory_documents.id",
    )

    # Overall pipeline status
    status = Column(
        WorkflowStatus,
        nullable=False,
        default="PENDING",
        index=True,
    )

    # Human-readable name of the currently executing pipeline stage
    # e.g. "Obligation Agent", "Completed"
    current_stage = Column(String(100), nullable=True)

    # Progress as a percentage 0-100, mirrors runner.update_status()
    progress = Column(Integer, nullable=False, default=0)

    # Schema version — allows future migrations of the swd payload structure
    schema_version = Column(Integer, nullable=False, default=1)

    # Shared Workflow Document — evolving JSONB blob that accumulates all
    # stage outputs (obligations, tasks, applicability, ambiguity, etc.)
    swd = Column(JSONB, nullable=False, default=dict)

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
    regulatory_document = relationship(
        "RegulatoryDocument",
        back_populates="workflow_documents",
    )
    obligations = relationship(
        "Obligation",
        back_populates="workflow_document",
        cascade="all, delete-orphan",
    )
    tasks = relationship(
        "Task",
        back_populates="workflow_document",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<WorkflowDocument id={self.id} "
            f"status={self.status!r} stage={self.current_stage!r}>"
        )
