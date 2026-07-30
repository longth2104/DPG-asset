import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

# Standing Hội đồng thanh lý tài sản roster, admin-managed — snapshotted
# onto each liquidate Request at creation time (see Request.council_snapshot)
# so historical paperwork stays stable across membership changes.
COUNCIL_ROLES = ("chu_tich", "pho_chu_tich", "thanh_vien")


class CouncilMember(Base):
    __tablename__ = "council_members"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    position: Mapped[str | None] = mapped_column(String, nullable=True)
    council_role: Mapped[str] = mapped_column(String, nullable=False, default="thanh_vien")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
