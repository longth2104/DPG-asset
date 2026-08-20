"""Company (holding-hierarchy) handling on assets — docs/field.md:
compulsory going forward, defaulting sensibly rather than ever being left
unset, both for manual create/edit and Excel import."""

import pytest
from sqlalchemy import select

from app.models.asset import Asset
from app.services.excel import build_asset_xlsx


class _FakeAsset:
    def __init__(self, **kwargs):
        self.holder_user_id = None
        self.company_id = None
        for k, v in kwargs.items():
            setattr(self, k, v)


def _asset_xlsx(name, company_text):
    asset = _FakeAsset(
        asset_code=None, name=name, category=None, spec=None,
        serial_number=None, manufacturer=None, manufacture_year=None, original_cost=None,
        warranty_months=None, department=None, holder=None, location=None,
        status="dang_su_dung", purchase_source=None, notes=None, year_put_in_use=None,
        budget_plan_year=None, budget_actual_year=None,
    )
    # build_asset_xlsx writes the "company" column via company_codes keyed
    # by company_id (None here, since this fake asset has no real one) —
    # not a plain attribute, so route the test's desired cell text through
    # that lookup instead of setting a (unused) `.company` attribute.
    return build_asset_xlsx([asset], company_codes={None: company_text})


@pytest.fixture
async def company_a(make_company):
    return await make_company("HOLD-A")


@pytest.fixture
async def company_b(make_company):
    return await make_company("HOLD-B")


async def test_create_asset_defaults_company_to_own(client, auth_headers, make_user, company_a):
    manager = await make_user(role="phong_thiet_bi", company=company_a)
    resp = await client.post(
        "/api/assets", json={"name": "Máy chiếu"}, headers=auth_headers(manager)
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["company_id"] == str(company_a.id)


async def test_create_asset_honors_explicit_company(client, auth_headers, make_user, company_a, company_b):
    manager = await make_user(role="phong_thiet_bi", company=company_a)
    resp = await client.post(
        "/api/assets",
        json={"name": "Máy chiếu", "company_id": str(company_b.id)},
        headers=auth_headers(manager),
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["company_id"] == str(company_b.id)


async def test_update_asset_can_change_company_and_add_extra_fields(
    client, auth_headers, make_user, make_asset, company_a, company_b
):
    manager = await make_user(role="phong_thiet_bi", company=company_a)
    asset = await make_asset(name="Máy in", company=company_a)

    resp = await client.put(
        f"/api/assets/{asset.id}",
        json={"company_id": str(company_b.id), "extra_fields": {"Ghi chú thêm": "test"}},
        headers=auth_headers(manager),
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["company_id"] == str(company_b.id)


async def test_import_resolves_company_by_code(
    client, auth_headers, make_user, company_a, company_b, db_session
):
    manager = await make_user(role="phong_thiet_bi", company=company_a)
    content = _asset_xlsx("Laptop công ty B", company_b.code)

    resp = await client.post(
        "/api/assets/import",
        files={"file": ("assets.xlsx", content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers=auth_headers(manager),
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["imported"] == 1

    # Queried directly, not via GET /api/assets as this manager — the asset
    # correctly landed in company_b, outside company_a's scope, so the
    # manager themselves wouldn't see it in their own asset list.
    result = await db_session.execute(select(Asset).where(Asset.name == "Laptop công ty B"))
    asset = result.scalars().first()
    assert asset is not None
    assert asset.company_id == company_b.id


async def test_import_falls_back_to_default_company_when_unmatched(
    client, auth_headers, make_user, company_a, company_b, db_session
):
    manager = await make_user(role="phong_thiet_bi", company=company_a)
    content = _asset_xlsx("Laptop không rõ công ty", "Công ty không tồn tại")

    resp = await client.post(
        "/api/assets/import",
        data={"default_company_id": str(company_b.id)},
        files={"file": ("assets.xlsx", content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers=auth_headers(manager),
    )
    assert resp.status_code == 200, resp.text

    result = await db_session.execute(select(Asset).where(Asset.name == "Laptop không rõ công ty"))
    asset = result.scalars().first()
    assert asset is not None
    assert asset.company_id == company_b.id


async def test_import_falls_back_to_own_company_with_no_default_given(
    client, auth_headers, make_user, company_a, db_session
):
    manager = await make_user(role="phong_thiet_bi", company=company_a)
    content = _asset_xlsx("Laptop mặc định", None)

    resp = await client.post(
        "/api/assets/import",
        files={"file": ("assets.xlsx", content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers=auth_headers(manager),
    )
    assert resp.status_code == 200, resp.text

    result = await db_session.execute(select(Asset).where(Asset.name == "Laptop mặc định"))
    asset = result.scalars().first()
    assert asset is not None
    assert asset.company_id == company_a.id
