import uuid
from datetime import date, datetime

from pydantic import BaseModel

from app.schemas.document import DocumentOut


class AssetCreate(BaseModel):
    name: str
    category: str | None = None
    spec: str | None = None
    serial_number: str | None = None
    manufacturer: str | None = None
    manufacture_year: int | None = None
    year_put_in_use: date | None = None
    original_cost: float | None = None
    warranty_months: int | None = None
    legal_entity: str = "Đạt Phương"
    department: str | None = None
    holder: str | None = None
    location: str | None = None
    status: str = "dang_su_dung"
    domain: str = "b"
    budget_plan_year: int | None = None
    budget_actual_year: int | None = None
    replacement_priority: str | None = None
    purchase_source: str | None = None
    notes: str | None = None
    asset_code: str | None = None


class AssetUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    spec: str | None = None
    serial_number: str | None = None
    manufacturer: str | None = None
    manufacture_year: int | None = None
    year_put_in_use: date | None = None
    original_cost: float | None = None
    warranty_months: int | None = None
    legal_entity: str | None = None
    department: str | None = None
    holder: str | None = None
    location: str | None = None
    status: str | None = None
    domain: str | None = None
    budget_plan_year: int | None = None
    budget_actual_year: int | None = None
    replacement_priority: str | None = None
    purchase_source: str | None = None
    notes: str | None = None
    asset_code: str | None = None


class AssetListItem(BaseModel):
    id: uuid.UUID
    asset_code: str | None = None
    name: str
    category: str | None = None
    department: str | None = None
    holder: str | None = None
    location: str | None = None
    status: str
    domain: str

    model_config = {"from_attributes": True}


class AssetEventOut(BaseModel):
    id: uuid.UUID
    type: str
    actor_id: uuid.UUID | None = None
    note: str | None = None
    timestamp: datetime

    model_config = {"from_attributes": True}


class AssetEventCreate(BaseModel):
    note: str


class AssetExportRequest(BaseModel):
    format: str  # "xlsx" | "pdf"
    ids: list[uuid.UUID] | None = None
    department: str | None = None
    category: str | None = None
    status: str | None = None
    location: str | None = None
    search: str | None = None


class AssetImportResult(BaseModel):
    imported: int
    skipped: int
    errors: list[dict] = []


class AssetDeleteRequest(BaseModel):
    ids: list[uuid.UUID]


class AssetDeleteResult(BaseModel):
    deleted: int


class AssetSyncResult(BaseModel):
    created: int
    updated: int
    unmapped_companies: list[str] = []


class AssetOut(AssetListItem):
    spec: str | None = None
    serial_number: str | None = None
    manufacturer: str | None = None
    manufacture_year: int | None = None
    year_put_in_use: date | None = None
    original_cost: float | None = None
    warranty_months: int | None = None
    legal_entity: str
    budget_plan_year: int | None = None
    budget_actual_year: int | None = None
    replacement_priority: str | None = None
    purchase_source: str | None = None
    notes: str | None = None
    # Columns an Excel import found but couldn't match to a known field —
    # keyed by their raw header text (see services/excel.py). Read-only;
    # never set via AssetCreate/AssetUpdate.
    extra_fields: dict | None = None
    created_at: datetime
    updated_at: datetime
    events: list[AssetEventOut] = []
    documents: list[DocumentOut] = []
