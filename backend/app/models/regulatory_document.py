"""
RegulatoryDocument SQLAlchemy Model

Maps to the `regulatory_documents` table.
Represents a SEBI regulatory circular/document as scraped from the website.
Fields are derived from the Document Pydantic schema in
app/modules/documents/schemas.py and the SERA TRD.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, Text, Enum as SAEnum, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.db import Base

# Valid embedding processing states
EmbeddingStatus = SAEnum(
    "pending",
    "processing",
    "completed",
    "failed",
    name="embedding_status_enum",
)


class RegulatoryDocument(Base):
    __tablename__ = "regulatory_documents"

    # Primary key — UUID for global uniqueness
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    # Stable SEBI reference ID, e.g. "SEBI-CIRC-2026-08-03-103314"
    # Sourced from Document.document_id / scraper reference field
    circular_number = Column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        comment="Stable SEBI reference ID, e.g. SEBI-CIRC-2026-08-03-103314",
    )

    # Full title of the regulatory circular
    title = Column(Text, nullable=False)

    # ISO 8601 date string as scraped, e.g. "2026-08-03"
    issue_date = Column(String(20), nullable=True)

    # Category as returned by the scraper, e.g. "Circulars"
    category = Column(String(100), nullable=True)

    # Relative or absolute URL to the detail page / PDF
    file_ref = Column(Text, nullable=True, comment="PDF or detail page URL")

    # Status of embedding generation for this document (future: pgvector)
    embedding_status = Column(
        EmbeddingStatus,
        nullable=False,
        default="pending",
    )

    # Audit timestamps (UTC)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationship — one document can have many workflow processing runs
    workflow_documents = relationship(
        "WorkflowDocument",
        back_populates="regulatory_document",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<RegulatoryDocument id={self.id} circular_number={self.circular_number!r}>"
