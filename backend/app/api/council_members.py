import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.core.database import get_db
from app.models.council import CouncilMember
from app.models.user import User
from app.schemas.council import CouncilMemberCreate, CouncilMemberOut, CouncilMemberUpdate

router = APIRouter(prefix="/api/council-members", tags=["council-members"])


@router.get("", response_model=list[CouncilMemberOut])
async def list_council_members(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    result = await db.execute(
        select(CouncilMember).order_by(CouncilMember.council_role, CouncilMember.full_name)
    )
    return result.scalars().all()


@router.post("", response_model=CouncilMemberOut, status_code=status.HTTP_201_CREATED)
async def create_council_member(
    body: CouncilMemberCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    member = CouncilMember(**body.model_dump())
    db.add(member)
    await db.commit()
    await db.refresh(member)
    return member


@router.put("/{member_id}", response_model=CouncilMemberOut)
async def update_council_member(
    member_id: uuid.UUID,
    body: CouncilMemberUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    member = await db.get(CouncilMember, member_id)
    if not member:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Council member not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(member, field, value)
    await db.commit()
    await db.refresh(member)
    return member
