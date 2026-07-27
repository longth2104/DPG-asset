import uuid

import redis.asyncio as aioredis
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

ASSET_MANAGER_ROLES = ("phong_thiet_bi", "hcns_truong_phong", "lanh_dao_noi_chinh", "tgd", "admin")


async def get_redis():
    client = aioredis.from_url(settings.REDIS_URL)
    try:
        yield client
    finally:
        await client.close()


async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> User:
    invalid = HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")
    if not token:
        raise invalid

    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise invalid

    if await redis.get(f"blocklist:{token}"):
        raise invalid

    try:
        user_id = uuid.UUID(payload.get("sub"))
    except (TypeError, ValueError):
        raise invalid

    user = await db.get(User, user_id)
    if not user or not user.is_active:
        raise invalid

    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin role required")
    return user


def require_asset_manager(user: User = Depends(get_current_user)) -> User:
    if user.role not in ASSET_MANAGER_ROLES:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not permitted to manage assets")
    return user


def require_role(*roles: str):
    """Factory for a role-gated dependency — `admin` always passes, matching
    the escalation path every other role check in this module already gives
    the admin role implicitly via ASSET_MANAGER_ROLES."""

    def _check(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles and user.role != "admin":
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Not permitted to perform this action")
        return user

    return _check
