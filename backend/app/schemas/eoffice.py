import uuid

from pydantic import BaseModel


class EofficeAssetOut(BaseModel):
    id: uuid.UUID
    asset_code: str | None = None
    name: str
    department: str | None = None
    location: str | None = None
    status: str
    company_code: str | None = None
    holder_email: str | None = None
    holder_name: str | None = None


class EofficeAssignmentIn(BaseModel):
    asset_code: str
    holder_email: str
    department: str | None = None
    location: str | None = None
    actor_email: str
    note: str | None = None
    external_ref: str | None = None


class EofficeRequestItemIn(BaseModel):
    # acquire
    name: str | None = None
    unit: str | None = None
    quantity: int = 1
    unit_price: float | None = None
    manufacturer: str | None = None
    purpose: str | None = None
    # liquidate
    asset_code: str | None = None
    remaining_value: float | None = None
    market_value: float | None = None
    proposed_value: float | None = None
    approved_sale_price: float | None = None
    condition_note: str | None = None


class EofficeRequestIn(BaseModel):
    type: str  # "acquire" | "liquidate"
    requester_email: str
    decided_by_email: str
    decision: str  # "approved" | "rejected"
    note: str | None = None
    external_ref: str | None = None
    to_department: str | None = None
    justification: str | None = None
    reason: str | None = None
    items: list[EofficeRequestItemIn] = []
