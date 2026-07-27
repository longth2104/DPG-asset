"""holder_user_id on assets; requests + request_signatures

Revision ID: 002
Revises: 001
Create Date: 2026-07-23
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "assets",
        sa.Column(
            "holder_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_assets_holder_user_id", "assets", ["holder_user_id"])

    op.create_table(
        "requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("type", sa.String, nullable=False),
        sa.Column("status", sa.String, nullable=False, server_default="pending"),
        sa.Column(
            "requester_id",
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
        sa.Column("scope", sa.String, nullable=True),
        sa.Column(
            "from_holder_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "to_holder_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("from_department", sa.String, nullable=True),
        sa.Column("to_department", sa.String, nullable=True),
        sa.Column("from_location", sa.String, nullable=True),
        sa.Column("to_location", sa.String, nullable=True),
        sa.Column("justification", sa.Text, nullable=True),
        sa.Column("estimated_cost", sa.Numeric(18, 2), nullable=True),
        sa.Column("reason", sa.Text, nullable=True),
        sa.Column("condition_note", sa.Text, nullable=True),
        sa.Column("approver_role", sa.String, nullable=False),
        sa.Column(
            "decided_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decision_note", sa.Text, nullable=True),
        sa.Column(
            "generated_document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.id", ondelete="SET NULL"),
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
    op.create_index("ix_requests_type", "requests", ["type"])
    op.create_index("ix_requests_status", "requests", ["status"])
    op.create_index("ix_requests_asset_id", "requests", ["asset_id"])

    op.create_table(
        "request_signatures",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "request_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("requests.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "actor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role_in_flow", sa.String, nullable=False),
        sa.Column("signed_name", sa.String, nullable=False),
        sa.Column("signature_image_url", sa.String, nullable=True),
        sa.Column("content_hash", sa.String, nullable=False),
        sa.Column("signed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_request_signatures_request_id", "request_signatures", ["request_id"])


def downgrade() -> None:
    op.drop_table("request_signatures")
    op.drop_table("requests")
    op.drop_index("ix_assets_holder_user_id", table_name="assets")
    op.drop_column("assets", "holder_user_id")
