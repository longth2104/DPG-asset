import uuid
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import Response
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_current_user,
    get_scope_company_path,
    require_admin,
    require_asset_manager,
)
from app.api.upload import MAX_UPLOAD_BYTES, store_object
from app.core.database import get_db
from app.models.asset import Asset
from app.models.asset_event import AssetEvent
from app.models.asset_maintenance import AssetMaintenanceRecord
from app.models.company import Company
from app.models.document import Document
from app.models.request import Request, RequestItem
from app.models.user import User
from app.schemas.asset import (
    AssetCreate,
    AssetDeleteRequest,
    AssetDeleteResult,
    AssetEventCreate,
    AssetEventOut,
    AssetExportRequest,
    AssetImportResult,
    AssetListItem,
    AssetOut,
    AssetSyncResult,
    AssetUpdate,
)
from app.schemas.asset_maintenance import (
    AssetMaintenanceRecordCreate,
    AssetMaintenanceRecordOut,
    AssetMaintenanceRecordUpdate,
)
from app.schemas.document import DocumentOut
from app.services.excel import build_asset_xlsx, parse_asset_xlsx
from app.services.pdf import render_asset_dossier_pdf, render_asset_export_pdf
from app.services.hris import search_employees
from app.services.rds import fetch_all_assets
from app.services.user_provisioning import find_or_create_user_by_email, find_user_by_name

router = APIRouter(prefix="/api/assets", tags=["assets"])


def _generate_asset_code() -> str:
    return f"A-{uuid.uuid4().hex[:8].upper()}"


def _scope_filter(stmt, company_path: str | None):
    """Joins Company and restricts to its subtree when the caller isn't
    unrestricted (see app.api.deps.get_scope_company_path)."""
    if company_path is not None:
        stmt = stmt.join(Company, Asset.company_id == Company.id).where(
            Company.path.startswith(company_path)
        )
    return stmt


def _asset_search_condition(pattern: str):
    """Matches name/code/holder text same as before, plus (new) the linked
    holder's email — so typing a person's HRIS email in the search box finds
    whatever asset they currently hold, not just a literal name match."""
    holder_ids_by_email = select(User.id).where(User.email.ilike(pattern))
    return (
        Asset.name.ilike(pattern)
        | Asset.asset_code.ilike(pattern)
        | Asset.holder.ilike(pattern)
        | Asset.holder_user_id.in_(holder_ids_by_email)
    )


async def _get_asset_or_404(
    db: AsyncSession, asset_id: uuid.UUID, company_path: str | None = None
) -> Asset:
    asset = await db.get(Asset, asset_id)
    if not asset:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Asset not found")
    if company_path is not None:
        company = await db.get(Company, asset.company_id) if asset.company_id else None
        if not company or not company.path.startswith(company_path):
            # 404, not 403 — don't confirm existence of out-of-scope assets.
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
    company_path: str | None = Depends(get_scope_company_path),
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
        stmt = stmt.where(_asset_search_condition(f"%{search}%"))
    stmt = _scope_filter(stmt, company_path).order_by(Asset.name)
    result = await db.execute(stmt)
    assets = result.scalars().all()

    holder_ids = {a.holder_user_id for a in assets if a.holder_user_id}
    holder_emails = {}
    if holder_ids:
        result = await db.execute(select(User.id, User.email).where(User.id.in_(holder_ids)))
        holder_emails = dict(result.all())

    return [
        AssetListItem(
            **AssetListItem.model_validate(a).model_dump(exclude={"holder_email"}),
            holder_email=holder_emails.get(a.holder_user_id),
        )
        for a in assets
    ]


@router.get("/mine", response_model=list[AssetListItem])
async def list_my_assets(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    company_path: str | None = Depends(get_scope_company_path),
):
    stmt = select(Asset).where(Asset.holder_user_id == user.id)
    stmt = _scope_filter(stmt, company_path).order_by(Asset.name)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/export")
