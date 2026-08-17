import uuid
from datetime import date, datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

# Controlled vocabularies kept as plain strings (validated in the Pydantic schema)
# rather than Postgres ENUMs, matching the User.role rationale — status options
# specifically will grow once the QT02/QT04 workflows land.
ASSET_STATUSES = (
    "dang_su_dung",
    "dang_sua_chua",
    "cho_thanh_ly",
    "da_thanh_ly",
    "da_dieu_dong",
)
ASSET_DOMAINS = ("a", "b")  # a = construction machinery (QT01-04), b = office/IT (QT10)

# Single source of truth for the Vietnamese label of each status — shared by
# the Excel export/import round-trip and the PDF export template so a
# re-imported sheet maps back to the same enum value it was exported with.
ASSET_STATUS_LABELS = {
    "dang_su_dung": "Đang sử dụng",
    "dang_sua_chua": "Đang sửa chữa",
    "cho_thanh_ly": "Chờ thanh lý",
    "da_thanh_ly": "Đã thanh lý",
    "da_dieu_dong": "Đã điều động",
}


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_code: Mapped[str | None] = mapped_column(String, unique=True, nullable=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    spec: Mapped[str | None] = mapped_column(Text, nullable=True)
    serial_number: Mapped[str | None] = mapped_column(String, nullable=True)
    manufacturer: Mapped[str | None] = mapped_column(String, nullable=True)
    manufacture_year: Mapped[int | None] = mapped_column(nullable=True)
    year_put_in_use: Mapped[date | None] = mapped_column(nullable=True)
    original_cost: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    warranty_months: Mapped[int | None] = mapped_column(nullable=True)
    legal_entity: Mapped[str] = mapped_column(String, nullable=False, default="Đạt Phương")
    department: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    holder: Mapped[str | None] = mapped_column(String, nullable=True)
    # Nullable link to a real account. Excel import tries to resolve this at
    # import time — reliably via a holder_email column, or (best-effort) by
    # matching the free-text holder name against HRIS when the name is
    # unambiguous (see find_user_by_name) — but never guesses on a collision,
    # so some rows still end up with `holder` as text only until someone
    # reassigns them through the app. RDS sync never touches this field at
    # all (RDS carries no holder/assignment data).
    holder_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    # Access-control company (which legal entity's staff can see/edit this
    # asset) — distinct from `legal_entity` above, which stays a free-text
    # display label for now rather than being migrated onto this FK.
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True
    )
    # RDS's own stable numeric id — the upsert-match key for asset sync,
    # since `asset_code` can be edited but this shouldn't change.
    rds_id: Mapped[int | None] = mapped_column(nullable=True, index=True)
    location: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="dang_su_dung", index=True)
    domain: Mapped[str] = mapped_column(String, nullable=False, default="b")
    budget_plan_year: Mapped[int | None] = mapped_column(nullable=True)
    budget_actual_year: Mapped[int | None] = mapped_column(nullable=True)
    replacement_priority: Mapped[str | None] = mapped_column(String, nullable=True)
    purchase_source: Mapped[str | None] = mapped_column(String, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Columns encountered on Excel import that don't match any known field
    # above — keyed by the raw header text as it appeared in the sheet, so
    # nothing an import file contains is silently dropped even when this
    # app's schema has no dedicated field for it (e.g. per-software license
    # status columns). Never written by the create/edit form; import-only.
    extra_fields: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
