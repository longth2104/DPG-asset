import uuid
from datetime import datetime

from pydantic import BaseModel


class CompanyCreate(BaseModel):
    code: str
    name: str
    parent_id: uuid.UUID | None = None


class CompanyUpdate(BaseModel):
    name: str | None = None
    parent_id: uuid.UUID | None = None
    grants_global_access: bool | None = None


class CompanyOut(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    parent_id: uuid.UUID | None = None
    path: str
    grants_global_access: bool
    created_at: datetime

    model_config = {"from_attributes": True}
