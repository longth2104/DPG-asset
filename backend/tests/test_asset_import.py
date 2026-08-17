"""Excel import wiring in app/api/assets.py: a holder name with no
holder_email column falls back to matching against the HRIS directory."""

import pytest
from sqlalchemy import select

from app.models.asset import Asset
from app.services.excel import build_asset_xlsx


class _FakeAsset:
    def __init__(self, **kwargs):
        self.holder_user_id = None
        for k, v in kwargs.items():
            setattr(self, k, v)


def _asset_xlsx(name, holder_name):
    asset = _FakeAsset(
        asset_code=None, name=name, category=None, spec=None,
        serial_number=None, manufacturer=None, manufacture_year=None, original_cost=None,
        warranty_months=None, department=None, holder=holder_name, location=None,
        status="dang_su_dung", purchase_source=None, notes=None, year_put_in_use=None,
        budget_plan_year=None, budget_actual_year=None,
    )
    return build_asset_xlsx([asset])


@pytest.fixture
async def company(make_company):
    return await make_company("C1")


async def test_import_links_holder_by_name_via_hris(
    client, auth_headers, make_user, company, monkeypatch, db_session
):
    manager = await make_user(role="phong_thiet_bi", company=company)
    holder = await make_user(role="cbnv", company=company, email="lmtuan@test.local")

    async def fake_search_employees(query=None):
        return [{"name": "Lương Minh Tuấn", "email": holder.email, "emp_code": "E001"}]

    monkeypatch.setattr("app.api.assets.search_employees", fake_search_employees)

    content = _asset_xlsx("Laptop có chủ", "Lương Minh Tuấn")
    resp = await client.post(
        "/api/assets/import",
        files={"file": ("assets.xlsx", content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers=auth_headers(manager),
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["imported"] == 1

    result = await db_session.execute(select(Asset).where(Asset.name == "Laptop có chủ"))
    asset = result.scalars().first()
    assert asset is not None
    assert asset.holder == "Lương Minh Tuấn"
    assert asset.holder_user_id == holder.id


async def test_import_leaves_holder_as_text_when_name_ambiguous(
    client, auth_headers, make_user, company, monkeypatch, db_session
):
    manager = await make_user(role="phong_thiet_bi", company=company)

    async def fake_search_employees(query=None):
        return [
            {"name": "Nguyễn Văn A", "email": "a1@test.local"},
            {"name": "Nguyễn Văn A", "email": "a2@test.local"},
        ]

    monkeypatch.setattr("app.api.assets.search_employees", fake_search_employees)

    content = _asset_xlsx("Laptop mơ hồ", "Nguyễn Văn A")
    resp = await client.post(
        "/api/assets/import",
        files={"file": ("assets.xlsx", content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers=auth_headers(manager),
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["imported"] == 1

    result = await db_session.execute(select(Asset).where(Asset.name == "Laptop mơ hồ"))
    asset = result.scalars().first()
    assert asset is not None
    assert asset.holder == "Nguyễn Văn A"
    assert asset.holder_user_id is None


async def test_import_when_hris_unreachable_keeps_holder_as_text(
    client, auth_headers, make_user, company, monkeypatch, db_session
):
    manager = await make_user(role="phong_thiet_bi", company=company)

    async def failing_search_employees(query=None):
        raise RuntimeError("HRIS is not configured")

    monkeypatch.setattr("app.api.assets.search_employees", failing_search_employees)

    content = _asset_xlsx("Laptop không HRIS", "Ai Đó")
    resp = await client.post(
        "/api/assets/import",
        files={"file": ("assets.xlsx", content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers=auth_headers(manager),
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["imported"] == 1

    result = await db_session.execute(select(Asset).where(Asset.name == "Laptop không HRIS"))
    asset = result.scalars().first()
    assert asset is not None
    assert asset.holder == "Ai Đó"
    assert asset.holder_user_id is None