async def export_assets(
    body: AssetExportRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
    company_path: str | None = Depends(get_scope_company_path),
):
    if body.format not in ("xlsx", "pdf"):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "format must be 'xlsx' or 'pdf'")

    stmt = select(Asset)
    if body.ids:
        stmt = stmt.where(Asset.id.in_(body.ids))
    else:
        if body.department:
            stmt = stmt.where(Asset.department == body.department)
        if body.category:
            stmt = stmt.where(Asset.category == body.category)
        if body.status:
            stmt = stmt.where(Asset.status == body.status)
        if body.location:
            stmt = stmt.where(Asset.location == body.location)
        if body.search:
            stmt = stmt.where(_asset_search_condition(f"%{body.search}%"))
    stmt = _scope_filter(stmt, company_path).order_by(Asset.name)
    assets = (await db.execute(stmt)).scalars().all()

    if body.format == "xlsx":
        holder_ids = {a.holder_user_id for a in assets if a.holder_user_id}
        holder_emails = {}
        if holder_ids:
            result = await db.execute(select(User.id, User.email).where(User.id.in_(holder_ids)))
            holder_emails = dict(result.all())
        company_ids = {a.company_id for a in assets if a.company_id}
        company_codes = {}
        if company_ids:
            result = await db.execute(select(Company.id, Company.code).where(Company.id.in_(company_ids)))
            company_codes = dict(result.all())
        content = build_asset_xlsx(assets, holder_emails, company_codes)
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = "danh-sach-tai-san.xlsx"
    else:
        content = render_asset_export_pdf(assets)
        media_type = "application/pdf"
        filename = "danh-sach-tai-san.pdf"

    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/import", response_model=AssetImportResult)
async def import_assets(
    file: UploadFile = File(...),
    # Fallback company for any row whose file has no (or an unrecognized)
    # company column — the frontend always sends this, pre-filled to the
    # importer's own company but changeable, per docs/field.md.
    default_company_id: uuid.UUID | None = Form(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_asset_manager),
):
    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "File too large")

    try:
        rows = parse_asset_xlsx(content)
    except ValueError as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(e))

    companies = (await db.execute(select(Company))).scalars().all()
    companies_by_code = {c.code.strip().lower(): c for c in companies if c.code}
    companies_by_name = {c.name.strip().lower(): c for c in companies if c.name}
    fallback_company_id = default_company_id or user.company_id

    # A duplicate asset_code would otherwise crash the whole import with an
    # unhandled IntegrityError — a real risk given export→edit→re-import is
    # the exact round trip this endpoint is meant to support. Pre-check
    # against existing codes and track codes seen so far in this file so an
    # intra-file duplicate is caught the same way.
    incoming_codes = {row["asset_code"] for row in rows if row.get("asset_code")}
    existing_codes = set()
    if incoming_codes:
        result = await db.execute(select(Asset.asset_code).where(Asset.asset_code.in_(incoming_codes)))
        existing_codes = {code for (code,) in result.all()}
    seen_codes = set(existing_codes)

    # Fetched once for the whole file rather than per row — matched against
    # each row's plain-text `holder` name below when there's no holder_email
    # column. Empty (not an error) if HRIS is unreachable: holders just stay
    # free text, same as before this existed.
    try:
        hris_directory = await search_employees()
    except (RuntimeError, httpx.HTTPError):
        hris_directory = []

    imported = 0
    errors: list[dict] = []
    for idx, row in enumerate(rows, start=2):
        if not row.get("name"):
            errors.append({"row": idx, "reason": "Thiếu tên tài sản"})
            continue
        code = row.get("asset_code")
        if code and code in seen_codes:
            errors.append({"row": idx, "reason": f"Mã tài sản đã tồn tại: {code}"})
            continue
        if not code:
            code = _generate_asset_code()
            row["asset_code"] = code
        seen_codes.add(code)

        # Not a real Asset column — resolved to holder_user_id via a
        # reliable exact-email match.
        holder_email = row.pop("holder_email", None)
        holder_user_id = None
        if holder_email:
            holder = await find_or_create_user_by_email(db, holder_email)
            holder_user_id = holder.id if holder else None
        elif row.get("holder") and hris_directory:
            # No email column — fall back to matching the free-text holder
            # name against HRIS. Only links when the name is unambiguous
            # (see find_user_by_name); otherwise `holder` stays plain text,
            # same as always.
            holder = await find_user_by_name(db, row["holder"], hris_directory)
            holder_user_id = holder.id if holder else None

        # Not a real Asset column — a "Công ty" column (matched by code or
        # name) resolves straight to a real Company; anything else (column
        # missing, or its value matching no known company) falls back to
        # default_company_id, which itself falls back to the importer's own
        # company — so this never ends up unset.
        company_text = (row.pop("company", None) or "").strip().lower()
        company = companies_by_code.get(company_text) or companies_by_name.get(company_text)
        company_id = company.id if company else fallback_company_id

        asset = Asset(**row, holder_user_id=holder_user_id, created_by=user.id, company_id=company_id)
        db.add(asset)
        await db.flush()
        await _log_event(db, asset.id, user.id, "created", f"Nhập từ file Excel: {file.filename}")
        imported += 1

    await db.commit()
    return AssetImportResult(imported=imported, skipped=len(errors), errors=errors)


