import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.document import DocumentOut


class AssetMaintenanceRecordCreate(BaseModel):
    location: str | None = None
    cost: float | None = None
    condition_note: str | None = None


class AssetMaintenanceRecordUpdate(BaseModel):
    status: str | None = None
    location: str | None = None
    cost: float | None = None
    condition_note: str | None = None
    # Sending true marks it resolved now — see api/assets.py.
    resolve: bool = False


class AssetMaintenanceRecordOut(BaseModel):
    id: uuid.UUID
    asset_id: uuid.UUID
    status: str
    reported_at: datetime
    resolved_at: datetime | None = None
    location: str | None = None
    cost: float | None = None
    condition_note: str | None = None
    created_by: uuid.UUID | None = None
    created_at: datetime
    documents: list[DocumentOut] = []

    model_config = {"from_attributes": True}
