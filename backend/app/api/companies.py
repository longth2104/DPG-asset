import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_admin
from app.core.database import get_db
from app.models.company import Company
from app.models.user import User
from app.schemas.company import CompanyCreate, CompanyOut, CompanyUpdate

router = APIRouter(prefix="/api/companies", tags=["companies"])


async def _recompute_subtree_paths(db: AsyncSession, company: Company) -> None:
    """Recomputes `path` for `company` and all of its descendants after a
    reparent. Walks the whole table rather than a recursive CTE — this is an
    admin-only, rare operation, not a hot path worth optimizing."""
    all_companies = (await db.execute(select(Company))).scalars().all()
    children_by_parent: dict[uuid.UUID | None, list[Company]] = {}
    for c in all_companies:
        children_by_parent.setdefault(c.parent_id, []).append(c)

    def set_path(node: Company, parent_path: str | None) -> None:
        node.path = f"{parent_path}/{node.id}" if parent_path else str(node.id)
        for child in children_by_parent.get(node.id, []):
            set_path(child, node.path)

    parent_path = None
    if company.parent_id:
        parent = next(c for c in all_companies if c.id == company.parent_id)
        parent_path = parent.path
    set_path(company, parent_path)


@router.get("", response_model=list[CompanyOut])
async def list_companies(
    db: AsyncSession = Depends(get_db),
    # Read-only company directory (code/name/hierarchy) — any signed-in user
    # needs this to populate the request form's company/department pickers.
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(Company).order_by(Company.code))
    return result.scalars().all()


@router.post("", response_model=CompanyOut, status_code=status.HTTP_201_CREATED)
async def create_company(
    body: CompanyCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    parent = await db.get(Company, body.parent_id) if body.parent_id else None
    if body.parent_id and not parent:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Parent company not found")

    existing = await db.execute(select(Company).where(Company.code == body.code))
    if existing.scalar_one_or_none():
        raise HTTPException(status.HTTP_409_CONFLICT, "A company with that code already exists")

    company = Company(code=body.code, name=body.name, parent_id=body.parent_id, path="")
    db.add(company)
    await db.flush()
    company.path = f"{parent.path}/{company.id}" if parent else str(company.id)
    await db.commit()
    await db.refresh(company)
    return company


@router.put("/{company_id}", response_model=CompanyOut)
async def update_company(
    company_id: uuid.UUID,
    body: CompanyUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    company = await db.get(Company, company_id)
    if not company:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Company not found")

    changes = body.model_dump(exclude_unset=True)
    reparented = "parent_id" in changes and changes["parent_id"] != company.parent_id

    if reparented and changes["parent_id"] is not None:
        if changes["parent_id"] == company.id:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "A company cannot be its own parent")
        new_parent = await db.get(Company, changes["parent_id"])
        if not new_parent:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Parent company not found")
        if new_parent.path.startswith(company.path):
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "Cannot reparent a company under its own descendant",
            )

    for field, value in changes.items():
        setattr(company, field, value)

    if reparented:
        await _recompute_subtree_paths(db, company)

    await db.commit()
    await db.refresh(company)
    return company
