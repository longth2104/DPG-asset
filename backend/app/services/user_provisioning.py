import secrets
import unicodedata

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.company import Company
from app.models.user import User
from app.services.hris import company_code_from_dept_code, search_employees


async def find_or_create_user_by_email(db: AsyncSession, email: str) -> User | None:
    """Resolves an email to a local User, auto-provisioning one from the HRIS
    directory if it matches an employee with no AMS account yet — the same
    single-click "add from HRIS" the admin Users page already does, just
    triggered automatically for the e-office integration instead of by an
    admin's click. Returns None if the email matches neither a local account
    nor an HRIS employee (never guesses a company for an unverified email)."""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user:
        return user

    try:
        employees = await search_employees(email)
    except (RuntimeError, httpx.HTTPError):
        return None

    match = next((e for e in employees if (e.get("email") or "").strip().lower() == email.strip().lower()), None)
    if not match:
        return None

    if match.get("emp_code"):
        # Same HRIS employee might already have a local account under a
        # slightly different email — avoid both a duplicate account and the
        # hris_emp_code unique-constraint violation that would follow.
        result = await db.execute(select(User).where(User.hris_emp_code == match["emp_code"]))
        existing_by_emp_code = result.scalar_one_or_none()
        if existing_by_emp_code:
            return existing_by_emp_code

    company_code = company_code_from_dept_code(match.get("dept_code"))
    company = None
    if company_code:
        result = await db.execute(select(Company).where(Company.code == company_code))
        company = result.scalar_one_or_none()
    if not company:
        return None

    user = User(
        email=match.get("email") or email,
        full_name=match.get("name"),
        # Random, unusable password — same rationale as the admin add-user
        # flow: this account signs in via Google SSO, not a set password.
        password_hash=hash_password(secrets.token_urlsafe(32)),
        role="cbnv",
        company_id=company.id,
        hris_emp_code=match.get("emp_code"),
    )
    db.add(user)
    await db.flush()
    return user


def _normalize_name(name: str | None) -> str:
    """Comparison key that's tolerant of stray whitespace and NFC/NFD
    Unicode-encoding differences in Vietnamese text (the same accented name
    typed in two files can decompose differently) — but doesn't strip
    diacritics themselves, since those still distinguish different names."""
    return " ".join(unicodedata.normalize("NFC", name or "").strip().lower().split())


async def find_user_by_name(db: AsyncSession, name: str, directory: list[dict]) -> User | None:
    """Resolves a plain holder name (e.g. an Excel column with no email, just
    "Người sử dụng") against an already-fetched HRIS directory — only when
    the name matches exactly one employee. Vietnamese full names collide
    often enough that resolving an ambiguous match would risk linking the
    asset to the wrong person, so this never guesses: 0 or >1 matches both
    return None and the holder stays a free-text label, same as before."""
    key = _normalize_name(name)
    if not key:
        return None
    matches = [e for e in directory if _normalize_name(e.get("name")) == key]
    if len(matches) != 1:
        return None
    email = matches[0].get("email")
    if not email:
        return None
    return await find_or_create_user_by_email(db, email)
