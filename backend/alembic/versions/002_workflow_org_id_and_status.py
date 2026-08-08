"""Add organization_id and change status to varchar

Revision ID: 002_workflow_org_id_and_status
Revises: 001_core_tables
Create Date: 2026-08-08

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_workflow_org_id_and_status'
down_revision = '001_core_tables'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add organization_id
    op.execute(
        "ALTER TABLE workflow_documents "
        "ADD COLUMN organization_id UUID NOT NULL DEFAULT '00000000-0000-0000-0000-000000000001'"
    )
    
    # Change status to VARCHAR
    op.execute(
        "ALTER TABLE workflow_documents "
        "ALTER COLUMN status DROP DEFAULT"
    )
    
    op.execute(
        "ALTER TABLE workflow_documents "
        "ALTER COLUMN status TYPE VARCHAR(100) USING status::VARCHAR"
    )
    
    op.execute(
        "ALTER TABLE workflow_documents "
        "ALTER COLUMN status SET DEFAULT 'created'"
    )
    
    # Drop enum if not used elsewhere
    op.execute("DROP TYPE IF EXISTS workflow_status_enum")

def downgrade() -> None:
    # Re-create ENUM
    op.execute("CREATE TYPE workflow_status_enum AS ENUM ('PENDING', 'RUNNING', 'COMPLETED', 'FAILED')")
    
    # Change status back to ENUM
    op.execute(
        "ALTER TABLE workflow_documents "
        "ALTER COLUMN status DROP DEFAULT"
    )
    
    op.execute(
        "ALTER TABLE workflow_documents "
        "ALTER COLUMN status TYPE workflow_status_enum "
        "USING status::workflow_status_enum"
    )
    
    op.execute(
        "ALTER TABLE workflow_documents "
        "ALTER COLUMN status SET DEFAULT 'PENDING'"
    )
    
    # Drop organization_id
    op.drop_column('workflow_documents', 'organization_id')
