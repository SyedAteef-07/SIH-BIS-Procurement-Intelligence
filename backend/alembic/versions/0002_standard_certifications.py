"""Structured certification metadata; no claim of verified applicability."""
from alembic import op
import sqlalchemy as sa

revision = "0002_standard_certifications"
down_revision = "0001_standards_metadata"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("standard_certifications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("standard_id", sa.Integer(), sa.ForeignKey("standards.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("authority", sa.Text(), nullable=False),
        sa.Column("applicable", sa.Boolean(), nullable=True),
        sa.Column("status", sa.String(40), nullable=False, server_default="unverified"),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.UniqueConstraint("standard_id", "name", name="uq_standard_certification"))
    op.create_index("ix_standard_certifications_standard_id", "standard_certifications", ["standard_id"])


def downgrade():
    op.drop_table("standard_certifications")
