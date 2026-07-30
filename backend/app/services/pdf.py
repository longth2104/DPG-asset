import base64
import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML

from app.api.upload import get_object_bytes
from app.models.asset import ASSET_STATUS_LABELS
from app.models.request import Request, RequestItem, RequestSignature
from app.services.vi_words import amount_in_words_vi

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"

_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html"]),
)

# Template per request type — each is a self-contained multi-section
# document (later sections appended once the request is decided), rebuilt
# to match the real BM-numbered forms in docs/Long/ rather than a generic
# layout.
TEMPLATE_BY_TYPE = {
    "transfer": "request_transfer.html",
    "acquire": "request_acquire.html",
    "liquidate": "request_liquidate.html",
}

REQUEST_STATUS_LABELS = {
    "pending": "Chờ duyệt",
    "approved": "Đã duyệt",
    "rejected": "Từ chối",
    "completed": "Hoàn tất",
}

SCOPE_LABELS = {
    "individual": "Cá nhân",
    "department": "Phòng ban",
    "branch": "Chi nhánh",
    "project": "Dự án",
}

COUNCIL_ROLE_LABELS = {
    "chu_tich": "Chủ tịch",
    "pho_chu_tich": "Phó Chủ tịch",
    "thanh_vien": "Thành viên",
}


def _user_label(user) -> str | None:
    if not user:
        return None
    return user.full_name or user.email


def _money(value) -> str:
    return f"{value:,.0f}" if value is not None else "—"


def _extract_origin(notes: str | None) -> str | None:
    """RDS-synced assets fold "Xuất xứ: X" into notes (see services/rds.py)
    — recovered here for the liquidation council's "Nước sản xuất" column,
    since Asset has no dedicated country-of-origin field."""
    if not notes:
        return None
    match = re.search(r"Xuất xứ:\s*([^|]+)", notes)
    return match.group(1).strip() if match else None


def _signature_image_data_uri(signature: RequestSignature | None) -> str | None:
    if not signature or not signature.signature_image_url:
        return None
    content = get_object_bytes(signature.signature_image_url)
    ext = signature.signature_image_url.rsplit(".", 1)[-1].lower()
    mime = "image/jpeg" if ext in ("jpg", "jpeg") else "image/png"
    return f"data:{mime};base64,{base64.b64encode(content).decode()}"


def content_hash_for(request: Request) -> str:
    """Hashes the request's user-editable header fields at signing time —
    per docs/feature-spec.md §7, a signed document's content is then
    immutable; corrections require filing a new request, not editing this
    one. Line items aren't included: they're only ever added at creation
    (before any signature) or have approved_sale_price set by the very
    decide action a signature accompanies."""
    fields = [
        request.type, request.scope, request.requester_department,
        request.from_department, request.to_department,
        request.from_location, request.to_location,
        request.to_contact_name, request.to_contact_id_card,
        request.justification, request.reason,
        request.status, request.decision_note,
    ]
    raw = "|".join("" if f is None else str(f) for f in fields)
    return hashlib.sha256(raw.encode()).hexdigest()


