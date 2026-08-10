import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import Response
from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    ASSET_MANAGER_ROLES,
    get_current_user,
    get_scope_company_path,
    require_admin,
)
from app.api.upload import MAX_UPLOAD_BYTES, store_object
from app.core.database import get_db
from app.models.asset import Asset
from app.models.asset_event import AssetEvent
from app.models.company import Company
from app.models.council import CouncilMember
from app.models.notification import Notification
from app.models.request import (
    APPROVER_ROLE_BY_TYPE,
    REQUEST_SCOPES,
    REQUEST_TYPES,
    Request,
    RequestItem,
    RequestSignature,
)
from app.models.user import User
from app.schemas.request import (
    RequestCreate,
    RequestDecide,
    RequestDeleteRequest,
    RequestDeleteResult,
    RequestItemOut,
    RequestListItem,
    RequestOut,
    RequestSignatureOut,
)
from app.services.pdf import content_hash_for, render_request_pdf

router = APIRouter(prefix="/api/requests", tags=["requests"])


async def _get_request_or_404(db: AsyncSession, request_id: uuid.UUID) -> Request:
    req = await db.get(Request, request_id)
    if not req:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Request not found")
    return req


async def _get_assets_or_404(
    db: AsyncSession, asset_ids: list[uuid.UUID], company_path: str | None
) -> dict[uuid.UUID, Asset]:
    """Batch-fetches assets by id, 404ing if any are missing or (when scoped)
    outside the caller's company subtree."""
    if not asset_ids:
        return {}
    result = await db.execute(select(Asset).where(Asset.id.in_(asset_ids)))
    assets = {a.id: a for a in result.scalars().all()}
    if set(asset_ids) - set(assets.keys()):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Asset not found")

    if company_path is not None:
        company_ids = {a.company_id for a in assets.values() if a.company_id}
        companies = {}
        if company_ids:
            result = await db.execute(select(Company).where(Company.id.in_(company_ids)))
            companies = {c.id: c for c in result.scalars().all()}
        for asset in assets.values():
            company = companies.get(asset.company_id) if asset.company_id else None
            if not company or not company.path.startswith(company_path):
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Asset not found")
    return assets


async def _items_for(db: AsyncSession, request_id: uuid.UUID) -> list[RequestItem]:
    result = await db.execute(
        select(RequestItem).where(RequestItem.request_id == request_id).order_by(RequestItem.created_at)
    )
    return result.scalars().all()


async def _signatures_for(db: AsyncSession, request_id: uuid.UUID) -> list[RequestSignature]:
    result = await db.execute(
        select(RequestSignature)
        .where(RequestSignature.request_id == request_id)
        .order_by(RequestSignature.signed_at)
    )
    return result.scalars().all()


def _request_scope_condition(company_path: str | None):
    """SQL condition for "is this request visible to someone scoped to
    company_path": an item-linked request (transfer/liquidate) needs at
    least one item's asset in scope; an acquire request (no assets yet)
    needs the requester's own company in scope. Returns None when
    unrestricted."""
    if company_path is None:
        return None
    in_scope_company_ids = select(Company.id).where(Company.path.startswith(company_path))
    asset_linked_in_scope = Request.id.in_(
        select(RequestItem.request_id)
        .join(Asset, RequestItem.asset_id == Asset.id)
        .where(Asset.company_id.in_(in_scope_company_ids))
    )
    requester_in_scope = (Request.type == "acquire") & Request.requester_id.in_(
        select(User.id).where(User.company_id.in_(in_scope_company_ids))
    )
    return or_(asset_linked_in_scope, requester_in_scope)


