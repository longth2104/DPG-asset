"""Backfill assets.company_id from the creator's own company, for existing
rows imported before company became a compulsory field (see docs/field.md:
"for the asset that are already imported, treat them as default").

Revision ID: 008
Revises: 007
Create Date: 2026-08-20
"""

from alembic import op

revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE assets
        SET company_id = users.company_id
        FROM users
        WHERE assets.created_by = users.id
          AND assets.company_id IS NULL
          AND users.company_id IS NOT NULL
        """
    )


def downgrade() -> None:
    # Data-only backfill — no schema change, and the original NULLs aren't
    # recoverable (nor worth recovering) on downgrade.
    pass
