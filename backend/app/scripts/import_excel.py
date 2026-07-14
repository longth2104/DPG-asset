"""One-shot import of the `TB-VP` sheet (active office/IT equipment) from the
real company registry into the `assets` table, per docs/feature-spec.md §8/§9.

Only `TB-VP` is imported in this increment — `ĐPHA`/`TB-Bỏ`/`TH` are out of
scope (no multi-entity or software-license modeling yet, per the approved
build-increment plan).

Run with: docker compose exec backend python -m app.scripts.import_excel
"""

import asyncio
import re
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path

import openpyxl

from app.core.database import AsyncSessionLocal
from app.models.asset import Asset
from app.models.asset_event import AssetEvent

# Imported for their mapper-registration side effect only — Asset/AssetEvent's
# FKs (created_by -> users.id) need every referenced table registered on
# Base.metadata before the ORM can resolve them at flush time.
from app.models import document as _document  # noqa: F401
from app.models import user as _user  # noqa: F401

XLSX_PATH = Path(__file__).resolve().parent.parent / "data" / "DS-Thiet-bi-VP-2025.xlsx"
SHEET_NAME = "TB-VP"
HEADER_ROW = 7  # 1-indexed row containing column headers in this sheet

STATUS_MAP = {
    "đang sử dụng": "dang_su_dung",
    "đang sửa chữa": "dang_sua_chua",
    "chờ thanh lý": "cho_thanh_ly",
    "đã thanh lý": "da_thanh_ly",
}


def _excel_serial_to_date(value) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        serial = float(value)
    except (TypeError, ValueError):
        return None
    return date(1899, 12, 30) + timedelta(days=serial)


def _parse_warranty_months(value) -> int | None:
    if not value:
        return None
    match = re.search(r"\d+", str(value))
    return int(match.group()) if match else None


def _map_status(value) -> str:
    return STATUS_MAP.get(str(value or "").strip().lower(), "dang_su_dung")


def _generate_asset_code() -> str:
    return f"A-{uuid.uuid4().hex[:8].upper()}"


def _cell(row, index):
    value = row[index] if index < len(row) else None
    if isinstance(value, str):
        value = value.strip()
    return value or None


async def main() -> None:
    if not XLSX_PATH.exists():
        raise SystemExit(f"Source workbook not found at {XLSX_PATH}")

    wb = openpyxl.load_workbook(XLSX_PATH, data_only=True)
    ws = wb[SHEET_NAME]

    imported = 0
    skipped = 0

    async with AsyncSessionLocal() as db:
        for row in ws.iter_rows(min_row=HEADER_ROW + 1, values_only=True):
            stt = row[0]
            name = _cell(row, 1)
            if not isinstance(stt, (int, float)) or not name:
                skipped += 1  # section header (roman numeral) or blank row
                continue

            asset_code = _cell(row, 2) or _generate_asset_code()
            category = _cell(row, 3)
            spec = _cell(row, 4)
            serial_number = _cell(row, 5)
            manufacture_year = int(row[6]) if isinstance(row[6], (int, float)) else None
            year_put_in_use = _excel_serial_to_date(row[7])
            manufacturer = _cell(row, 8)
            original_cost = row[9] if isinstance(row[9], (int, float)) else None
            warranty_months = _parse_warranty_months(_cell(row, 10))
            repair_desc = _cell(row, 11)
            repair_cost = row[12] if isinstance(row[12], (int, float)) else None
            department = _cell(row, 13)
            holder = _cell(row, 14)
            status_text = _cell(row, 15)
            budget_plan_year = int(row[16]) if isinstance(row[16], (int, float)) else None
            budget_actual_year = None  # THỰC HIỆN NS NĂM is text ("Đã mua"/"Chưa mua"), not a year
            usage_history = _cell(row, 18)
            purchase_source = _cell(row, 19)
            note_text = _cell(row, 20)

            notes_parts = []
            if repair_desc:
                notes_parts.append(f"Thay thế/sửa chữa: {repair_desc}")
            if repair_cost:
                notes_parts.append(f"Chi phí sửa chữa: {repair_cost:,.0f}đ")
            if note_text:
                notes_parts.append(note_text)

            asset = Asset(
                asset_code=asset_code,
                name=name,
                category=category,
                spec=spec,
                serial_number=serial_number,
                manufacturer=manufacturer,
                manufacture_year=manufacture_year,
                year_put_in_use=year_put_in_use,
                original_cost=original_cost,
                warranty_months=warranty_months,
                legal_entity="Đạt Phương",
                department=department,
                holder=holder,
                location="Văn phòng Công ty",
                status=_map_status(status_text),
                domain="b",
                budget_plan_year=budget_plan_year,
                budget_actual_year=budget_actual_year,
                purchase_source=purchase_source,
                notes=" | ".join(notes_parts) or None,
            )
            db.add(asset)
            await db.flush()

            db.add(
                AssetEvent(
                    asset_id=asset.id,
                    type="created",
                    note=f"Nhập từ DS-Thiết bị VP 2025.xlsx (sheet {SHEET_NAME})",
                )
            )
            if usage_history:
                db.add(
                    AssetEvent(
                        asset_id=asset.id,
                        type="note",
                        note=f"Lịch sử sử dụng (nhập liệu): {usage_history}",
                    )
                )

            imported += 1

        await db.commit()

    print(f"Imported {imported} assets, skipped {skipped} non-data rows")


if __name__ == "__main__":
    asyncio.run(main())
