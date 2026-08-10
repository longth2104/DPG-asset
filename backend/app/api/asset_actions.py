from datetime import datetime, timezone

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_scope_company_path, require_admin
from app.api.requests import _apply_effect, _build_request, _items_for, _to_out
from app.core.database import get_db
from app.models.user import User
from app.schemas.request import RequestCreate, RequestOut

# Admin shortcut: perform a transfer/acquire/liquidate immediately, with no
# pending-approval step — for correcting the registry or recording something
# that already happened outside the app, rather than routing it through the
# normal request/approve flow. Reuses the same Request/RequestItem model and
# _apply_effect as app/api/requests.py, just tagged origin="direct" and
# already decided, so it stays visible in the archive/PDF/dossier exactly
# like any other request — the request page/flow itself is untouched.
router = APIRouter(prefix="/api/asset-actions", tags=["asset-actions"])


@router.post("", response_model=RequestOut, status_code=status.HTTP_201_CREATED)
async def create_asset_action(
    body: RequestCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
    company_path: str | None = Depends(get_scope_company_path),
):
    req = await _build_request(db, body, admin, company_path)
    items = await _items_for(db, req.id)

    req.origin = "direct"
    req.status = "approved"
    req.decided_by_id = admin.id
    req.decided_at = datetime.now(timezone.utc)
    await _apply_effect(db, req, items, admin)

    await db.commit()
    await db.refresh(req)
    items = await _items_for(db, req.id)
    return _to_out(req, items, [])
