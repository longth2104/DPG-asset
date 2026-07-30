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
    # Free-text department name for the requester's own unit (e.g. "Ban
    # CNTT") — User has no department field, and the real forms print this
    # in the header (acquire) / as Bên A (transfer's handover record), so
    # it's captured directly on the request instead of guessed at.
    requester_department: Mapped[str | None] = mapped_column(String, nullable=True)

    # transfer: who/where it's moving from and to. acquire: where it's needed.
    # Applies uniformly across every item in the request (one handover event
    # can bundle several devices to the same destination, per the real
    # Biên bản bàn giao template).
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
    # Bên B identity block for a handover recipient without a User account
    # (e.g. a department/branch contact) — matches the real Biên bản bàn
    # giao's identity fields (name/title/phone/email/CCCD).
    to_contact_name: Mapped[str | None] = mapped_column(String, nullable=True)
    to_contact_title: Mapped[str | None] = mapped_column(String, nullable=True)
    to_contact_phone: Mapped[str | None] = mapped_column(String, nullable=True)
    to_contact_email: Mapped[str | None] = mapped_column(String, nullable=True)
    to_contact_id_card: Mapped[str | None] = mapped_column(String, nullable=True)

    # acquire: the overall intro/reason paragraph (per-item "for whom" lives
    # on RequestItem.purpose).
    justification: Mapped[str | None] = mapped_column(Text, nullable=True)

    # liquidate: the overall proposal reason (per-item technical condition
    # lives on RequestItem.condition_note).
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    # JSON snapshot (list of {full_name, position, council_role}) of the
    # active CouncilMember roster at request creation time, so the printed
    # assessment/accounting forms stay stable even if membership changes
    # later. Text column — never queried into, only rendered.
    council_snapshot: Mapped[str | None] = mapped_column(Text, nullable=True)

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


class RequestItem(Base):
    """One line item within a request — every request type is a header plus
    a list of these, matching how the real BM forms are actually filled out
    (a purchase memo or handover record almost always covers several
    devices, not one)."""

    __tablename__ = "request_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("requests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Existing asset for transfer/liquidate items; null for acquire items
    # until approval creates the new asset (then filled in retroactively).
    # ON DELETE CASCADE: if the linked asset is deleted, this line item goes
    # with it — and if that empties a request of all its items, the request
    # itself is cleaned up too (see requests.py's delete/cleanup logic).
    asset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    unit: Mapped[str | None] = mapped_column(String, nullable=True)
    quantity: Mapped[int] = mapped_column(nullable=False, default=1)

    # acquire
    unit_price: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    manufacturer: Mapped[str | None] = mapped_column(String, nullable=True)
    purpose: Mapped[str | None] = mapped_column(Text, nullable=True)

    # liquidate
    remaining_value: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    market_value: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    proposed_value: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    # Set by the approver as part of deciding the request — the Quyết định
    # thanh lý's approved sale price, per item.
    approved_sale_price: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    condition_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


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