async def _request_in_company_scope(db: AsyncSession, req: Request, company_path: str) -> bool:
    """Whether `req` is visible to someone scoped to `company_path` — only
    meaningful when the caller already knows they're scoped (never call
    with company_path=None; that's the unrestricted case, always visible)."""
    if req.type == "acquire":
        requester = await db.get(User, req.requester_id)
        if not requester or not requester.company_id:
            return False
        company = await db.get(Company, requester.company_id)
        return bool(company and company.path.startswith(company_path))
    items = await _items_for(db, req.id)
    asset_ids = [i.asset_id for i in items if i.asset_id]
    if not asset_ids:
        return False
    result = await db.execute(select(Asset).where(Asset.id.in_(asset_ids)))
    company_ids = {a.company_id for a in result.scalars().all() if a.company_id}
    if not company_ids:
        return False
    result2 = await db.execute(select(Company).where(Company.id.in_(company_ids)))
    return any(c.path.startswith(company_path) for c in result2.scalars().all())


async def _assert_request_visible(
    db: AsyncSession, req: Request, user: User, company_path: str | None
) -> None:
    if user.id == req.requester_id or company_path is None:
        return
    if not await _request_in_company_scope(db, req, company_path):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Request not found")


async def _notify_pending_approvers(db: AsyncSession, req: Request) -> None:
    """One notification per approver-role user who can actually see this
    request — same company-scope rule as the "pending for me" list, so
    nobody gets alerted about a request they couldn't open anyway."""
    result = await db.execute(
        select(User).where(User.role == req.approver_role, User.is_active.is_(True))
    )
    for candidate in result.scalars().all():
        path = await get_scope_company_path(db=db, user=candidate)
        if path is None or await _request_in_company_scope(db, req, path):
            db.add(Notification(recipient_id=candidate.id, request_id=req.id, type="pending_approval"))


def _notify_requester_decided(db: AsyncSession, req: Request) -> None:
    db.add(Notification(recipient_id=req.requester_id, request_id=req.id, type="decided"))


def _item_to_out(item: RequestItem) -> RequestItemOut:
    return RequestItemOut(
        id=item.id,
        asset_id=item.asset_id,
        name=item.name,
        unit=item.unit,
        quantity=item.quantity,
        unit_price=float(item.unit_price) if item.unit_price is not None else None,
        manufacturer=item.manufacturer,
        purpose=item.purpose,
        remaining_value=float(item.remaining_value) if item.remaining_value is not None else None,
        market_value=float(item.market_value) if item.market_value is not None else None,
        proposed_value=float(item.proposed_value) if item.proposed_value is not None else None,
        approved_sale_price=(
            float(item.approved_sale_price) if item.approved_sale_price is not None else None
        ),
        condition_note=item.condition_note,
    )


def _to_out(req: Request, items: list[RequestItem], signatures: list[RequestSignature]) -> RequestOut:
    return RequestOut(
        **RequestListItem.model_validate(req).model_dump(),
        requester_department=req.requester_department,
        scope=req.scope,
        from_holder_user_id=req.from_holder_user_id,
        to_holder_user_id=req.to_holder_user_id,
        from_department=req.from_department,
        to_department=req.to_department,
        from_location=req.from_location,
        to_location=req.to_location,
        to_contact_name=req.to_contact_name,
        to_contact_title=req.to_contact_title,
        to_contact_phone=req.to_contact_phone,
        to_contact_email=req.to_contact_email,
        to_contact_id_card=req.to_contact_id_card,
        justification=req.justification,
        reason=req.reason,
        decided_by_id=req.decided_by_id,
        decided_at=req.decided_at,
        decision_note=req.decision_note,
        generated_document_id=req.generated_document_id,
        updated_at=req.updated_at,
        items=[_item_to_out(i) for i in items],
        council=json.loads(req.council_snapshot) if req.council_snapshot else [],
        signatures=[RequestSignatureOut.model_validate(s) for s in signatures],
    )


