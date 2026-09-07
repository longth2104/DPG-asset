"""POST /api/assets/link-holders-hris — retroactively links existing
free-text `holder` names to real accounts via HRIS, admin-only."""

import pytest

from app.models.asset import Asset


@pytest.fixture
async def company(make_company):
    return await make_company("C1")


async def test_non_admin_forbidden(client, auth_headers, make_user, company):
    manager = await make_user(role="phong_thiet_bi", company=company)
    resp = await client.post("/api/assets/link-holders-hris", headers=auth_headers(manager))
    assert resp.status_code == 403


async def test_links_unique_name_match(
    client, auth_headers, make_user, make_asset, company, monkeypatch, db_session
):
    admin = await make_user(role="admin", company=company)
    holder = await make_user(role="cbnv", company=company, email="hai.nguyen@datphuong.vn")
    asset = await make_asset(name="Bàn phím", company=company, holder="Nguyễn Thanh Hải")

    async def fake_search_employees(query=None):
        return [{"name": "Nguyễn Thanh Hải", "email": holder.email, "emp_code": "E100"}]

    monkeypatch.setattr("app.api.assets.search_employees", fake_search_employees)

    resp = await client.post("/api/assets/link-holders-hris", headers=auth_headers(admin))
    assert resp.status_code == 200, resp.text
    assert resp.json() == {"linked": 1, "unmatched": 0}

    await db_session.refresh(asset)
    assert asset.holder_user_id == holder.id


async def test_leaves_ambiguous_and_no_match_unlinked(
    client, auth_headers, make_user, make_asset, company, monkeypatch, db_session
):
    admin = await make_user(role="admin", company=company)
    await make_asset(name="Máy in 1", company=company, holder="Nguyễn Văn A")
    await make_asset(name="Máy in 2", company=company, holder="Không ai biết")

    async def fake_search_employees(query=None):
        return [
            {"name": "Nguyễn Văn A", "email": "a1@datphuong.vn"},
            {"name": "Nguyễn Văn A", "email": "a2@datphuong.vn"},
        ]

    monkeypatch.setattr("app.api.assets.search_employees", fake_search_employees)

    resp = await client.post("/api/assets/link-holders-hris", headers=auth_headers(admin))
    assert resp.status_code == 200, resp.text
    assert resp.json() == {"linked": 0, "unmatched": 2}


async def test_skips_assets_already_linked(
    client, auth_headers, make_user, make_asset, company, monkeypatch, db_session
):
    admin = await make_user(role="admin", company=company)
    holder = await make_user(role="cbnv", company=company, email="already@datphuong.vn")
    await make_asset(name="Đã liên kết", company=company, holder="Ai đó", holder_user_id=holder.id)

    called = False

    async def fake_search_employees(query=None):
        nonlocal called
        called = True
        return []

    monkeypatch.setattr("app.api.assets.search_employees", fake_search_employees)

    resp = await client.post("/api/assets/link-holders-hris", headers=auth_headers(admin))
    assert resp.status_code == 200, resp.text
    assert resp.json() == {"linked": 0, "unmatched": 0}


async def test_hris_unavailable_returns_503(client, auth_headers, make_user, company, monkeypatch):
    admin = await make_user(role="admin", company=company)

    async def failing_search_employees(query=None):
        raise RuntimeError("HRIS is not configured")

    monkeypatch.setattr("app.api.assets.search_employees", failing_search_employees)

    resp = await client.post("/api/assets/link-holders-hris", headers=auth_headers(admin))
    assert resp.status_code == 503
