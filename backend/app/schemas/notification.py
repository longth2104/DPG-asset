import uuid
from datetime import datetime

from pydantic import BaseModel


class NotificationOut(BaseModel):
    id: uuid.UUID
    type: str
    request_id: uuid.UUID
    request_type: str
    request_status: str
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UnreadCountOut(BaseModel):
    count: int