def _item_view(item: RequestItem, asset) -> dict:
    quantity = item.quantity or 1
    unit_price = float(item.unit_price) if item.unit_price is not None else None
    line_total = unit_price * quantity if unit_price is not None else None
    return {
        "name": item.name,
        "unit": item.unit or "—",
        "quantity": quantity,
        "unit_price_label": _money(unit_price),
        "line_total": line_total,
        "line_total_label": _money(line_total),
        "manufacturer": item.manufacturer or (asset.manufacturer if asset else None) or "—",
        "purpose": item.purpose or "—",
        "asset_code": asset.asset_code if asset else None,
        "serial_number": asset.serial_number if asset else None,
        "warranty_months": asset.warranty_months if asset else None,
        "manufacture_year": asset.manufacture_year if asset else None,
        "year_put_in_use": asset.year_put_in_use if asset else None,
        "spec": (asset.spec if asset else None) or "—",
        "origin": _extract_origin(asset.notes if asset else None) or "—",
        "original_cost": float(asset.original_cost) if asset and asset.original_cost is not None else None,
        "original_cost_label": _money(float(asset.original_cost)) if asset and asset.original_cost is not None else "—",
        "remaining_value_label": _money(float(item.remaining_value)) if item.remaining_value is not None else "—",
        "market_value_label": _money(float(item.market_value)) if item.market_value is not None else "—",
        "proposed_value_label": _money(float(item.proposed_value)) if item.proposed_value is not None else "—",
        "approved_sale_price": (
            float(item.approved_sale_price) if item.approved_sale_price is not None else None
        ),
        "approved_sale_price_label": (
            _money(float(item.approved_sale_price)) if item.approved_sale_price is not None else "—"
        ),
        "condition_note": item.condition_note or "Hoạt động bình thường",
    }


def render_request_pdf(
    *,
    request: Request,
    items: list[RequestItem],
    assets_by_id: dict,
    requester,
    approver,
    from_holder,
    to_holder,
    signatures: list[RequestSignature],
    council: list[dict],
) -> bytes:
    requester_signature = next((s for s in signatures if s.role_in_flow == "requester"), None)
    approver_signature = next((s for s in signatures if s.role_in_flow == "approver"), None)

    item_views = [_item_view(item, assets_by_id.get(item.asset_id)) for item in items]
    grand_total = sum(v["line_total"] for v in item_views if v["line_total"] is not None) or 0
    liquidation_total = sum(
        v["approved_sale_price"] for v in item_views if v["approved_sale_price"] is not None
    )

    council_view = [
        {**m, "council_role_label": COUNCIL_ROLE_LABELS.get(m["council_role"], m["council_role"])}
        for m in council
    ]

    context = {
        "request": request,
        "items": item_views,
        "grand_total": grand_total,
        "grand_total_label": _money(grand_total),
        "amount_words": amount_in_words_vi(grand_total) if grand_total else None,
        "liquidation_total_label": _money(liquidation_total) if liquidation_total else "—",
        "liquidation_total_words": amount_in_words_vi(liquidation_total) if liquidation_total else None,
        "requester_name": _user_label(requester) or "—",
        "requester_department": request.requester_department or "—",
        "approver_name": _user_label(approver),
        "status_label": REQUEST_STATUS_LABELS.get(request.status, request.status),
        "scope_label": SCOPE_LABELS.get(request.scope, request.scope or "—"),
        "from_holder_name": _user_label(from_holder),
        "to_holder_name": _user_label(to_holder) or request.to_contact_name,
        "council": council_view,
        "requester_signature": requester_signature,
        "approver_signature": approver_signature,
        "requester_signature_image_data_uri": _signature_image_data_uri(requester_signature),
        "approver_signature_image_data_uri": _signature_image_data_uri(approver_signature),
    }
    html = _env.get_template(TEMPLATE_BY_TYPE[request.type]).render(**context)
    return HTML(string=html, base_url=str(TEMPLATES_DIR)).write_pdf()


def render_asset_dossier_pdf(asset, documents, events, company_name: str | None) -> bytes:
    html = _env.get_template("asset_dossier.html").render(
        asset=asset,
        documents=documents,
        events=events,
        company_name=company_name,
        status_label=ASSET_STATUS_LABELS.get(asset.status, asset.status),
        original_cost_label=(
            f"{asset.original_cost:,.0f} VNĐ" if asset.original_cost is not None else "—"
        ),
    )
    return HTML(string=html, base_url=str(TEMPLATES_DIR)).write_pdf()


def render_asset_export_pdf(assets) -> bytes:
    html = _env.get_template("asset_export.html").render(
        assets=assets,
        status_labels=ASSET_STATUS_LABELS,
        generated_at=datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M"),
    )
    return HTML(string=html, base_url=str(TEMPLATES_DIR)).write_pdf()
