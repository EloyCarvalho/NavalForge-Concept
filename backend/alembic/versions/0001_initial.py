"""Initial project and calculation job tables.

Revision ID: 0001
"""

from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("project_id", sa.String(length=120), primary_key=True),
        sa.Column("name", sa.String(length=240), nullable=False),
        sa.Column("revision", sa.String(length=40), nullable=False),
        sa.Column("project_data", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "calculation_jobs",
        sa.Column("job_id", sa.String(length=80), primary_key=True),
        sa.Column("project_id", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("request_data", sa.JSON(), nullable=False),
        sa.Column("result_data", sa.JSON(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_calculation_jobs_project_id", "calculation_jobs", ["project_id"])
    op.create_index("ix_calculation_jobs_status", "calculation_jobs", ["status"])


def downgrade() -> None:
    op.drop_table("calculation_jobs")
    op.drop_table("projects")
