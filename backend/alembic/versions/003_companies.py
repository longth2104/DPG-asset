"""companies table; company_id on users/assets; rds_id on assets

Revision ID: 003
Revises: 002
Create Date: 2026-07-28
"""

import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None

# Seeded from the live RDS/HRIS company-code catalogs (see docs/featurex.md).
# All seeded FLAT (parent_id left null) — deliberately not guessing a
# hierarchy for something access-control-sensitive; use the Companies admin
# page to set real parent/subsidiary relationships once confirmed.
SEED_COMPANIES = [
    ("DPG", "Công ty Cổ phần Tập đoàn Đạt Phương"),
    ("DP1", "Công ty Cổ phần Xây dựng Đạt Phương số 1"),
    ("DP2", "Công ty Cổ phần Xây dựng Đạt Phương số 2"),
    ("DSB", "Công ty Cổ phần Thủy điện Đạt Phương Sông Bung"),
    ("DST", "Công ty Cổ phần Thủy điện Đạt Phương Sơn Trà"),
    ("FUK", "Công ty TNHH FUKUNANA"),
    # Not returned by RDS's company catalog (no assets tagged there yet) —
    # name is a placeholder from docs/feature-spec.md; confirm and correct
    # via the Companies admin page.
    ("DHA", "Đạt Phương Hội An"),
    ("KDP", "KDP"),
]


def upgrade() -> None:
    op.create_table(
        "companies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String, nullable=False),
        sa.Column("name", sa.String, nullable=False),
        sa.Column(
            "parent_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("companies.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("path", sa.String, nullable=False),
        sa.Column("grants_global_access", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_unique_constraint("uq_companies_code", "companies", ["code"])
    op.create_index("ix_companies_code", "companies", ["code"])
    op.create_index("ix_companies_path", "companies", ["path"])

    companies_table = sa.table(
        "companies",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("code", sa.String),
        sa.column("name", sa.String),
        sa.column("path", sa.String),
        sa.column("grants_global_access", sa.Boolean),
    )
    root_id = None
    rows = []
    for code, name in SEED_COMPANIES:
        cid = uuid.uuid4()
        is_root = code == "DPG"
        if is_root:
            root_id = cid
        rows.append(
            {
                "id": cid,
                "code": code,
                "name": name,
                "path": str(cid),
                "grants_global_access": is_root,
            }
        )
    op.bulk_insert(companies_table, rows)

    op.add_column(
        "users",
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("companies.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_users_company_id", "users", ["company_id"])
    op.add_column("users", sa.Column("hris_emp_code", sa.String, nullable=True))
    op.create_unique_constraint("uq_users_hris_emp_code", "users", ["hris_emp_code"])

    op.add_column(
        "assets",
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("companies.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_assets_company_id", "assets", ["company_id"])
    op.add_column("assets", sa.Column("rds_id", sa.Integer, nullable=True))
    op.create_unique_constraint("uq_assets_rds_id", "assets", ["rds_id"])
    op.create_index("ix_assets_rds_id", "assets", ["rds_id"])

    # Backfill: every asset/user existing today predates this feature and
    # belongs to the Group parent entity.
    if root_id is not None:
        op.execute(sa.text("UPDATE assets SET company_id = :cid").bindparams(cid=root_id))
        op.execute(sa.text("UPDATE users SET company_id = :cid").bindparams(cid=root_id))


def downgrade() -> None:
    op.drop_index("ix_assets_rds_id", table_name="assets")
    op.drop_constraint("uq_assets_rds_id", "assets", type_="unique")
    op.drop_column("assets", "rds_id")
    op.drop_index("ix_assets_company_id", table_name="assets")
    op.drop_column("assets", "company_id")

    op.drop_constraint("uq_users_hris_emp_code", "users", type_="unique")
    op.drop_column("users", "hris_emp_code")
    op.drop_index("ix_users_company_id", table_name="users")
    op.drop_column("users", "company_id")

    op.drop_table("companies")
