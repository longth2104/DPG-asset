import uuid
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_redis
from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import (
    GoogleLoginRequest,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    TokenResponse,
    UserOut,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _tokens_for(user: User) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    if not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Account is disabled")
    return _tokens_for(user)


@router.post("/google", response_model=TokenResponse)
async def google_login(body: GoogleLoginRequest, db: AsyncSession = Depends(get_db)):
    client_id = settings.GOOGLE_CLIENT_ID
    if not client_id:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Google SSO is not configured")

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            "https://oauth2.googleapis.com/tokeninfo", params={"id_token": body.credential}
        )
    if resp.status_code != 200:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid Google credential")

    info = resp.json()
    if info.get("aud") != client_id:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid Google credential")
    if str(info.get("email_verified")).lower() != "true":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Google email not verified")

    email = info.get("email", "")
    allowed_domain = settings.GOOGLE_ALLOWED_DOMAIN
    if allowed_domain and not email.endswith(f"@{allowed_domain}"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Email domain not allowed")

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        # This app is access-by-invitation only — an admin must add the
        # user (via HRIS lookup) before they can sign in at all, Google
        # or otherwise. No auto-provisioning on first login.
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Your account hasn't been added yet — contact an administrator",
        )

    if not user.google_sub:
        user.google_sub = info.get("sub")
        await db.commit()

    if not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Account is disabled")

    return _tokens_for(user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    payload = decode_token(body.refresh_token)
    invalid = HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired refresh token")
    if not payload or payload.get("type") != "refresh":
        raise invalid

    try:
        user_id = uuid.UUID(payload.get("sub"))
    except (TypeError, ValueError):
        raise invalid

    user = await db.get(User, user_id)
    if not user or not user.is_active:
        raise invalid

    return _tokens_for(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(body: LogoutRequest, redis=Depends(get_redis)):
    payload = decode_token(body.refresh_token)
    if not payload:
        return  # silently accept invalid tokens — server may already have revoked them

    exp = payload.get("exp")
    ttl = int(exp - datetime.now(timezone.utc).timestamp()) if exp else 0
    if ttl > 0:
        await redis.setex(f"blocklist:{body.refresh_token}", ttl, "1")


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    return user
