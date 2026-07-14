from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("")
def get_public_settings():
    # Public, unauthenticated — the login page needs this before a session exists.
    return {
        "site_name": "DPG Asset Management",
        "google_client_id": settings.GOOGLE_CLIENT_ID,
        "google_allowed_domain": settings.GOOGLE_ALLOWED_DOMAIN,
    }