@router.post("/backfill-holders")
async def backfill_holders(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_asset_manager),
):
    """Link assets that carry only a free-text holder (holder_user_id null) to a
    real account by matching the name against the HRIS directory — the SAME
    exact, unambiguous match the Excel import uses (find_user_by_name), which
    auto-provisions the account from HRIS when needed and never guesses on a
    name collision, so it can't mislink. Rows whose holder name is missing,
    unmatched, or ambiguous stay free text (still findable via the
    /eoffice/assets holder_name filter). Idempotent: re-running only revisits
    rows that are still unlinked. Use it to repair data imported before an
    email column existed or while HRIS was unreachable.
    """
    try:
        hris_directory = await search_employees()
    except (RuntimeError, httpx.HTTPError):
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Không truy cập được danh bạ HRIS")

    result = await db.execute(
        select(Asset).where(Asset.holder_user_id.is_(None), Asset.holder.isnot(None), Asset.holder != "")
    )
    assets = result.scalars().all()
    linked = 0
    for asset in assets:
        holder = await find_user_by_name(db, asset.holder, hris_directory)
        if not holder:
            continue
        asset.holder_user_id = holder.id
        await db.flush()
        await _log_event(db, asset.id, user.id, "note", f"Liên kết người giữ theo tài khoản HRIS: {holder.email}")
        linked += 1
    await db.commit()
    return {"scanned": len(assets), "linked": linked, "unresolved": len(assets) - linked}


@router.post("/delete", response_model=AssetDeleteResult)
async def delete_assets(
    body: AssetDeleteRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_asset_manager),
    company_path: str | None = Depends(get_scope_company_path),
):
    if not body.ids:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "No asset ids provided")

    # Resolve which of the requested ids are actually in scope before
    # deleting — silently drops out-of-scope ids rather than erroring, same
    # posture as export's id filtering.
    id_stmt = select(Asset.id).where(Asset.id.in_(body.ids))
    id_stmt = _scope_filter(id_stmt, company_path)
    allowed_ids = {row[0] for row in (await db.execute(id_stmt)).all()}

    if not allowed_ids:
        return AssetDeleteResult(deleted=0)

    # A single bulk statement so Postgres's own ON DELETE CASCADE (assets ->
    # asset_events/documents/request_items -> request_signatures) handles
    # cleanup — deleting an asset here also deletes its history, documents,
    # and any request line items referencing it; the frontend confirmation
    # dialog says so.
    result = await db.execute(delete(Asset).where(Asset.id.in_(allowed_ids)))

    # A request whose every item just got cascade-deleted is a bare header
    # with nothing left in it — sweep those away too, per "requests are also
    # deleted ... when the asset related is deleted."
    await db.execute(
        delete(Request).where(~Request.id.in_(select(RequestItem.request_id).distinct()))
    )

    await db.commit()
    return AssetDeleteResult(deleted=result.rowcount)