@router.post("", response_model=RequestOut, status_code=status.HTTP_201_CREATED)
async def create_request(
    body: RequestCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    company_path: str | None = Depends(get_scope_company_path),
):
    if body.type not in REQUEST_TYPES:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Unknown request type")
    if body.scope is not None and body.scope not in REQUEST_SCOPES:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Unknown scope")
    if not body.items:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "At least one item is required")

    assets_by_id: dict[uuid.UUID, Asset] = {}
    if body.type in ("transfer", "liquidate"):
        if any(item.asset_id is None for item in body.items):
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Each item needs an asset_id")
        assets_by_id = await _get_assets_or_404(db, [item.asset_id for item in body.items], company_path)
    else:  # acquire
        for item in body.items:
            if item.asset_id:
                raise HTTPException(
                    status.HTTP_422_UNPROCESSABLE_ENTITY, "acquire items have no existing asset"
                )
            if not item.name:
                raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Each item needs a name")

    # Snapshot the active liquidation council now, so the printed assessment
    # /accounting forms stay stable even if membership changes later.
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
        requester_id=user.id,
        requester_department=body.requester_department,
        scope=body.scope,
        to_holder_user_id=body.to_holder_user_id,
        from_department=body.from_department,
        to_department=body.to_department,
        from_location=body.from_location,
        to_location=body.to_location,
        to_contact_name=body.to_contact_name,
        to_contact_title=body.to_contact_title,
        to_contact_phone=body.to_contact_phone,
        to_contact_email=body.to_contact_email,
        to_contact_id_card=body.to_contact_id_card,
        justification=body.justification,
        reason=body.reason,
        council_snapshot=council_snapshot,
        approver_role=APPROVER_ROLE_BY_TYPE[body.type],
    )
    if body.type == "transfer" and assets_by_id:
        first_asset = assets_by_id[body.items[0].asset_id]
        req.from_holder_user_id = first_asset.holder_user_id
        req.from_department = req.from_department or first_asset.department
        req.from_location = req.from_location or first_asset.location

    db.add(req)
    await db.flush()

    for item_in in body.items:
        asset = assets_by_id.get(item_in.asset_id) if item_in.asset_id else None
        db.add(
            RequestItem(
                request_id=req.id,
                asset_id=item_in.asset_id,
                name=item_in.name or (asset.name if asset else "—"),
                unit=item_in.unit,
                quantity=item_in.quantity or 1,
                unit_price=item_in.unit_price,
                manufacturer=item_in.manufacturer,
                purpose=item_in.purpose,
                remaining_value=item_in.remaining_value,
                market_value=item_in.market_value,
                proposed_value=item_in.proposed_value,
                condition_note=item_in.condition_note,
            )
        )

    for asset in assets_by_id.values():
        db.add(
            AssetEvent(
                asset_id=asset.id,
                actor_id=user.id,
                type="note",
                note=f"Yêu cầu {body.type} được tạo (mã yêu cầu {req.id})",
            )
        )

    await _notify_pending_approvers(db, req)

    await db.commit()
    await db.refresh(req)
    items = await _items_for(db, req.id)
    return _to_out(req, items, [])


@router.get("", response_model=list[RequestListItem])
async def list_requests(
    mine: bool = Query(False),
    pending_for_me: bool = Query(False),
    all_requests: bool = Query(False, alias="all"),
    type_: str | None = Query(None, alias="type"),
    status_: str | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    company_path: str | None = Depends(get_scope_company_path),
):
    scope_condition = _request_scope_condition(company_path)

    stmt = select(Request)
    if all_requests:
        # The requests archive — every request the caller's company scope
        # can see, not just their own or ones awaiting their approval.
        if user.role not in ASSET_MANAGER_ROLES:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Not permitted to view all requests")
        if scope_condition is not None:
            stmt = stmt.where(scope_condition)
        if type_:
            stmt = stmt.where(Request.type == type_)
        if status_:
            stmt = stmt.where(Request.status == status_)
    elif mine:
        stmt = stmt.where(Request.requester_id == user.id)
    elif pending_for_me:
        stmt = stmt.where(Request.status == "pending", Request.approver_role == user.role)
        if scope_condition is not None:
            stmt = stmt.where(scope_condition)
    else:
        # Default: the caller's own requests, plus whatever's pending at their role.
        pending_mine = (Request.status == "pending") & (Request.approver_role == user.role)
        if scope_condition is not None:
            pending_mine = pending_mine & scope_condition
        stmt = stmt.where(or_(Request.requester_id == user.id, pending_mine))
    stmt = stmt.order_by(Request.created_at.desc())
    result = await db.execute(stmt)
    reqs = result.scalars().all()

    requester_ids = {r.requester_id for r in reqs}
    names: dict[uuid.UUID, str] = {}
    if requester_ids:
        result = await db.execute(select(User).where(User.id.in_(requester_ids)))
        names = {u.id: (u.full_name or u.email) for u in result.scalars().all()}

    return [
        RequestListItem(
            id=r.id, type=r.type, status=r.status, origin=r.origin, requester_id=r.requester_id,
            requester_name=names.get(r.requester_id), approver_role=r.approver_role,
            created_at=r.created_at,
        )
        for r in reqs
    ]


