"""request_items, council_members; requests gains contact/council fields;
drops the old singular asset_id/estimated_cost/condition_note in favor of
per-item fields on request_items.

Revision ID: 004
Revises: 003
Create Date: 2026-07-29
"""

import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "request_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "request_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("requests.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "asset_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("assets.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("unit", sa.String, nullable=True),
        sa.Column("quantity", sa.Integer, nullable=False, server_default="1"),
        sa.Column("unit_price", sa.Numeric(18, 2), nullable=True),
        sa.Column("manufacturer", sa.String, nullable=True),
        sa.Column("purpose", sa.Text, nullable=True),
        sa.Column("remaining_value", sa.Numeric(18, 2), nullable=True),
        sa.Column("market_value", sa.Numeric(18, 2), nullable=True),
        sa.Column("proposed_value", sa.Numeric(18, 2), nullable=True),
        sa.Column("approved_sale_price", sa.Numeric(18, 2), nullable=True),
        sa.Column("condition_note", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_request_items_request_id", "request_items", ["request_id"])
    op.create_index("ix_request_items_asset_id", "request_items", ["asset_id"])

    op.create_table(
        "council_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("full_name", sa.String, nullable=False),
        sa.Column("position", sa.String, nullable=True),
        sa.Column("council_role", sa.String, nullable=False, server_default="thanh_vien"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.add_column("requests", sa.Column("requester_department", sa.String, nullable=True))
    op.add_column("requests", sa.Column("to_contact_name", sa.String, nullable=True))
    op.add_column("requests", sa.Column("to_contact_title", sa.String, nullable=True))
    op.add_column("requests", sa.Column("to_contact_phone", sa.String, nullable=True))
    op.add_column("requests", sa.Column("to_contact_email", sa.String, nullable=True))
    op.add_column("requests", sa.Column("to_contact_id_card", sa.String, nullable=True))
    op.add_column("requests", sa.Column("council_snapshot", sa.Text, nullable=True))

    # Backfill: migrate any existing single-asset requests into request_items
    # before dropping the old column, so no historical request loses its
    # asset linkage.
    conn = op.get_bind()
    existing = conn.execute(
        sa.text(
            "SELECT r.id AS request_id, r.asset_id AS asset_id, a.name AS name "
            "FROM requests r JOIN assets a ON a.id = r.asset_id "
            "WHERE r.asset_id IS NOT NULL"
        )
    ).fetchall()
    if existing:
        request_items_table = sa.table(
            "request_items",
            sa.column("id", postgresql.UUID(as_uuid=True)),
            sa.column("request_id", postgresql.UUID(as_uuid=True)),
            sa.column("asset_id", postgresql.UUID(as_uuid=True)),
            sa.column("name", sa.String),
            sa.column("quantity", sa.Integer),
        )
        op.bulk_insert(
            request_items_table,
            [
                {
                    "id": uuid.uuid4(),
                    "request_id": row.request_id,
                    "asset_id": row.asset_id,
                    "name": row.name,
                    "quantity": 1,
                }
                for row in existing
            ],
        )

    op.drop_constraint("requests_asset_id_fkey", "requests", type_="foreignkey")
    op.drop_index("ix_requests_asset_id", table_name="requests")
    op.drop_column("requests", "asset_id")
    # Superseded by request_items.unit_price/quantity and .condition_note.
    op.drop_column("requests", "estimated_cost")
    op.drop_column("requests", "condition_note")


def downgrade() -> None:
    op.add_column("requests", sa.Column("condition_note", sa.Text, nullable=True))
    op.add_column("requests", sa.Column("estimated_cost", sa.Numeric(18, 2), nullable=True))
    op.add_column(
        "requests",
        sa.Column(
            "asset_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("assets.id", ondelete="CASCADE"),
            nullable=True,
        ),
    )
    op.create_index("ix_requests_asset_id", "requests", ["asset_id"])

    op.drop_column("requests", "council_snapshot")
    op.drop_column("requests", "to_contact_id_card")
    op.drop_column("requests", "to_contact_email")
    op.drop_column("requests", "to_contact_phone")
    op.drop_column("requests", "to_contact_title")
    op.drop_column("requests", "to_contact_name")
    op.drop_column("requests", "requester_department")

    op.drop_table("council_members")
    op.drop_index("ix_request_items_asset_id", table_name="request_items")
    op.drop_index("ix_request_items_request_id", table_name="request_items")
    op.drop_table("request_items")