@router.post("/sync-rds", response_model=AssetSyncResult)
async def sync_from_rds(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
):
    """Pulls the full asset listing from RDS and upserts it into the
    registry — matched by rds_id first, falling back to asset_code, so
    re-running is safe. Spans every company, so admin-only."""
    try:
        rows = await fetch_all_assets()
    except RuntimeError as e:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(e))
    except httpx.HTTPError as e:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"RDS request failed: {e}")

    companies = {c.code: c for c in (await db.execute(select(Company))).scalars().all()}

    created = 0
    updated = 0
    unmapped_companies: set[str] = set()

    for row in rows:
        rds_id = row.get("id")
        extra = row.get("extra") or {}
        notes_parts = [
            part
            for part in [
                f"Xuất xứ: {extra['origin']}" if extra.get("origin") else None,
                f"Nhóm TSCĐ: {extra['asset_group']}" if extra.get("asset_group") else None,
                f"Đơn vị tính: {extra['unit']}" if extra.get("unit") else None,
                f"Số kỳ phân bổ: {extra['alloc_periods']}" if extra.get("alloc_periods") else None,
                row.get("description"),
            ]
            if part
        ]
        mapped = {
            "asset_code": row.get("code"),
            "name": row.get("name") or row.get("code") or f"RDS-{rds_id}",
            "category": extra.get("asset_class"),
            "notes": " | ".join(notes_parts) or None,
        }

        company_code = row.get("company_code")
        company = companies.get(company_code) if company_code else None
        if company_code and not company:
            unmapped_companies.add(company_code)

        asset = None
        if rds_id is not None:
            result = await db.execute(select(Asset).where(Asset.rds_id == rds_id))
            asset = result.scalar_one_or_none()
        if not asset and mapped["asset_code"]:
            result = await db.execute(select(Asset).where(Asset.asset_code == mapped["asset_code"]))
            asset = result.scalar_one_or_none()

        if asset:
            for field, value in mapped.items():
                if value is not None:
                    setattr(asset, field, value)
            asset.rds_id = rds_id
            if company:
                asset.company_id = company.id
            updated += 1
        else:
            asset = Asset(
                **{k: v for k, v in mapped.items() if v is not None},
                rds_id=rds_id,
                company_id=company.id if company else None,
                domain="a",
                created_by=user.id,
            )
            db.add(asset)
            await db.flush()
            await _log_event(db, asset.id, user.id, "created", "Đồng bộ từ RDS")
            created += 1

    await db.commit()
    return AssetSyncResult(
        created=created, updated=updated, unmapped_companies=sorted(unmapped_companies)
    )


