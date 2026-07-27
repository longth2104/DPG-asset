import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

# Three request types for this increment, matching docs/features.md — QT02
# (maintenance) and QT10 (office/IT helpdesk) are out of scope here, per
# docs/plan.md's phasing.
REQUEST_TYPES = ("transfer", "acquire", "liquidate")
REQUEST_STATUSES = ("pending", "approved", "rejected", "completed")
# Who the asset is being handed to / acquired for (transfer.to_scope, acquire.scope).
REQUEST_SCOPES = ("individual", "department", "branch", "project")

# Single fixed approver role per type for this increment — the value-tiered
# engine in docs/feature-spec.md §3.5 (300tr/2 tỷ/HĐQT ladder) is deferred to
# a later phase until real threshold numbers exist (docs/plan.md open Q3).
APPROVER_ROLE_BY_TYPE = {
    "transfer": "phong_thiet_bi",
    "acquire": "tgd",
    "liquidate": "tgd",
}


class Request(Base):
    __tablename__ = "requests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type: Mapped[str] = mapped_column(String, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending", index=True)

    requester_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    # Nullable: an `acquire` request has no asset yet — one may be created as
    # a manual follow-up once procurement fulfillment lands in a later phase.
    asset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=True, index=True
    )

    # transfer: who/where it's moving from and to. acquire: where it's needed.
    scope: Mapped[str | None] = mapped_column(String, nullable=True)
    from_holder_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    to_holder_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    from_department: Mapped[str | None] = mapped_column(String, nullable=True)
    to_department: Mapped[str | None] = mapped_column(String, nullable=True)
    from_location: Mapped[str | None] = mapped_column(String, nullable=True)
    to_location: Mapped[str | None] = mapped_column(String, nullable=True)

    # acquire
    justification: Mapped[str | None] = mapped_column(Text, nullable=True)
    estimated_cost: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)

    # liquidate
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    condition_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    # shared approval outcome
    approver_role: Mapped[str] = mapped_column(String, nullable=False)
    decided_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    decision_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Reserved for a future "freeze the signed PDF as a Document" step once
    # post-signature edits need blocking; unpopulated this increment — the
    # PDF is rendered fresh from live request/signature data on every fetch.
    generated_document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class RequestSignature(Base):
    __tablename__ = "request_signatures"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("requests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    actor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    # Which step this signs: "requester" at submission, "approver" at decision.
    role_in_flow: Mapped[str] = mapped_column(String, nullable=False)
    signed_name: Mapped[str] = mapped_column(String, nullable=False)
    # MinIO object name for a drawn/uploaded signature image, if provided —
    # typed-name confirmation alone is still a valid signature without one.
    signature_image_url: Mapped[str | None] = mapped_column(String, nullable=True)
    content_hash: Mapped[str] = mapped_column(String, nullable=False)
    signed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
