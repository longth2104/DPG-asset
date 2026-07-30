import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str | None = None
    role: str
    company_id: uuid.UUID
    hris_emp_code: str | None = None


class UserUpdate(BaseModel):
    role: str | None = None
    # "Removing" a user deactivates their account (blocks login, matching
    # the is_active check already enforced in get_current_user) rather than
    # deleting the row — several tables (requests, request_signatures,
    # documents) cascade-delete on users.id, so a hard delete would silently
    # wipe their request/signature/upload history along with the account.
    is_active: bool | None = None


class UserAdminOut(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str | None = None
    role: str
    company_id: uuid.UUID | None = None
    hris_emp_code: str | None = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class HrisEmployeeOut(BaseModel):
    emp_code: str | None = None
    name: str | None = None
    email: str | None = None
    dept_code: str | None = None
    dept_name: str | None = None
    job_title: str | None = None
    phone: str | None = None
    # Derived from dept_code's prefix — the add-user form pre-selects this
    # company, but the admin can still override it.
    suggested_company_code: str | None = None
