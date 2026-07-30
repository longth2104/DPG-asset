import uuid
from datetime import datetime

from pydantic import BaseModel


class CouncilMemberCreate(BaseModel):
    full_name: str
    position: str | None = None
    council_role: str = "thanh_vien"


class CouncilMemberUpdate(BaseModel):
    full_name: str | None = None
    position: str | None = None
    council_role: str | None = None
    is_active: bool | None = None


class CouncilMemberOut(BaseModel):
    id: uuid.UUID
    full_name: str
    position: str | None = None
    council_role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
