import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_eoffice_key
from app.api.requests import _apply_effect, _items_for, _to_out
from app.core.database import get_db
from app.models.asset import Asset
from app.models.company import Company
from app.models.council import CouncilMember
from app.models.request import APPROVER_ROLE_BY_TYPE, Request, RequestItem
from app.models.user import User
from app.schemas.eoffice import EofficeAssetOut, EofficeAssignmentIn, EofficeRequestIn
from app.schemas.request import RequestOut
from app.services.user_provisioning import find_or_create_user_by_email

# Inbound integration: datphuong.vn calls into AMS, key-authenticated rather
# than user-session-authenticated — see require_eoffice_key. Deliberately
# unscoped by company (the key itself is the trust boundary, since e-office
# is the cross-company authority for personal assignment/purchase/liquidation
# per docs/e-office.md), unlike every user-facing endpoint elsewhere in this
# app which is scoped by the caller's company.
router = APIRouter(prefix="/api/eoffice", tags=["eoffice"], dependencies=[Depends(require_eoffice_key)])


async def _existing_by_ref(db: AsyncSession, external_ref: str | None) -> Request | None:
    if not external_ref:
        return None
    result = await db.execute(select(Request).where(Request.external_ref == external_ref))
    return result.scalar_one_or_none()


@router.get("/assets", response_model=list[EofficeAssetOut])
async def list_assets_for_eoffice(
    limit: int = Query(1000, le=5000),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Asset).order_by(Asset.asset_code).limit(limit).offset(offset))
    assets = result.scalars().all()

    holder_ids = {a.holder_user_id for a in assets if a.holder_user_id}
    users_by_id: dict = {}
    if holder_ids:
        result = await db.execute(select(User).where(User.id.in_(holder_ids)))
        users_by_id = {u.id: u for u in result.scalars().all()}

    company_ids = {a.company_id for a in assets if a.company_id}
    companies_by_id: dict = {}
    if company_ids:
        result = await db.execute(select(Company).where(Company.id.in_(company_ids)))
        companies_by_id = {c.id: c for c in result.scalars().all()}

    out = []
    for a in assets:
        holder = users_by_id.get(a.holder_user_id) if a.holder_user_id else None
        company = companies_by_id.get(a.company_id) if a.company_id else None
        out.append(
            EofficeAssetOut(
                id=a.id,
                asset_code=a.asset_code,
                name=a.name,
                department=a.department,
                location=a.location,
                status=a.status,
                company_code=company.code if company else None,
                holder_email=holder.email if holder else None,
                holder_name=holder.full_name if holder else None,
            )
        )
    return out


@router.post("/assignments", response_model=RequestOut, status_code=status.HTTP_201_CREATED)
async def report_assignment(
    body: EofficeAssignmentIn,
    db: AsyncSession = Depends(get_db),
):
    """Reports a personal asset assignment decided on datphuong.vn — the
    same effect as an in-app transfer request, already completed."""
    existing = await _existing_by_ref(db, body.external_ref)
    if existing:
        items = await _items_for(db, existing.id)
        return _to_out(existing, items, [])

    asset_result = await db.execute(select(Asset).where(Asset.asset_code == body.asset_code))
    asset = asset_result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"No asset with code {body.asset_code}")

    holder = await find_or_create_user_by_email(db, body.holder_email)
    if not holder:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, f"No account or HRIS match for {body.holder_email}"
        )
    actor = await find_or_create_user_by_email(db, body.actor_email)
    if not actor:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, f"No account or HRIS match for {body.actor_email}"
        )

    req = Request(
        type="transfer",
        requester_id=actor.id,
        scope="individual",
        to_holder_user_id=holder.id,
        from_holder_user_id=asset.holder_user_id,
        from_department=asset.department,
        from_location=asset.location,
        to_department=body.department,
        to_location=body.location,
        approver_role=APPROVER_ROLE_BY_TYPE["transfer"],
        origin="eoffice",
        external_ref=body.external_ref,
        decided_by_id=actor.id,
        decided_at=datetime.now(timezone.utc),
        decision_note=body.note,
    )
    db.add(req)
    await db.flush()

    item = RequestItem(request_id=req.id, asset_id=asset.id, name=asset.name)
    db.add(item)
    await db.flush()

    await _apply_effect(db, req, [item], actor)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raced = await _existing_by_ref(db, body.external_ref)
        if raced:
            items = await _items_for(db, raced.id)
            return _to_out(raced, items, [])
        raise

    await db.refresh(req)
    items = await _items_for(db, req.id)
    return _to_out(req, items, [])


