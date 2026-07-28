import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

# Role set is deliberately a plain string, not a Postgres ENUM, so later phases
# (QT01-04 domain-A roles: Phòng Thi công, Phòng Kế hoạch, Phòng Kế toán, HĐQT, ...)
# can add roles without an ALTER TYPE migration.
ROLES = (
    "cbnv",
    "phong_thiet_bi",
    "hcns_truong_phong",
    "lanh_dao_noi_chinh",
    "tgd",
    "admin",
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    full_name: Mapped[str | None] = mapped_column(String, nullable=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False, default="cbnv")
    google_sub: Mapped[str | None] = mapped_column(String, nullable=True, unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True
    )
    # HRIS's own employee code — set when the user was added via HRIS lookup
    # rather than typed in manually; also the natural re-sync key later.
    hris_emp_code: Mapped[str | None] = mapped_column(String, nullable=True, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
