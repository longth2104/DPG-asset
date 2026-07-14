"""initial schema: users, assets, asset_events, documents

Revision ID: 001
Revises:
Create Date: 2026-07-14
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String, nullable=False, unique=True),
        sa.Column("full_name", sa.String, nullable=True),
        sa.Column("password_hash", sa.String, nullable=False),
        sa.Column("role", sa.String, nullable=False, server_default="cbnv"),
        sa.Column("google_sub", sa.String, nullable=True, unique=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("asset_code", sa.String, nullable=True, unique=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("category", sa.String, nullable=True),
        sa.Column("spec", sa.Text, nullable=True),
        sa.Column("serial_number", sa.String, nullable=True),
        sa.Column("manufacturer", sa.String, nullable=True),
        sa.Column("manufacture_year", sa.Integer, nullable=True),
        sa.Column("year_put_in_use", sa.Date, nullable=True),
        sa.Column("original_cost", sa.Numeric(18, 2), nullable=True),
        sa.Column("warranty_months", sa.Integer, nullable=True),
        sa.Column("legal_entity", sa.String, nullable=False, server_default="Đạt Phương"),
        sa.Column("department", sa.String, nullable=True),
        sa.Column("holder", sa.String, nullable=True),
        sa.Column("location", sa.String, nullable=True),
        sa.Column("status", sa.String, nullable=False, server_default="dang_su_dung"),
        sa.Column("domain", sa.String, nullable=False, server_default="b"),
        sa.Column("budget_plan_year", sa.Integer, nullable=True),
        sa.Column("budget_actual_year", sa.Integer, nullable=True),
        sa.Column("replacement_priority", sa.String, nullable=True),
        sa.Column("purchase_source", sa.String, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )
    op.create_index("ix_assets_asset_code", "assets", ["asset_code"])
    op.create_index("ix_assets_category", "assets", ["category"])
    op.create_index("ix_assets_department", "assets", ["department"])
    op.create_index("ix_assets_location", "assets", ["location"])
    op.create_index("ix_assets_status", "assets", ["status"])

    op.create_table(
        "asset_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "asset_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("assets.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("type", sa.String, nullable=False),
        sa.Column(
            "actor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("note", sa.Text, nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_asset_events_asset_id", "asset_events", ["asset_id"])

    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("filename", sa.String, nullable=False),
        sa.Column("file_url", sa.String, nullable=False),
        sa.Column("content_type", sa.String, nullable=True),
        sa.Column("size_bytes", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_private", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("secure_view", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column(
            "uploaded_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "asset_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("assets.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_documents_asset_id", "documents", ["asset_id"])


def downgrade() -> None:
    op.drop_table("documents")
    op.drop_table("asset_events")
    op.drop_table("assets")
    op.drop_table("users")
