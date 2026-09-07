import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

# Structured maintenance/repair history per docs/cycle.md — separate from the
# generic AssetEvent free-text timeline so cost/condition/dates are queryable
# on their own (e.g. summing repair spend, feeding the eventual liquidation
# value calc), the same way Request/RequestItem are their own tables rather
# than folded into the generic log.
MAINTENANCE_STATUSES = ("reported", "in_progress", "resolved")


class AssetMaintenanceRecord(Base):
    __tablename__ = "asset_maintenance_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String, nullable=False, default="reported")
    # When the issue was reported / repair work started.
    reported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # Set when the repair is closed out — also the signal that flips the
    # asset's own status back from "dang_sua_chua" (see api/assets.py).
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    location: Mapped[str | None] = mapped_column(String, nullable=True)
    cost: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    # Asset integrity/condition assessment — filled in at report time and/or
    # updated once resolved (e.g. "sửa xong, hoạt động bình thường").
    condition_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
