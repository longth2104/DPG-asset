import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_asset_manager
from app.api.upload import MAX_UPLOAD_BYTES, store_object
from app.core.database import get_db
from app.models.asset import Asset
from app.models.asset_event import AssetEvent
from app.models.document import Document
from app.models.user import User
from app.schemas.asset import (
    AssetCreate,
    AssetEventCreate,
    AssetEventOut,
    AssetListItem,
    AssetOut,
    AssetUpdate,
)
from app.schemas.document import DocumentOut

router = APIRouter(prefix="/api/assets", tags=["assets"])


def _generate_asset_code() -> str:
    return f"A-{uuid.uuid4().hex[:8].upper()}"


async def _get_asset_or_404(db: AsyncSession, asset_id: uuid.UUID) -> Asset:
    asset = await db.get(Asset, asset_id)
    if not asset:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Asset not found")
    return asset


async def _log_event(
    db: AsyncSession, asset_id: uuid.UUID, actor_id: uuid.UUID, type_: str, note: str | None
) -> None:
    db.add(AssetEvent(asset_id=asset_id, actor_id=actor_id, type=type_, note=note))


@router.get("", response_model=list[AssetListItem])
async def list_assets(
    department: str | None = Query(None),
    category: str | None = Query(None),
    status_: str | None = Query(None, alias="status"),
    location: str | None = Query(None),
    search: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    stmt = select(Asset)
    if department:
        stmt = stmt.where(Asset.department == department)
    if category:
        stmt = stmt.where(Asset.category == category)
    if status_:
        stmt = stmt.where(Asset.status == status_)
    if location:
        stmt = stmt.where(Asset.location == location)
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(
            (Asset.name.ilike(pattern))
            | (Asset.asset_code.ilike(pattern))
            | (Asset.holder.ilike(pattern))
        )
    stmt = stmt.order_by(Asset.name)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{asset_id}", response_model=AssetOut)
async def get_asset(
    asset_id: uuid.UUID, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)
):
    asset = await _get_asset_or_404(db, asset_id)

    events = (
        (
            await db.execute(
                select(AssetEvent)
                .where(AssetEvent.asset_id == asset_id)
                .order_by(AssetEvent.timestamp.desc())
            )
        )
        .scalars()
        .all()
    )
    documents = (
        (
            await db.execute(
                select(Document)
                .where(Document.asset_id == asset_id)
                .order_by(Document.created_at.desc())
            )
        )
        .scalars()
        .all()
    )

    return AssetOut(
        **AssetListItem.model_validate(asset).model_dump(),
        spec=asset.spec,
        serial_number=asset.serial_number,
        manufacturer=asset.manufacturer,
        manufacture_year=asset.manufacture_year,
        year_put_in_use=asset.year_put_in_use,
        original_cost=float(asset.original_cost) if asset.original_cost is not None else None,
        warranty_months=asset.warranty_months,
        legal_entity=asset.legal_entity,
        budget_plan_year=asset.budget_plan_year,
        budget_actual_year=asset.budget_actual_year,
        replacement_priority=asset.replacement_priority,
        purchase_source=asset.purchase_source,
        notes=asset.notes,
        created_at=asset.created_at,
        updated_at=asset.updated_at,
        events=[AssetEventOut.model_validate(e) for e in events],
        documents=[DocumentOut.model_validate(d) for d in documents],
    )


@router.post("", response_model=AssetListItem, status_code=status.HTTP_201_CREATED)
async def create_asset(
    body: AssetCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_asset_manager),
):
    data = body.model_dump()
    if not data.get("asset_code"):
        data["asset_code"] = _generate_asset_code()

    asset = Asset(**data, created_by=user.id)
    db.add(asset)
    await db.flush()
    await _log_event(db, asset.id, user.id, "created", f"Tạo tài sản {asset.name}")
    await db.commit()
    await db.refresh(asset)
    return asset


@router.put("/{asset_id}", response_model=AssetListItem)
async def update_asset(
    asset_id: uuid.UUID,
    body: AssetUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_asset_manager),
):
    asset = await _get_asset_or_404(db, asset_id)

    changes = body.model_dump(exclude_unset=True)
    if not changes:
        return asset

    status_changed = "status" in changes and changes["status"] != asset.status
    old_status = asset.status
    changed_fields = [f for f, v in changes.items() if getattr(asset, f) != v]

    for field, value in changes.items():
        setattr(asset, field, value)

    if status_changed:
        await _log_event(
            db, asset.id, user.id, "status_change", f"{old_status} → {asset.status}"
        )
    elif changed_fields:
        await _log_event(
            db, asset.id, user.id, "updated", "Cập nhật: " + ", ".join(changed_fields)
        )

    await db.commit()
    await db.refresh(asset)
    return asset


@router.post("/{asset_id}/events", response_model=AssetEventOut, status_code=status.HTTP_201_CREATED)
async def add_note_event(
    asset_id: uuid.UUID,
    body: AssetEventCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_asset_manager),
):
    await _get_asset_or_404(db, asset_id)
    event = AssetEvent(asset_id=asset_id, actor_id=user.id, type="note", note=body.note)
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event


@router.post(
    "/{asset_id}/documents", response_model=DocumentOut, status_code=status.HTTP_201_CREATED
)
async def upload_document(
    asset_id: uuid.UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_asset_manager),
):
    await _get_asset_or_404(db, asset_id)

    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "File too large")

    object_name = store_object(content, file.filename or "file", file.content_type)

    document = Document(
        filename=file.filename or object_name,
        file_url=object_name,
        content_type=file.content_type,
        size_bytes=len(content),
        uploaded_by=user.id,
        asset_id=asset_id,
    )
    db.add(document)
    await _log_event(db, asset_id, user.id, "note", f"Tải lên tài liệu: {document.filename}")
    await db.commit()
    await db.refresh(document)
    return document
