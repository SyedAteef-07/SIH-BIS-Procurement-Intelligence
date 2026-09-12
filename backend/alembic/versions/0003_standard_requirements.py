"""Data-driven specification requirement metadata."""
from alembic import op
import sqlalchemy as sa

revision = "0003_standard_requirements"
down_revision = "0002_standard_certifications"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("standard_requirements",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("standard_id", sa.Integer(), sa.ForeignKey("standards.id", ondelete="CASCADE"), nullable=False),
        sa.Column("requirement_key", sa.String(120), nullable=False),
        sa.Column("label", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(120)),
        sa.Column("is_mandatory", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("source_section", sa.Text()),
        sa.UniqueConstraint("standard_id", "requirement_key", name="uq_standard_requirement"))
    op.create_index("ix_standard_requirements_standard_id", "standard_requirements", ["standard_id"])


def downgrade():
    op.drop_table("standard_requirements")
