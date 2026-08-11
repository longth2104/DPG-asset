"""Add assets.extra_fields — captures unmapped Excel import columns.

Revision ID: 007
Revises: 006
Create Date: 2026-08-11
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("assets", sa.Column("extra_fields", postgresql.JSONB, nullable=True))


def downgrade() -> None:
    op.drop_column("assets", "extra_fields")
