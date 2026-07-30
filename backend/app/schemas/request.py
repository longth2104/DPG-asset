import uuid
from datetime import datetime

from pydantic import BaseModel


class UserBrief(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str | None = None

    model_config = {"from_attributes": True}


class AssetBrief(BaseModel):
    id: uuid.UUID
    asset_code: str | None = None
    name: str

    model_config = {"from_attributes": True}


class RequestItemCreate(BaseModel):
    # Required for transfer/liquidate items (an existing asset); absent for
    # acquire items (the asset doesn't exist yet).
    asset_id: uuid.UUID | None = None
    # Required for acquire (there's no asset to pull a name from yet);
    # optional for transfer/liquidate, where it defaults to the asset's name.
    name: str | None = None
    unit: str | None = None
    quantity: int = 1
    unit_price: float | None = None
    manufacturer: str | None = None
    purpose: str | None = None
    remaining_value: float | None = None
    market_value: float | None = None
    proposed_value: float | None = None
    condition_note: str | None = None


class RequestItemDecision(BaseModel):
    id: uuid.UUID
    approved_sale_price: float | None = None


class CouncilSnapshotMember(BaseModel):
    full_name: str
    position: str | None = None
    council_role: str


class RequestItemOut(BaseModel):
    id: uuid.UUID
    asset_id: uuid.UUID | None = None
    name: str
    unit: str | None = None
    quantity: int
    unit_price: float | None = None
    manufacturer: str | None = None
    purpose: str | None = None
    remaining_value: float | None = None
    market_value: float | None = None
    proposed_value: float | None = None
    approved_sale_price: float | None = None
    condition_note: str | None = None

    model_config = {"from_attributes": True}


# Flat body covering all three request types (transfer/acquire/liquidate) —
# the endpoint validates which fields are required per `type`, matching the
# existing AssetCreate/AssetUpdate style rather than a discriminated union.
class RequestCreate(BaseModel):
    type: str
    requester_department: str | None = None
    scope: str | None = None
    to_holder_user_id: uuid.UUID | None = None
    from_department: str | None = None
    to_department: str | None = None
    from_location: str | None = None
    to_location: str | None = None
    to_contact_name: str | None = None
    to_contact_title: str | None = None
    to_contact_phone: str | None = None
    to_contact_email: str | None = None
    to_contact_id_card: str | None = None
    justification: str | None = None
    reason: str | None = None
    items: list[RequestItemCreate] = []


class RequestDecide(BaseModel):
    approve: bool
    note: str | None = None
    # Per-item approved sale price for liquidate requests — ignored by
    # transfer/acquire.
    items: list[RequestItemDecision] = []


class RequestDeleteRequest(BaseModel):
    ids: list[uuid.UUID]


class RequestDeleteResult(BaseModel):
    deleted: int


class RequestSignatureOut(BaseModel):
    id: uuid.UUID
    actor_id: uuid.UUID
    role_in_flow: str
    signed_name: str
    signature_image_url: str | None = None
    signed_at: datetime

    model_config = {"from_attributes": True}


class RequestListItem(BaseModel):
    id: uuid.UUID
    type: str
    status: str
    requester_id: uuid.UUID
    requester_name: str | None = None
    approver_role: str
    created_at: datetime

    model_config = {"from_attributes": True}


class RequestOut(RequestListItem):
    requester_department: str | None = None
    scope: str | None = None
    from_holder_user_id: uuid.UUID | None = None
    to_holder_user_id: uuid.UUID | None = None
    from_department: str | None = None
    to_department: str | None = None
    from_location: str | None = None
    to_location: str | None = None
    to_contact_name: str | None = None
    to_contact_title: str | None = None
    to_contact_phone: str | None = None
    to_contact_email: str | None = None
    to_contact_id_card: str | None = None
    justification: str | None = None
    reason: str | None = None
    decided_by_id: uuid.UUID | None = None
    decided_at: datetime | None = None
    decision_note: str | None = None
    generated_document_id: uuid.UUID | None = None
    updated_at: datetime
    items: list[RequestItemOut] = []
    council: list[CouncilSnapshotMember] = []
    signatures: list[RequestSignatureOut] = []
