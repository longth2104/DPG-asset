import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import Response
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.api.upload import MAX_UPLOAD_BYTES, store_object
from app.core.database import get_db
from app.models.asset import Asset
from app.models.asset_event import AssetEvent
from app.models.request import APPROVER_ROLE_BY_TYPE, REQUEST_SCOPES, REQUEST_TYPES, Request, RequestSignature
from app.models.user import User
from app.schemas.request import (
    RequestCreate,
    RequestDecide,
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


async def _get_asset_or_404(db: AsyncSession, asset_id: uuid.UUID) -> Asset:
    asset = await db.get(Asset, asset_id)
    if not asset:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Asset not found")
    return asset


async def _signatures_for(db: AsyncSession, request_id: uuid.UUID) -> list[RequestSignature]:
    result = await db.execute(
        select(RequestSignature)
        .where(RequestSignature.request_id == request_id)
        .order_by(RequestSignature.signed_at)
    )
    return result.scalars().all()


def _to_out(req: Request, signatures: list[RequestSignature]) -> RequestOut:
    return RequestOut(
        **RequestListItem.model_validate(req).model_dump(),
        scope=req.scope,
        from_holder_user_id=req.from_holder_user_id,
        to_holder_user_id=req.to_holder_user_id,
        from_department=req.from_department,
        to_department=req.to_department,
        from_location=req.from_location,
        to_location=req.to_location,
        justification=req.justification,
        estimated_cost=float(req.estimated_cost) if req.estimated_cost is not None else None,
        reason=req.reason,
        condition_note=req.condition_note,
        decided_by_id=req.decided_by_id,
        decided_at=req.decided_at,
        decision_note=req.decision_note,
        generated_document_id=req.generated_document_id,
        updated_at=req.updated_at,
        signatures=[RequestSignatureOut.model_validate(s) for s in signatures],
    )


@router.post("", response_model=RequestOut, status_code=status.HTTP_201_CREATED)
async def create_request(
    body: RequestCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if body.type not in REQUEST_TYPES:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Unknown request type")
    if body.scope is not None and body.scope not in REQUEST_SCOPES:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Unknown scope")

    asset = None
    if body.type in ("transfer", "liquidate"):
        if not body.asset_id:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "asset_id is required")
        asset = await _get_asset_or_404(db, body.asset_id)
    elif body.asset_id:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "acquire requests have no existing asset")

    req = Request(
        type=body.type,
        asset_id=body.asset_id,
        requester_id=user.id,
        scope=body.scope,
        to_holder_user_id=body.to_holder_user_id,
        from_department=body.from_department,
        to_department=body.to_department,
        from_location=body.from_location,
        to_location=body.to_location,
        justification=body.justification,
        estimated_cost=body.estimated_cost,
        reason=body.reason,
        condition_note=body.condition_note,
        approver_role=APPROVER_ROLE_BY_TYPE[body.type],
    )
    if body.type == "transfer" and asset:
        req.from_holder_user_id = asset.holder_user_id
        req.from_department = req.from_department or asset.department
        req.from_location = req.from_location or asset.location

    db.add(req)
    await db.flush()

    if asset:
        db.add(
            AssetEvent(
                asset_id=asset.id,
                actor_id=user.id,
                type="note",
                note=f"Yêu cầu {body.type} được tạo (mã yêu cầu {req.id})",
            )
        )

    await db.commit()
    await db.refresh(req)
    return _to_out(req, [])


@router.get("", response_model=list[RequestListItem])
async def list_requests(
    mine: bool = Query(False),
    pending_for_me: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(Request)
    if mine:
        stmt = stmt.where(Request.requester_id == user.id)
    elif pending_for_me:
        stmt = stmt.where(Request.status == "pending", Request.approver_role == user.role)
    else:
        # Default: the caller's own requests, plus whatever's pending at their role.
        stmt = stmt.where(
            or_(
                Request.requester_id == user.id,
                (Request.status == "pending") & (Request.approver_role == user.role),
            )
        )
    stmt = stmt.order_by(Request.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{request_id}", response_model=RequestOut)
async def get_request(
    request_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    req = await _get_request_or_404(db, request_id)
    signatures = await _signatures_for(db, request_id)
    return _to_out(req, signatures)


async def _apply_effect(db: AsyncSession, req: Request, actor: User) -> None:
    if req.type == "transfer" and req.asset_id:
        asset = await db.get(Asset, req.asset_id)
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
    elif req.type == "liquidate" and req.asset_id:
        asset = await db.get(Asset, req.asset_id)
        asset.status = "da_thanh_ly"
        db.add(
            AssetEvent(
                asset_id=asset.id, actor_id=actor.id, type="status_change",
                note=f"Thanh lý theo yêu cầu {req.id}",
            )
        )
        req.status = "completed"
    # acquire: approval alone doesn't create an asset yet — fulfillment stays
    # a manual follow-up until QT03 procurement execution ships (see plan.md Phase 2).


@router.post("/{request_id}/decide", response_model=RequestOut)
async def decide_request(
    request_id: uuid.UUID,
    body: RequestDecide,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    req = await _get_request_or_404(db, request_id)
    if req.status != "pending":
        raise HTTPException(status.HTTP_409_CONFLICT, "Request already decided")
    if user.role != req.approver_role and user.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not the approver for this request")

    req.status = "approved" if body.approve else "rejected"
    req.decided_by_id = user.id
    req.decided_at = datetime.now(timezone.utc)
    req.decision_note = body.note

    if body.approve:
        await _apply_effect(db, req, user)

    await db.commit()
    await db.refresh(req)
    signatures = await _signatures_for(db, request_id)
    return _to_out(req, signatures)


@router.post(
    "/{request_id}/sign", response_model=RequestSignatureOut, status_code=status.HTTP_201_CREATED
)
async def sign_request(
    request_id: uuid.UUID,
    signed_name: str = Form(...),
    signature_image: UploadFile | None = File(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    req = await _get_request_or_404(db, request_id)

    if user.id == req.requester_id:
        role_in_flow = "requester"
    elif user.role == req.approver_role or user.role == "admin":
        role_in_flow = "approver"
    else:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not a party to this request")

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
    _: User = Depends(get_current_user),
):
    req = await _get_request_or_404(db, request_id)
    asset = await db.get(Asset, req.asset_id) if req.asset_id else None
    requester = await db.get(User, req.requester_id)
    approver = await db.get(User, req.decided_by_id) if req.decided_by_id else None
    from_holder = await db.get(User, req.from_holder_user_id) if req.from_holder_user_id else None
    to_holder = await db.get(User, req.to_holder_user_id) if req.to_holder_user_id else None
    signatures = await _signatures_for(db, request_id)

    pdf_bytes = render_request_pdf(
        request=req,
        asset=asset,
        requester=requester,
        approver=approver,
        from_holder=from_holder,
        to_holder=to_holder,
        signatures=signatures,
    )
    return Response(content=pdf_bytes, media_type="application/pdf")
