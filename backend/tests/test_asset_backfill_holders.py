"""POST /api/assets/backfill-holders — retroactively links existing
free-text `holder` names to real accounts via HRIS (asset-manager)."""

import pytest


@pytest.fixture
async def company(make_company):
    return await make_company("C1")


async def test_non_asset_manager_forbidden(client, auth_headers, make_user, company):
    cbnv = await make_user(role="cbnv", company=company)
    resp = await client.post("/api/assets/backfill-holders", headers=auth_headers(cbnv))
    assert resp.status_code == 403


async def test_links_unique_name_match(
    client, auth_headers, make_user, make_asset, company, monkeypatch, db_session
):
    manager = await make_user(role="phong_thiet_bi", company=company)
    holder = await make_user(role="cbnv", company=company, email="hai.nguyen@datphuong.vn")
    asset = await make_asset(name="Bàn phím", company=company, holder="Nguyễn Thanh Hải")

    async def fake_search_employees(query=None):
        return [{"name": "Nguyễn Thanh Hải", "email": holder.email, "emp_code": "E100"}]

    monkeypatch.setattr("app.api.assets.search_employees", fake_search_employees)

    resp = await client.post("/api/assets/backfill-holders", headers=auth_headers(manager))
    assert resp.status_code == 200, resp.text
    assert resp.json() == {"scanned": 1, "linked": 1, "unresolved": 0}

    await db_session.refresh(asset)
    assert asset.holder_user_id == holder.id


async def test_leaves_ambiguous_and_no_match_unlinked(
    client, auth_headers, make_user, make_asset, company, monkeypatch
):
    manager = await make_user(role="phong_thiet_bi", company=company)
    await make_asset(name="Máy in 1", company=company, holder="Nguyễn Văn A")
    await make_asset(name="Máy in 2", company=company, holder="Không ai biết")

    async def fake_search_employees(query=None):
        return [
            {"name": "Nguyễn Văn A", "email": "a1@datphuong.vn"},
            {"name": "Nguyễn Văn A", "email": "a2@datphuong.vn"},
        ]

    monkeypatch.setattr("app.api.assets.search_employees", fake_search_employees)

    resp = await client.post("/api/assets/backfill-holders", headers=auth_headers(manager))
    assert resp.status_code == 200, resp.text
    assert resp.json() == {"scanned": 2, "linked": 0, "unresolved": 2}


async def test_skips_assets_already_linked_or_without_holder(
    client, auth_headers, make_user, make_asset, company, monkeypatch
):
    manager = await make_user(role="phong_thiet_bi", company=company)
    holder = await make_user(role="cbnv", company=company, email="already@datphuong.vn")
    await make_asset(name="Đã liên kết", company=company, holder="Ai đó", holder_user_id=holder.id)
    await make_asset(name="Không có người giữ", company=company, holder=None)

    async def fake_search_employees(query=None):
        return []

    monkeypatch.setattr("app.api.assets.search_employees", fake_search_employees)

    resp = await client.post("/api/assets/backfill-holders", headers=auth_headers(manager))
    assert resp.status_code == 200, resp.text
    assert resp.json() == {"scanned": 0, "linked": 0, "unresolved": 0}


async def test_hris_unavailable_returns_503(client, auth_headers, make_user, company, monkeypatch):
    manager = await make_user(role="phong_thiet_bi", company=company)

    async def failing_search_employees(query=None):
        raise RuntimeError("HRIS is not configured")

    monkeypatch.setattr("app.api.assets.search_employees", failing_search_employees)

    resp = await client.post("/api/assets/backfill-holders", headers=auth_headers(manager))
    assert resp.status_code == 503
