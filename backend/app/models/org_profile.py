"""Single-row organisation profile captured during onboarding."""
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSONB

from app.core.db import Base


class OrgProfile(Base):
    __tablename__ = "org_profile"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    entity_types = Column(JSONB, nullable=False)
    departments = Column(JSONB, nullable=False)
    systems = Column(JSONB, nullable=False)
    officer_name = Column(String(120), nullable=True)
    onboarded = Column(Boolean, nullable=False, default=False)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))
