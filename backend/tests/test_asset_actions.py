"""Admin direct-action endpoint (app/api/asset_actions.py) — same request
model as the normal flow, but no pending step: it's completed immediately."""

import pytest


@pytest.fixture
async def company(make_company):
    return await make_company("C1")


@pytest.fixture
async def admin(make_user, company):
    return await make_user(role="admin", company=company)


async def test_non_admin_forbidden(client, auth_headers, make_user, make_asset, company):
    cbnv = await make_user(role="cbnv", company=company)
    asset = await make_asset(name="Laptop", company=company)
    resp = await client.post(
        "/api/asset-actions",
        json={"type": "transfer", "items": [{"asset_id": str(asset.id)}], "to_department": "Ban CNTT"},
        headers=auth_headers(cbnv),
    )
    assert resp.status_code == 403


async def test_transfer_completes_immediately(client, auth_headers, admin, make_asset, make_user, company):
    recipient = await make_user(role="cbnv", company=company)
    asset = await make_asset(name="Laptop", company=company, status="dang_su_dung")

    resp = await client.post(
        "/api/asset-actions",
        json={
            "type": "transfer",
            "items": [{"asset_id": str(asset.id)}],
            "to_holder_user_id": str(recipient.id),
            "to_department": "Ban CNTT",
        },
        headers=auth_headers(admin),
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["status"] == "completed"
    assert body["origin"] == "direct"
    assert body["decided_by_id"] == str(admin.id)


async def test_acquire_creates_asset_immediately(client, auth_headers, admin):
    resp = await client.post(
        "/api/asset-actions",
        json={"type": "acquire", "items": [{"name": "Ghế mới", "unit_price": 500000}]},
        headers=auth_headers(admin),
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["status"] == "completed"
    assert body["items"][0]["asset_id"] is not None


async def test_liquidate_accepts_sale_price_at_creation(client, auth_headers, admin, make_asset, company):
    asset = await make_asset(name="Máy in cũ", company=company, status="cho_thanh_ly")

    resp = await client.post(
        "/api/asset-actions",
        json={
            "type": "liquidate",
            "items": [{"asset_id": str(asset.id), "approved_sale_price": 300000}],
            "reason": "Hết khấu hao",
        },
        headers=auth_headers(admin),
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["status"] == "completed"
    assert body["items"][0]["approved_sale_price"] == 300000


async def test_request_endpoint_unaffected_by_refactor(client, auth_headers, make_user, make_asset, company):
    requester = await make_user(role="cbnv", company=company)
    asset = await make_asset(name="Bàn", company=company)
    resp = await client.post(
        "/api/requests",
        json={"type": "transfer", "items": [{"asset_id": str(asset.id)}], "to_department": "Ban CNTT"},
        headers=auth_headers(requester),
    )
    assert resp.status_code == 201
    assert resp.json()["status"] == "pending"
    assert resp.json()["origin"] == "ams"
