"""SERA engine: richer obligations/tasks/documents, hash-chained audit, org profile

Revision ID: 004_engine_audit_profile
Revises: 003_notifications
Create Date: 2026-11-24
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "004_engine_audit_profile"
down_revision = "003_notifications"
branch_labels = None
depends_on = None

JSONB = postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    # regulatory_documents
    for name, col in [
        ("source", sa.Column("source", sa.String(20), nullable=False, server_default="SEBI")),
        ("summary", sa.Column("summary", sa.Text, nullable=True)),
        ("risk", sa.Column("risk", sa.String(20), nullable=True)),
        ("pdf_url", sa.Column("pdf_url", sa.Text, nullable=True)),
        ("local_path", sa.Column("local_path", sa.Text, nullable=True)),
        ("origin", sa.Column("origin", sa.String(20), nullable=False, server_default="scraped")),
        ("text_hash", sa.Column("text_hash", sa.String(64), nullable=True)),
        ("analysis_meta", sa.Column("analysis_meta", JSONB, nullable=True)),
    ]:
        op.add_column("regulatory_documents", col)

    # obligations
    for col in [
        sa.Column("code", sa.String(40), nullable=True),
        sa.Column("clause_ref", sa.String(120), nullable=True),
        sa.Column("source_text", sa.Text, nullable=True),
        sa.Column("page_number", sa.Integer, nullable=True),
        sa.Column("deadline", sa.String(120), nullable=True),
        sa.Column("due_date", sa.Date, nullable=True),
        sa.Column("department", sa.String(120), nullable=True),
        sa.Column("owner", sa.String(120), nullable=True),
        sa.Column("risk", sa.String(20), nullable=True),
        sa.Column("applicable", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("applicability_reason", sa.Text, nullable=True),
        sa.Column("ambiguity", JSONB, nullable=True),
        sa.Column("impact", JSONB, nullable=True),
        sa.Column("excluded", sa.Boolean, nullable=False, server_default=sa.false()),
    ]:
        op.add_column("obligations", col)

    # tasks
    for col in [
        sa.Column("department", sa.String(120), nullable=True),
        sa.Column("assignee", sa.String(120), nullable=True),
        sa.Column("phase", sa.String(60), nullable=True),
        sa.Column("evidence_note", sa.Text, nullable=True),
        sa.Column("evidence_files", JSONB, nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    ]:
        op.add_column("tasks", col)

    op.create_table(
        "audit_events",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("workflow_id", postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("kind", sa.String(30), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("detail", sa.Text, nullable=True),
        sa.Column("actor", sa.String(120), nullable=False),
        sa.Column("payload", JSONB, nullable=True),
        sa.Column("prev_hash", sa.String(64), nullable=False),
        sa.Column("hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "org_profile",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("entity_types", JSONB, nullable=False),
        sa.Column("departments", JSONB, nullable=False),
        sa.Column("systems", JSONB, nullable=False),
        sa.Column("officer_name", sa.String(120), nullable=True),
        sa.Column("onboarded", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("org_profile")
    op.drop_table("audit_events")
    for c in ["department", "assignee", "phase", "evidence_note", "evidence_files", "completed_at"]:
        op.drop_column("tasks", c)
    for c in ["code", "clause_ref", "source_text", "page_number", "deadline", "due_date", "department", "owner",
              "risk", "applicable", "applicability_reason", "ambiguity", "impact", "excluded"]:
        op.drop_column("obligations", c)
    for c in ["source", "summary", "risk", "pdf_url", "local_path", "origin", "text_hash", "analysis_meta"]:
        op.drop_column("regulatory_documents", c)
