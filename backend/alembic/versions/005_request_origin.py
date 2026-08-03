"""requests gain origin + external_ref, for the e-office integration.

Revision ID: 005
Revises: 004
Create Date: 2026-07-30
"""

import sqlalchemy as sa
from alembic import op

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "requests",
        sa.Column("origin", sa.String, nullable=False, server_default="ams"),
    )
    op.add_column("requests", sa.Column("external_ref", sa.String, nullable=True))
    op.create_unique_constraint("uq_requests_external_ref", "requests", ["external_ref"])


def downgrade() -> None:
    op.drop_constraint("uq_requests_external_ref", "requests", type_="unique")
    op.drop_column("requests", "external_ref")
    op.drop_column("requests", "origin")
