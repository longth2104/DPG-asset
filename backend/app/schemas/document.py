import uuid
from datetime import datetime

from pydantic import BaseModel


class DocumentOut(BaseModel):
    id: uuid.UUID
    filename: str
    file_url: str
    content_type: str | None = None
    size_bytes: int
    created_at: datetime

    model_config = {"from_attributes": True}
