from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.request import UserBrief

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
