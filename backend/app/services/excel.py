import io

import openpyxl
from openpyxl.utils import get_column_letter

from app.models.asset import ASSET_STATUS_LABELS

# Single canonical column mapping used for both export and import, per
# docs/feature-spec.md §9 ("one canonical schema, adapters" rather than
# N special-case scripts). Column order here is also the .xlsx column order.
COLUMNS = [
    ("asset_code", "Mã tài sản"),
    ("name", "Tên tài sản"),
    ("category", "Nhóm thiết bị"),
    ("spec", "Cấu hình kỹ thuật"),
    ("serial_number", "Số Serial"),
    ("manufacturer", "Hãng sản xuất"),
    ("manufacture_year", "Năm sản xuất"),
    ("original_cost", "Nguyên giá (VNĐ)"),
    ("warranty_months", "Bảo hành (tháng)"),
    ("department", "Phòng ban"),
    ("holder", "Người sử dụng"),
    ("location", "Vị trí"),
    ("status", "Tình trạng"),
    ("purchase_source", "Nơi mua"),
    ("notes", "Ghi chú"),
    # Appended rather than inserted alongside "holder" — keeps every existing
    # column's position stable so already-exported .xlsx files still import.
    # Not an Asset column: resolved to/from holder_user_id at the API layer
    # (see assets.py import/export), not passed straight through like the
    # other fields here.
    ("holder_email", "Email người sử dụng"),
]

_STATUS_LABEL_TO_CODE = {label.lower(): code for code, label in ASSET_STATUS_LABELS.items()}


def build_asset_xlsx(assets, holder_emails: dict | None = None) -> bytes:
    """`holder_emails` maps Asset.holder_user_id -> email, resolved by the
    caller (assets.py) since `holder_email` isn't a real Asset column."""
    holder_emails = holder_emails or {}
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Danh sách tài sản"

    for col_idx, (_, label) in enumerate(COLUMNS, start=1):
        ws.cell(row=1, column=col_idx, value=label)

    for row_idx, asset in enumerate(assets, start=2):
        for col_idx, (field, _) in enumerate(COLUMNS, start=1):
            if field == "holder_email":
                value = holder_emails.get(asset.holder_user_id)
            else:
                value = getattr(asset, field)
                if field == "status":
                    value = ASSET_STATUS_LABELS.get(value, value)
                elif field == "original_cost" and value is not None:
                    value = float(value)
            ws.cell(row=row_idx, column=col_idx, value=value)

    for col_idx in range(1, len(COLUMNS) + 1):
        ws.column_dimensions[get_column_letter(col_idx)].width = 20

    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


def parse_asset_xlsx(content: bytes) -> list[dict]:
    """Parses an uploaded workbook using the same column mapping as export.
    Returns one dict per data row, keyed by Asset field name. Raises
    ValueError if the header row doesn't match the expected column labels.
    """
    wb = openpyxl.load_workbook(io.BytesIO(content), data_only=True)
    ws = wb.active

    header = [cell.value for cell in next(ws.iter_rows(min_row=1, max_row=1))]
    expected = [label for _, label in COLUMNS]
    if header[: len(expected)] != expected:
        raise ValueError(
            "Cột không khớp mẫu xuất — vui lòng dùng file được xuất từ hệ thống "
            "hoặc sắp xếp đúng thứ tự cột."
        )

    rows = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not any(row):
            continue
        record = {}
        for col_idx, (field, _) in enumerate(COLUMNS):
            value = row[col_idx] if col_idx < len(row) else None
            if isinstance(value, str):
                value = value.strip() or None
            if field == "status":
                value = _STATUS_LABEL_TO_CODE.get(str(value or "").strip().lower(), "dang_su_dung")
            elif field in ("manufacture_year", "warranty_months") and value is not None:
                value = int(value) if isinstance(value, (int, float)) else None
            elif field == "original_cost" and not isinstance(value, (int, float)):
                value = None
            record[field] = value
        rows.append(record)
    return rows