@router.get("/{asset_id}", response_model=AssetOut)
async def get_asset(
    asset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
    company_path: str | None = Depends(get_scope_company_path),
):
    asset = await _get_asset_or_404(db, asset_id, company_path)
    # If this asset was just mutated elsewhere in the same session (e.g. a
    # request's _apply_effect) without a refresh, server-computed columns
    # like updated_at are left expired — a bare attribute access on those
    # below would try to lazy-load outside the async greenlet and crash.
    # Safe no-op when the object is already fresh.
    await db.refresh(asset)

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

    maintenance_records = (
        (
            await db.execute(
                select(AssetMaintenanceRecord)
                .where(AssetMaintenanceRecord.asset_id == asset_id)
                .order_by(AssetMaintenanceRecord.reported_at.desc())
            )
        )
        .scalars()
        .all()
    )
    maintenance_docs_by_record: dict[uuid.UUID, list[Document]] = {}
    maintenance_ids = [m.id for m in maintenance_records]
    if maintenance_ids:
        result = await db.execute(
            select(Document)
            .where(Document.maintenance_record_id.in_(maintenance_ids))
            .order_by(Document.created_at.desc())
        )
        for d in result.scalars().all():
            maintenance_docs_by_record.setdefault(d.maintenance_record_id, []).append(d)

    holder_email = None
    if asset.holder_user_id:
        holder = await db.get(User, asset.holder_user_id)
        holder_email = holder.email if holder else None

    return AssetOut(
        **AssetListItem.model_validate(asset).model_dump(exclude={"holder_email"}),
        holder_email=holder_email,
        spec=asset.spec,
        serial_number=asset.serial_number,
        manufacturer=asset.manufacturer,
        manufacture_year=asset.manufacture_year,
        purchase_date=asset.purchase_date,
        year_put_in_use=asset.year_put_in_use,
        original_cost=float(asset.original_cost) if asset.original_cost is not None else None,
        warranty_months=asset.warranty_months,
        legal_entity=asset.legal_entity,
        project=asset.project,
        budget_plan_year=asset.budget_plan_year,
        budget_actual_year=asset.budget_actual_year,
        replacement_priority=asset.replacement_priority,
        purchase_source=asset.purchase_source,
        notes=asset.notes,
        extra_fields=asset.extra_fields,
        created_at=asset.created_at,
        updated_at=asset.updated_at,
        events=[AssetEventOut.model_validate(e) for e in events],
        documents=[DocumentOut.model_validate(d) for d in documents],
        maintenance_records=[
            AssetMaintenanceRecordOut(
                **AssetMaintenanceRecordOut.model_validate(m).model_dump(exclude={"documents"}),
                documents=[DocumentOut.model_validate(d) for d in maintenance_docs_by_record.get(m.id, [])],
            )
            for m in maintenance_records
        ],
    )


@router.post("", response_model=AssetListItem, status_code=status.HTTP_201_CREATED)
async def create_asset(
    body: AssetCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_asset_manager),
):
    data = body.model_dump()
    # Not an Asset column — resolve the picked HRIS employee's email to a real
    # account (auto-provisioned from HRIS) and link it; `holder` text still
    # carries the display name. Unresolved/empty email → link stays null.
    holder_email = data.pop("holder_email", None)
    holder_user_id = None
    if holder_email:
        holder = await find_or_create_user_by_email(db, holder_email)
        holder_user_id = holder.id if holder else None
    if not data.get("asset_code"):
        data["asset_code"] = _generate_asset_code()
    # Compulsory going forward — defaults to the creator's own company when
    # the form doesn't send one (never left unset).
    company_id = data.pop("company_id", None) or user.company_id

    asset = Asset(**data, holder_user_id=holder_user_id, created_by=user.id, company_id=company_id)
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
    company_path: str | None = Depends(get_scope_company_path),
):
    asset = await _get_asset_or_404(db, asset_id, company_path)

    changes = body.model_dump(exclude_unset=True)

    # Not an Asset column — only acted on when the form actually sent it (a
    # sentinel distinguishes "omitted" from "sent empty"). Sent with a value →
    # re-link holder_user_id to that HRIS account; sent empty → clear the link.
    _UNSET = object()
    holder_email = changes.pop("holder_email", _UNSET)
    holder_relinked = False
    if holder_email is not _UNSET:
        holder = await find_or_create_user_by_email(db, holder_email) if holder_email else None
        new_holder_id = holder.id if holder else None
        if asset.holder_user_id != new_holder_id:
            asset.holder_user_id = new_holder_id
            holder_relinked = True

    if not changes and not holder_relinked:
        return asset

    status_changed = "status" in changes and changes["status"] != asset.status
    old_status = asset.status
    changed_fields = [f for f, v in changes.items() if getattr(asset, f) != v]
    if holder_relinked:
        changed_fields.append("holder_user_id")

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


