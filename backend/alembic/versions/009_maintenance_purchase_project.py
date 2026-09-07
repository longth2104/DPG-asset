"""Add purchase_date/project to assets, project to requests, the
asset_maintenance_records table, and documents.maintenance_record_id.

Per docs/cycle.md: purchase tracking, project-based ownership, and a
structured maintenance/repair log.

Revision ID: 009
Revises: 008
Create Date: 2026-09-08
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "009"
down_revision = "008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("assets", sa.Column("purchase_date", sa.Date, nullable=True))
    op.add_column("assets", sa.Column("project", sa.String, nullable=True))
    op.create_index("ix_assets_project", "assets", ["project"])

    op.add_column("requests", sa.Column("project", sa.String, nullable=True))

    op.create_table(
        "asset_maintenance_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String, nullable=False, server_default="reported"),
        sa.Column("reported_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("location", sa.String, nullable=True),
        sa.Column("cost", sa.Numeric(18, 2), nullable=True),
        sa.Column("condition_note", sa.Text, nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_asset_maintenance_records_asset_id", "asset_maintenance_records", ["asset_id"])

    op.add_column(
        "documents", sa.Column("maintenance_record_id", postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.create_foreign_key(
        "fk_documents_maintenance_record_id",
        "documents",
        "asset_maintenance_records",
        ["maintenance_record_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_documents_maintenance_record_id", "documents", ["maintenance_record_id"])


def downgrade() -> None:
    op.drop_index("ix_documents_maintenance_record_id", table_name="documents")
    op.drop_constraint("fk_documents_maintenance_record_id", "documents", type_="foreignkey")
    op.drop_column("documents", "maintenance_record_id")

    op.drop_index("ix_asset_maintenance_records_asset_id", table_name="asset_maintenance_records")
    op.drop_table("asset_maintenance_records")

    op.drop_column("requests", "project")

    op.drop_index("ix_assets_project", table_name="assets")
    op.drop_column("assets", "project")
    op.drop_column("assets", "purchase_date")