@router.post("/delete", response_model=RequestDeleteResult)
async def delete_requests(
    body: RequestDeleteRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    if not body.ids:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "No request ids provided")
    result = await db.execute(delete(Request).where(Request.id.in_(body.ids)))
    await db.commit()
    return RequestDeleteResult(deleted=result.rowcount)


@router.get("/{request_id}", response_model=RequestOut)
async def get_request(
    request_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    company_path: str | None = Depends(get_scope_company_path),
):
    req = await _get_request_or_404(db, request_id)
    await _assert_request_visible(db, req, user, company_path)
    items = await _items_for(db, request_id)
    signatures = await _signatures_for(db, request_id)
    return _to_out(req, items, signatures)


async def _apply_effect(
    db: AsyncSession, req: Request, items: list[RequestItem], actor: User
) -> None:
    if req.type == "transfer":
        for item in items:
            if not item.asset_id:
                continue
            asset = await db.get(Asset, item.asset_id)
            if not asset:
                continue
            asset.holder_user_id = req.to_holder_user_id
            asset.department = req.to_department or asset.department
            asset.location = req.to_location or asset.location
            asset.status = "da_dieu_dong"
            db.add(
                AssetEvent(
                    asset_id=asset.id, actor_id=actor.id, type="status_change",
                    note=f"Điều động theo yêu cầu {req.id}",
                )
            )
        req.status = "completed"
    elif req.type == "liquidate":
        for item in items:
            if not item.asset_id:
                continue
            asset = await db.get(Asset, item.asset_id)
            if not asset:
                continue
            asset.status = "da_thanh_ly"
            price_note = (
                f" — giá bán duyệt: {item.approved_sale_price:,.0f}đ"
                if item.approved_sale_price is not None
                else ""
            )
            db.add(
                AssetEvent(
                    asset_id=asset.id, actor_id=actor.id, type="status_change",
                    note=f"Thanh lý theo yêu cầu {req.id}{price_note}",
                )
            )
        req.status = "completed"
    elif req.type == "acquire":
        # One asset per line item regardless of `quantity` — quantity is an
        # informational multiplier for the printed total (Thành tiền), not a
        # request to spawn N separately-tracked assets. If per-unit tracking
        # is needed later, this is the place to revisit.
        requester = await db.get(User, req.requester_id)
        for item in items:
            if item.asset_id:
                continue
            asset = Asset(
                name=item.name,
                manufacturer=item.manufacturer,
                original_cost=item.unit_price,
                company_id=requester.company_id if requester else None,
                domain="b",
                department=req.to_department,
                holder_user_id=req.to_holder_user_id,
                created_by=actor.id,
                notes=(
                    f"Tạo từ yêu cầu mua sắm {req.id}"
                    + (f" — {item.purpose}" if item.purpose else "")
                ),
            )
            db.add(asset)
            await db.flush()
            item.asset_id = asset.id
            db.add(
                AssetEvent(
                    asset_id=asset.id, actor_id=actor.id, type="created",
                    note=f"Tạo từ yêu cầu mua sắm {req.id}",
                )
            )
        req.status = "completed"


