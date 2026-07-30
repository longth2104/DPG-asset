import secrets

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_admin
from app.core.database import get_db
from app.core.security import hash_password
from app.models.company import Company
from app.models.user import ROLES, User
from app.schemas.request import UserBrief
from app.schemas.user import HrisEmployeeOut, UserAdminOut, UserCreate
from app.services.hris import company_code_from_dept_code, search_employees

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/lookup", response_model=UserBrief)
async def lookup_user(
    email: str = Query(...),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    # Resolves a recipient by email for the transfer-request form's "to"
    # picker — there's no full user directory/search endpoint yet, and this
    # increment doesn't need one.
    result = await db.execute(
        select(User).where(User.email == email, User.is_active.is_(True))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No user with that email")
    return user


@router.get("/hris-search", response_model=list[HrisEmployeeOut])
async def hris_search(
    q: str | None = Query(None),
    _: User = Depends(get_current_user),
):
    """Proxies the HRIS employee directory so the API key never reaches the
    frontend. Used by the admin add-user form's "search HRIS" step, and by
    the request form's recipient/department pickers — any signed-in user
    may look up the internal directory, same as the admin view."""
    try:
        employees = await search_employees(q)
    except RuntimeError as e:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(e))
    except httpx.HTTPError as e:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"HRIS request failed: {e}")

    return [
        HrisEmployeeOut(
            emp_code=e.get("emp_code"),
            name=e.get("name"),
            email=e.get("email"),
            dept_code=e.get("dept_code"),
            dept_name=e.get("dept_name"),
            job_title=e.get("job_title"),
            phone=e.get("phone"),
            suggested_company_code=company_code_from_dept_code(e.get("dept_code")),
        )
        for e in employees
    ]


@router.get("", response_model=list[UserAdminOut])
async def list_users(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    result = await db.execute(select(User).order_by(User.email))
    return result.scalars().all()


@router.post("", response_model=UserAdminOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Manually adds a user (typically after an HRIS lookup) — this app is
    access-by-invitation only, so this is the only way an account comes
    into existence besides the one-shot seed_admin script."""
    if body.role not in ROLES:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Unknown role")

    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status.HTTP_409_CONFLICT, "A user with that email already exists")

    if body.hris_emp_code:
        existing_emp = await db.execute(
            select(User).where(User.hris_emp_code == body.hris_emp_code)
        )
        if existing_emp.scalar_one_or_none():
            raise HTTPException(
                status.HTTP_409_CONFLICT, "That HRIS employee has already been added"
            )

    company = await db.get(Company, body.company_id)
    if not company:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Company not found")

    user = User(
        email=body.email,
        full_name=body.full_name,
        # Random, unusable password — this account is meant to sign in via
        # Google SSO; an admin can set a real password later if needed.
        password_hash=hash_password(secrets.token_urlsafe(32)),
        role=body.role,
        company_id=body.company_id,
        hris_emp_code=body.hris_emp_code,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
