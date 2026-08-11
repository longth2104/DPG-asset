"""Tolerant Excel import (app/services/excel.py) — header-based matching,
not the old strict positional-equality check, so files this app never
exported (renamed/reordered/missing/extra columns, title rows, section
dividers) still import instead of being rejected wholesale."""

import io
from datetime import date, datetime

import openpyxl
import pytest

from app.services.excel import build_asset_xlsx, parse_asset_xlsx


def _wb_bytes(rows: list[list]) -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    for row in rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


class _FakeAsset:
    def __init__(self, **kwargs):
        self.holder_user_id = None
        for k, v in kwargs.items():
            setattr(self, k, v)


def test_own_export_still_imports_round_trip():
    asset = _FakeAsset(
        asset_code="A-1", name="Máy in", category="IT", spec=None, serial_number=None,
        manufacturer=None, manufacture_year=None, original_cost=1000.0, warranty_months=12,
        department="Ban CNTT", holder="Nguyen Van A", location="HN", status="dang_su_dung",
        purchase_source=None, notes=None, year_put_in_use=None, budget_plan_year=None,
        budget_actual_year=None,
    )
    content = build_asset_xlsx([asset])
    rows = parse_asset_xlsx(content)
    assert len(rows) == 1
    assert rows[0]["asset_code"] == "A-1"
    assert rows[0]["name"] == "Máy in"
    assert rows[0]["status"] == "dang_su_dung"
    assert rows[0]["extra_fields"] is None


def test_messy_real_world_sheet_with_title_rows_and_group_header():
    content = _wb_bytes(
        [
            [None, "TẬP ĐOÀN ĐẠT PHƯƠNG"],
            [None, "DANH SÁCH THIẾT BỊ"],
            ["STT", "QUẢN LÝ PHẦN CỨNG"],  # coarse group-title row, should NOT be picked
            [
                "STT", "TÊN VẬT TƯ- THIẾT BỊ", "MÃ TÀI SẢN", "NHÓM THIẾT BỊ",
                "CẤU HÌNH KỸ THUẬT CƠ BẢN", "NĂM SẢN XUẤT", "NĂM SỬ DỤNG",
                "HÃNG SẢN XUẤT", "NGUYỄN GIÁ\n(Đơn vị: VNĐ)", "BẢO HÀNH\n(Thời gian: Tháng)",
                "PHÒNG BAN SỬ DỤNG", "NGƯỜI SỬ DỤNG", "TÌNH TRẠNG", "NƠI MUA", "GHI CHÚ",
                "HĐH", "Microsoft Office",
            ],
            ["I", "Máy tính xách tay Laptop"] + [None] * 15,  # section divider, not an asset
            [
                1, "Laptop Dell XPS 13", "TVP001", "Laptop",
                "i7 32GB 1TB", 2022, datetime(2023, 2, 28), "Dell", 57200000, "12 Tháng",
                "CT HĐQT", "Lương Minh Tuấn", "Đang sử dụng", "Công ty LPL", "ghi chú abc",
                "Windows 11 Pro", "Office 365",
            ],
        ]
    )
    rows = parse_asset_xlsx(content)
    assert len(rows) == 1  # the "I" section-divider row must be skipped
    r = rows[0]
    assert r["asset_code"] == "TVP001"
    assert r["name"] == "Laptop Dell XPS 13"
    assert r["category"] == "Laptop"
    assert r["manufacturer"] == "Dell"
    assert r["manufacture_year"] == 2022
    assert r["year_put_in_use"] == date(2023, 2, 28)
    assert r["original_cost"] == 57200000.0
    assert r["warranty_months"] == 12  # extracted from "12 Tháng"
    assert r["department"] == "CT HĐQT"
    assert r["holder"] == "Lương Minh Tuấn"
    assert r["status"] == "dang_su_dung"
    assert r["purchase_source"] == "Công ty LPL"
    assert r["notes"] == "ghi chú abc"
    # no location/serial_number/holder_email column existed in this sheet at all
    assert "location" not in r
    assert "serial_number" not in r
    # unrecognized software-license columns preserved verbatim, not dropped
    assert r["extra_fields"] == {"HĐH": "Windows 11 Pro", "Microsoft Office": "Office 365"}


def test_reordered_and_renamed_headers_still_match():
    content = _wb_bytes(
        [
            ["Tên tài sản", "Ghi chú", "Mã tài sản"],
            ["Bàn làm việc", "cũ", "B-01"],
        ]
    )
    rows = parse_asset_xlsx(content)
    assert len(rows) == 1
    assert rows[0]["name"] == "Bàn làm việc"
    assert rows[0]["notes"] == "cũ"
    assert rows[0]["asset_code"] == "B-01"


def test_no_recognizable_header_raises():
    content = _wb_bytes([["foo", "bar", "baz"], [1, 2, 3]])
    with pytest.raises(ValueError):
        parse_asset_xlsx(content)
