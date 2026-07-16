"""Add immutable project revision history.

Revision ID: 0002
"""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "project_revisions",
        sa.Column("revision_id", sa.String(length=80), primary_key=True),
        sa.Column(
            "project_id",
            sa.String(length=120),
            sa.ForeignKey("projects.project_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("revision", sa.String(length=40), nullable=False),
        sa.Column("change_summary", sa.Text(), nullable=False),
        sa.Column("project_data", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_project_revisions_project_id", "project_revisions", ["project_id"])
    op.create_index("ix_project_revisions_revision", "project_revisions", ["revision"])


def downgrade() -> None:
    op.drop_index("ix_project_revisions_revision", table_name="project_revisions")
    op.drop_index("ix_project_revisions_project_id", table_name="project_revisions")
    op.drop_table("project_revisions")
