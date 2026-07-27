import base64
import hashlib
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML

from app.api.upload import get_object_bytes
from app.models.asset import ASSET_STATUS_LABELS
from app.models.request import Request, RequestSignature

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"

_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html"]),
)

# Form code / process reference per docs/feature-spec.md §1 traceability
# matrix — same required fields/signers as the paper BM form, clean layout
# rather than a pixel-faithful replica (scope decision for this increment).
FORM_META = {
    "transfer": {
        "form_code": "BM03",
        "process_code": "QT01 — Yêu cầu / điều động thiết bị",
        "title": "Biên bản bàn giao / điều động tài sản",
        "template": "request_transfer.html",
    },
    "acquire": {
        "form_code": "BM01",
        "process_code": "QT03 — Mua sắm tài sản cố định",
        "title": "Đề xuất mua sắm tài sản",
        "template": "request_acquire.html",
    },
    "liquidate": {
        "form_code": "BM01",
        "process_code": "QT04 — Thanh lý tài sản cố định",
        "title": "Đề xuất thanh lý tài sản",
        "template": "request_liquidate.html",
    },
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


def _user_label(user) -> str | None:
    if not user:
        return None
    return user.full_name or user.email


def _signature_image_data_uri(signature: RequestSignature | None) -> str | None:
    if not signature or not signature.signature_image_url:
        return None
    content = get_object_bytes(signature.signature_image_url)
    ext = signature.signature_image_url.rsplit(".", 1)[-1].lower()
    mime = "image/jpeg" if ext in ("jpg", "jpeg") else "image/png"
    return f"data:{mime};base64,{base64.b64encode(content).decode()}"


def content_hash_for(request: Request) -> str:
    """Hashes the request's user-editable fields at signing time — per
    docs/feature-spec.md §7, a signed document's content is then immutable;
    corrections require filing a new request, not editing this one."""
    fields = [
        request.type, request.asset_id, request.scope,
        request.from_department, request.to_department,
        request.from_location, request.to_location,
        request.justification, request.estimated_cost,
        request.reason, request.condition_note,
        request.status, request.decision_note,
    ]
    raw = "|".join("" if f is None else str(f) for f in fields)
    return hashlib.sha256(raw.encode()).hexdigest()


def render_request_pdf(
    *,
    request: Request,
    asset,
    requester,
    approver,
    from_holder,
    to_holder,
    signatures: list[RequestSignature],
) -> bytes:
    meta = FORM_META[request.type]
    requester_signature = next((s for s in signatures if s.role_in_flow == "requester"), None)
    approver_signature = next((s for s in signatures if s.role_in_flow == "approver"), None)

    context = {
        "request": request,
        "asset": asset,
        "form_code": meta["form_code"],
        "process_code": meta["process_code"],
        "title": meta["title"],
        "requester_name": _user_label(requester) or "—",
        "approver_name": _user_label(approver),
        "status_label": REQUEST_STATUS_LABELS.get(request.status, request.status),
        "scope_label": SCOPE_LABELS.get(request.scope, request.scope or "—"),
        "from_holder_name": _user_label(from_holder),
        "to_holder_name": _user_label(to_holder),
        "estimated_cost_label": (
            f"{request.estimated_cost:,.0f} VNĐ" if request.estimated_cost is not None else "—"
        ),
        "requester_signature": requester_signature,
        "approver_signature": approver_signature,
        "requester_signature_image_data_uri": _signature_image_data_uri(requester_signature),
        "approver_signature_image_data_uri": _signature_image_data_uri(approver_signature),
    }
    html = _env.get_template(meta["template"]).render(**context)
    return HTML(string=html, base_url=str(TEMPLATES_DIR)).write_pdf()


def render_asset_export_pdf(assets) -> bytes:
    html = _env.get_template("asset_export.html").render(
        assets=assets,
        status_labels=ASSET_STATUS_LABELS,
        generated_at=datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M"),
    )
    return HTML(string=html, base_url=str(TEMPLATES_DIR)).write_pdf()
