"""Structured standards metadata, separate from the legacy bootstrap database."""
from alembic import op
import sqlalchemy as sa

revision = "0001_standards_metadata"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("standards",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("standard_code", sa.String(120), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("scope", sa.Text(), nullable=False, server_default=""),
        sa.Column("abstract", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", sa.String(40), nullable=False, server_default="unverified"),
        sa.Column("revision", sa.Text()),
        sa.Column("publication_date", sa.Date()),
        sa.Column("withdrawn_date", sa.Date()),
        sa.Column("superseded_by", sa.String(120)),
        sa.Column("source_url", sa.Text()),
        sa.Column("is_mock", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("(is_mock = false OR status = 'unverified') AND (standard_code NOT LIKE 'IS-DEMO-%' OR is_mock = true)", name="ck_standards_mock_safety"))
    op.create_index("ix_standards_standard_code", "standards", ["standard_code"], unique=True)
    op.create_table("standard_keywords",
        sa.Column("standard_id", sa.Integer(), sa.ForeignKey("standards.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("keyword", sa.String(200), primary_key=True))
    op.create_table("standard_relationships",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_standard_id", sa.Integer(), sa.ForeignKey("standards.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_standard_id", sa.Integer(), sa.ForeignKey("standards.id", ondelete="CASCADE"), nullable=False),
        sa.Column("relationship_type", sa.String(80), nullable=False),
        sa.UniqueConstraint("source_standard_id", "target_standard_id", "relationship_type", name="uq_standard_relationship"))
    op.create_index("ix_standard_relationships_source_standard_id", "standard_relationships", ["source_standard_id"])
    op.create_index("ix_standard_relationships_target_standard_id", "standard_relationships", ["target_standard_id"])


def downgrade():
    op.drop_table("standard_relationships")
    op.drop_table("standard_keywords")
    op.drop_table("standards")
