import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Matches HRIS's dept_code prefix and RDS's company_code (e.g. "DPG", "DHA").
    code: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="SET NULL"), nullable=True
    )
    # Materialized path of ancestor ids joined by "/", ending in this
    # company's own id — recomputed on create/reparent so "is company X
    # inside my subtree" is a cheap prefix match (Company.path.startswith)
    # instead of a recursive CTE on every asset/request query.
    path: Mapped[str] = mapped_column(String, nullable=False, index=True)
    # Explicit flag rather than "has no parent" — every company is seeded
    # flat (no parent yet), so tree position alone can't distinguish "the
    # designated all-seeing parent" from "just not organized yet." Only the
    # Group entity (DPG) has this set to True.
    grants_global_access: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
