import httpx

from app.core.config import settings


async def search_employees(query: str | None = None) -> list[dict]:
    """Fetches the HRIS employee directory. The API returns the whole
    directory in one call (no documented server-side search param), so
    filtering by name/email/emp_code happens here instead."""
    if not settings.HRIS_BASE_URL or not settings.HRIS_API_KEY:
        raise RuntimeError("HRIS is not configured")

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{settings.HRIS_BASE_URL}{settings.HRIS_EMPLOYEES_PATH}",
            headers={"Authorization": f"Bearer {settings.HRIS_API_KEY}"},
        )
    resp.raise_for_status()
    employees = resp.json().get("data", [])

    if query:
        q = query.strip().lower()
        employees = [
            e
            for e in employees
            if q in (e.get("name") or "").lower()
            or q in (e.get("email") or "").lower()
            or q in (e.get("emp_code") or "").lower()
        ]
    return employees


def company_code_from_dept_code(dept_code: str | None) -> str | None:
    """HRIS encodes the legal entity as the prefix of dept_code, e.g.
    "DPG-BTB" -> "DPG"."""
    if not dept_code or "-" not in dept_code:
        return None
    return dept_code.split("-", 1)[0]