@router.post("/requests", response_model=RequestOut, status_code=status.HTTP_201_CREATED)
async def report_request(
    body: EofficeRequestIn,
    db: AsyncSession = Depends(get_db),
):
    """Reports a completed acquire/liquidate action decided on datphuong.vn.
    Transfers go through /assignments instead — see there."""
    if body.type not in ("acquire", "liquidate"):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "type must be 'acquire' or 'liquidate' — use /assignments for transfers",
        )
    if body.decision not in ("approved", "rejected"):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "decision must be 'approved' or 'rejected'")
    if not body.items:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "At least one item is required")

    existing = await _existing_by_ref(db, body.external_ref)
    if existing:
        items = await _items_for(db, existing.id)
        return _to_out(existing, items, [])

    requester = await find_or_create_user_by_email(db, body.requester_email)
    if not requester:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, f"No account or HRIS match for {body.requester_email}"
        )
    decided_by = await find_or_create_user_by_email(db, body.decided_by_email)
    if not decided_by:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, f"No account or HRIS match for {body.decided_by_email}"
        )

    assets_by_code: dict[str, Asset] = {}
    if body.type == "liquidate":
        codes = [i.asset_code for i in body.items]
        if any(c is None for c in codes):
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Each liquidate item needs asset_code")
        result = await db.execute(select(Asset).where(Asset.asset_code.in_(codes)))
        assets_by_code = {a.asset_code: a for a in result.scalars().all()}
        missing = set(codes) - set(assets_by_code.keys())
        if missing:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, f"Unknown asset code(s): {', '.join(sorted(missing))}"
            )
    else:
        for i in body.items:
            if not i.name:
                raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Each acquire item needs a name")

    council_snapshot = None
    if body.type == "liquidate":
        result = await db.execute(
            select(CouncilMember)
            .where(CouncilMember.is_active.is_(True))
            .order_by(CouncilMember.council_role, CouncilMember.full_name)
        )
        council_snapshot = json.dumps(
            [
                {"full_name": m.full_name, "position": m.position, "council_role": m.council_role}
                for m in result.scalars().all()
            ]
        )

    req = Request(
        type=body.type,
        requester_id=requester.id,
        to_department=body.to_department,
        justification=body.justification,
        reason=body.reason,
        council_snapshot=council_snapshot,
        approver_role=APPROVER_ROLE_BY_TYPE[body.type],
        origin="eoffice",
        external_ref=body.external_ref,
        decided_by_id=decided_by.id,
        decided_at=datetime.now(timezone.utc),
        decision_note=body.note,
    )
    db.add(req)
    await db.flush()

    items = []
    for item_in in body.items:
        asset = assets_by_code.get(item_in.asset_code) if item_in.asset_code else None
        item = RequestItem(
            request_id=req.id,
            asset_id=asset.id if asset else None,
            name=item_in.name or (asset.name if asset else "—"),
            unit=item_in.unit,
            quantity=item_in.quantity or 1,
            unit_price=item_in.unit_price,
            manufacturer=item_in.manufacturer,
            purpose=item_in.purpose,
            remaining_value=item_in.remaining_value,
            market_value=item_in.market_value,
            proposed_value=item_in.proposed_value,
            approved_sale_price=item_in.approved_sale_price,
            condition_note=item_in.condition_note,
        )
        db.add(item)
        items.append(item)
    await db.flush()

    if body.decision == "approved":
        await _apply_effect(db, req, items, decided_by)
    else:
        req.status = "rejected"

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raced = await _existing_by_ref(db, body.external_ref)
        if raced:
            items = await _items_for(db, raced.id)
            return _to_out(raced, items, [])
        raise

    await db.refresh(req)
    items = await _items_for(db, req.id)
    return _to_out(req, items, [])
