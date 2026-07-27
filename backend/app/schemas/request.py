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


# Flat body covering all three request types (transfer/acquire/liquidate) —
# the endpoint validates which fields are required per `type`, matching the
# existing AssetCreate/AssetUpdate style rather than a discriminated union.
class RequestCreate(BaseModel):
    type: str
    asset_id: uuid.UUID | None = None
    scope: str | None = None
    to_holder_user_id: uuid.UUID | None = None
    from_department: str | None = None
    to_department: str | None = None
    from_location: str | None = None
    to_location: str | None = None
    justification: str | None = None
    estimated_cost: float | None = None
    reason: str | None = None
    condition_note: str | None = None


class RequestDecide(BaseModel):
    approve: bool
    note: str | None = None


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
    asset_id: uuid.UUID | None = None
    approver_role: str
    created_at: datetime

    model_config = {"from_attributes": True}


class RequestOut(RequestListItem):
    scope: str | None = None
    from_holder_user_id: uuid.UUID | None = None
    to_holder_user_id: uuid.UUID | None = None
    from_department: str | None = None
    to_department: str | None = None
    from_location: str | None = None
    to_location: str | None = None
    justification: str | None = None
    estimated_cost: float | None = None
    reason: str | None = None
    condition_note: str | None = None
    decided_by_id: uuid.UUID | None = None
    decided_at: datetime | None = None
    decision_note: str | None = None
    generated_document_id: uuid.UUID | None = None
    updated_at: datetime
    signatures: list[RequestSignatureOut] = []
