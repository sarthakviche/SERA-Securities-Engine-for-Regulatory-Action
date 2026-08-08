"""Create core SERA tables

Revision ID: 001_core_tables
Revises: 
Create Date: 2026-08-08

Creates the four foundational tables for the SERA database:
  1. regulatory_documents  — SEBI circulars as scraped
  2. workflow_documents    — pipeline run records with JSONB swd
  3. obligations           — compliance obligations extracted from documents
  4. tasks                 — actionable tasks derived from obligations
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = "001_core_tables"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ─────────────────────────────────────────────────────────────────────
    # 0. ENUMs — create safely handling pre-existing types
    # ─────────────────────────────────────────────────────────────────────
    def create_enum_if_not_exists(name, values):
        op.execute(f"""
            DO $$ BEGIN
                CREATE TYPE {name} AS ENUM ({', '.join(f"'{v}'" for v in values)});
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        """)

    create_enum_if_not_exists("embedding_status_enum", ["pending", "processing", "completed", "failed"])
    create_enum_if_not_exists("workflow_status_enum", ["PENDING", "RUNNING", "COMPLETED", "FAILED"])
    create_enum_if_not_exists("obligation_status_enum", ["pending", "active", "waived", "completed"])
    create_enum_if_not_exists("task_status_enum", ["Pending", "In Progress", "Completed", "Overdue", "Blocked"])
    create_enum_if_not_exists("task_priority_enum", ["LOW", "MEDIUM", "HIGH", "CRITICAL"])

    # ─────────────────────────────────────────────────────────────────────
    # 1. regulatory_documents
    # ─────────────────────────────────────────────────────────────────────
    op.create_table(
        "regulatory_documents",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "circular_number",
            sa.String(255),
            nullable=False,
            unique=True,
            comment="Stable SEBI reference ID, e.g. SEBI-CIRC-2026-08-03-103314",
        ),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("issue_date", sa.String(20), nullable=True),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column(
            "file_ref",
            sa.Text,
            nullable=True,
            comment="PDF or detail page URL",
        ),
        sa.Column(
            "embedding_status",
            postgresql.ENUM(
                "pending", "processing", "completed", "failed",
                name="embedding_status_enum",
                create_type=False,
            ),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index(
        "ix_regulatory_documents_circular_number",
        "regulatory_documents",
        ["circular_number"],
    )

    # ─────────────────────────────────────────────────────────────────────
    # 2. workflow_documents
    # ─────────────────────────────────────────────────────────────────────
    op.create_table(
        "workflow_documents",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(
                "regulatory_documents.id",
                ondelete="CASCADE",
                name="fk_workflow_documents_document_id",
            ),
            nullable=False,
            comment="FK to regulatory_documents.id",
        ),
        sa.Column(
            "status",
            postgresql.ENUM(
                "PENDING", "RUNNING", "COMPLETED", "FAILED",
                name="workflow_status_enum",
                create_type=False,
            ),
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column("current_stage", sa.String(100), nullable=True),
        sa.Column(
            "progress",
            sa.Integer,
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "schema_version",
            sa.Integer,
            nullable=False,
            server_default="1",
        ),
        sa.Column(
            "swd",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
            comment="Shared Workflow Document — accumulates all stage outputs",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index(
        "ix_workflow_documents_document_id",
        "workflow_documents",
        ["document_id"],
    )
    op.create_index(
        "ix_workflow_documents_status",
        "workflow_documents",
        ["status"],
    )

    # ─────────────────────────────────────────────────────────────────────
    # 3. obligations
    # ─────────────────────────────────────────────────────────────────────
    op.create_table(
        "obligations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "workflow_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(
                "workflow_documents.id",
                ondelete="CASCADE",
                name="fk_obligations_workflow_id",
            ),
            nullable=False,
            comment="FK to workflow_documents.id",
        ),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("frequency", sa.String(100), nullable=True),
        sa.Column("evidence_type", sa.String(255), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM(
                "pending", "active", "waived", "completed",
                name="obligation_status_enum",
                create_type=False,
            ),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("confidence_score", sa.Float, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index(
        "ix_obligations_workflow_id",
        "obligations",
        ["workflow_id"],
    )

    # ─────────────────────────────────────────────────────────────────────
    # 4. tasks
    # ─────────────────────────────────────────────────────────────────────
    op.create_table(
        "tasks",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "workflow_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(
                "workflow_documents.id",
                ondelete="CASCADE",
                name="fk_tasks_workflow_id",
            ),
            nullable=False,
            comment="FK to workflow_documents.id",
        ),
        sa.Column(
            "obligation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(
                "obligations.id",
                ondelete="SET NULL",
                name="fk_tasks_obligation_id",
            ),
            nullable=True,
            comment="FK to obligations.id",
        ),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM(
                "Pending", "In Progress", "Completed", "Overdue", "Blocked",
                name="task_status_enum",
                create_type=False,
            ),
            nullable=False,
            server_default="Pending",
        ),
        sa.Column(
            "priority",
            postgresql.ENUM(
                "LOW", "MEDIUM", "HIGH", "CRITICAL",
                name="task_priority_enum",
                create_type=False,
            ),
            nullable=True,
            server_default="MEDIUM",
        ),
        sa.Column("due_date", sa.Date, nullable=True),
        sa.Column("evidence_requirement", sa.Text, nullable=True),
        sa.Column("recurrence_rule", sa.String(255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index(
        "ix_tasks_workflow_id",
        "tasks",
        ["workflow_id"],
    )
    op.create_index(
        "ix_tasks_obligation_id",
        "tasks",
        ["obligation_id"],
    )
    op.create_index(
        "ix_tasks_status",
        "tasks",
        ["status"],
    )


def downgrade() -> None:
    # Drop in reverse dependency order
    op.drop_index("ix_tasks_status", table_name="tasks")
    op.drop_index("ix_tasks_obligation_id", table_name="tasks")
    op.drop_index("ix_tasks_workflow_id", table_name="tasks")
    op.drop_table("tasks")

    op.drop_index("ix_obligations_workflow_id", table_name="obligations")
    op.drop_table("obligations")

    op.drop_index("ix_workflow_documents_status", table_name="workflow_documents")
    op.drop_index("ix_workflow_documents_document_id", table_name="workflow_documents")
    op.drop_table("workflow_documents")

    op.drop_index("ix_regulatory_documents_circular_number", table_name="regulatory_documents")
    op.drop_table("regulatory_documents")

    # Drop ENUMs
    op.execute("DROP TYPE IF EXISTS task_priority_enum")
    op.execute("DROP TYPE IF EXISTS task_status_enum")
    op.execute("DROP TYPE IF EXISTS obligation_status_enum")
    op.execute("DROP TYPE IF EXISTS workflow_status_enum")
    op.execute("DROP TYPE IF EXISTS embedding_status_enum")
