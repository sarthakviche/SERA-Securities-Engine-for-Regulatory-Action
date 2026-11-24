"""Hash-chained, append-only audit log (tamper evident)."""
from datetime import datetime, timezone

from sqlalchemy import BigInteger, Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.core.db import Base


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    workflow_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    kind = Column(String(30), nullable=False)  # SYSTEM | AGENT | APPROVAL | EVIDENCE | REQUEST
    title = Column(String(300), nullable=False)
    detail = Column(Text, nullable=True)
    actor = Column(String(120), nullable=False)
    payload = Column(JSONB, nullable=True)
    prev_hash = Column(String(64), nullable=False)
    hash = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