@router.post("/{request_id}/decide", response_model=RequestOut)
async def decide_request(
    request_id: uuid.UUID,
    body: RequestDecide,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    company_path: str | None = Depends(get_scope_company_path),
):
    req = await _get_request_or_404(db, request_id)
    if req.status != "pending":
        raise HTTPException(status.HTTP_409_CONFLICT, "Request already decided")
    if user.role != req.approver_role and user.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not the approver for this request")
    await _assert_request_visible(db, req, user, company_path)

    items = await _items_for(db, request_id)

    if body.items:
        items_by_id = {i.id: i for i in items}
        for update in body.items:
            item = items_by_id.get(update.id)
            if item:
                item.approved_sale_price = update.approved_sale_price

    req.status = "approved" if body.approve else "rejected"
    req.decided_by_id = user.id
    req.decided_at = datetime.now(timezone.utc)
    req.decision_note = body.note

    if body.approve:
        await _apply_effect(db, req, items, user)

    _notify_requester_decided(db, req)

    await db.commit()
    await db.refresh(req)
    items = await _items_for(db, request_id)
    signatures = await _signatures_for(db, request_id)
    return _to_out(req, items, signatures)


@router.post(
    "/{request_id}/sign", response_model=RequestSignatureOut, status_code=status.HTTP_201_CREATED
)
async def sign_request(
    request_id: uuid.UUID,
    signed_name: str = Form(...),
    signature_image: UploadFile | None = File(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    company_path: str | None = Depends(get_scope_company_path),
):
    req = await _get_request_or_404(db, request_id)

    if user.id == req.requester_id:
        role_in_flow = "requester"
    elif user.role == req.approver_role or user.role == "admin":
        role_in_flow = "approver"
    else:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not a party to this request")
    await _assert_request_visible(db, req, user, company_path)

    already = await db.execute(
        select(RequestSignature).where(
            RequestSignature.request_id == request_id,
            RequestSignature.role_in_flow == role_in_flow,
        )
    )
    if already.scalar_one_or_none():
        raise HTTPException(status.HTTP_409_CONFLICT, "Already signed")

    image_object_name = None
    if signature_image is not None:
        content = await signature_image.read()
        if len(content) > MAX_UPLOAD_BYTES:
            raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "File too large")
        image_object_name = store_object(
            content, signature_image.filename or "signature.png", signature_image.content_type
        )

    signature = RequestSignature(
        request_id=request_id,
        actor_id=user.id,
        role_in_flow=role_in_flow,
        signed_name=signed_name,
        signature_image_url=image_object_name,
        content_hash=content_hash_for(req),
    )
    db.add(signature)
    await db.commit()
    await db.refresh(signature)
    return signature


@router.get("/{request_id}/pdf")
async def get_request_pdf(
    request_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    company_path: str | None = Depends(get_scope_company_path),
):
    req = await _get_request_or_404(db, request_id)
    await _assert_request_visible(db, req, user, company_path)

    items = await _items_for(db, request_id)
    asset_ids = [i.asset_id for i in items if i.asset_id]
    assets_by_id = {}
    if asset_ids:
        result = await db.execute(select(Asset).where(Asset.id.in_(asset_ids)))
        assets_by_id = {a.id: a for a in result.scalars().all()}

    requester = await db.get(User, req.requester_id)
    approver = await db.get(User, req.decided_by_id) if req.decided_by_id else None
    from_holder = await db.get(User, req.from_holder_user_id) if req.from_holder_user_id else None
    to_holder = await db.get(User, req.to_holder_user_id) if req.to_holder_user_id else None
    signatures = await _signatures_for(db, request_id)
    council = json.loads(req.council_snapshot) if req.council_snapshot else []

    pdf_bytes = render_request_pdf(
        request=req,
        items=items,
        assets_by_id=assets_by_id,
        requester=requester,
        approver=approver,
        from_holder=from_holder,
        to_holder=to_holder,
        signatures=signatures,
        council=council,
    )
    return Response(content=pdf_bytes, media_type="application/pdf")