@router.post(
    "/{asset_id}/maintenance",
    response_model=AssetMaintenanceRecordOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_maintenance_record(
    asset_id: uuid.UUID,
    body: AssetMaintenanceRecordCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_asset_manager),
    company_path: str | None = Depends(get_scope_company_path),
):
    """Reports an asset as broken/under repair — per docs/cycle.md's
    maintenance log (when, where, cost, condition, documents). Flips the
    asset to "dang_sua_chua" only when it was actually in use, so this can't
    clobber a more terminal status (liquidated, reallocated) set in the
    meantime."""
    asset = await _get_asset_or_404(db, asset_id, company_path)
    record = AssetMaintenanceRecord(
        asset_id=asset_id,
        status="reported",
        location=body.location,
        cost=body.cost,
        condition_note=body.condition_note,
        created_by=user.id,
    )
    db.add(record)
    if asset.status == "dang_su_dung":
        asset.status = "dang_sua_chua"
    await _log_event(db, asset_id, user.id, "status_change", "Báo hỏng / đưa vào sửa chữa")
    await db.commit()
    await db.refresh(record)
    return AssetMaintenanceRecordOut(
        **AssetMaintenanceRecordOut.model_validate(record).model_dump(exclude={"documents"}), documents=[]
    )


@router.patch("/{asset_id}/maintenance/{record_id}", response_model=AssetMaintenanceRecordOut)
async def update_maintenance_record(
    asset_id: uuid.UUID,
    record_id: uuid.UUID,
    body: AssetMaintenanceRecordUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_asset_manager),
    company_path: str | None = Depends(get_scope_company_path),
):
    asset = await _get_asset_or_404(db, asset_id, company_path)
    record = await db.get(AssetMaintenanceRecord, record_id)
    if not record or record.asset_id != asset_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Maintenance record not found")

    changes = body.model_dump(exclude_unset=True, exclude={"resolve"})
    for field, value in changes.items():
        setattr(record, field, value)

    if body.resolve and not record.resolved_at:
        record.resolved_at = datetime.now(timezone.utc)
        record.status = "resolved"
        # Only reverts the asset if nothing else moved it on in the meantime
        # (e.g. a transfer/liquidation while under repair).
        if asset.status == "dang_sua_chua":
            asset.status = "dang_su_dung"
        await _log_event(db, asset_id, user.id, "status_change", "Sửa chữa hoàn tất")

    await db.commit()
    await db.refresh(record)
    documents = (
        (
            await db.execute(
                select(Document)
                .where(Document.maintenance_record_id == record_id)
                .order_by(Document.created_at.desc())
            )
        )
        .scalars()
        .all()
    )
    return AssetMaintenanceRecordOut(
        **AssetMaintenanceRecordOut.model_validate(record).model_dump(exclude={"documents"}),
        documents=[DocumentOut.model_validate(d) for d in documents],
    )


@router.post("/{asset_id}/events", response_model=AssetEventOut, status_code=status.HTTP_201_CREATED)
async def add_note_event(
    asset_id: uuid.UUID,
    body: AssetEventCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_asset_manager),
    company_path: str | None = Depends(get_scope_company_path),
):
    await _get_asset_or_404(db, asset_id, company_path)
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
    # Set when uploading a receipt/report against a specific maintenance
    # record rather than the asset generally (see AssetMaintenanceRecordOut).
    maintenance_record_id: uuid.UUID | None = Form(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_asset_manager),
    company_path: str | None = Depends(get_scope_company_path),
):
    await _get_asset_or_404(db, asset_id, company_path)

    if maintenance_record_id:
        record = await db.get(AssetMaintenanceRecord, maintenance_record_id)
        if not record or record.asset_id != asset_id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Maintenance record not found")

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
        maintenance_record_id=maintenance_record_id,
    )
    db.add(document)
    await _log_event(db, asset_id, user.id, "note", f"Tải lên tài liệu: {document.filename}")
    await db.commit()
    await db.refresh(document)
    return document


@router.get("/{asset_id}/pdf")
async def get_asset_dossier_pdf(
    asset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
    company_path: str | None = Depends(get_scope_company_path),
):
    asset = await _get_asset_or_404(db, asset_id, company_path)
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
    company = await db.get(Company, asset.company_id) if asset.company_id else None

    pdf_bytes = render_asset_dossier_pdf(asset, documents, events, company.name if company else None)
    return Response(content=pdf_bytes, media_type="application/pdf")
