"""Asset.purchase_date / Asset.project (docs/cycle.md) and propagating a
named project onto the asset when a transfer's scope is "project"."""

import pytest


@pytest.fixture
async def company(make_company):
    return await make_company("C1")


async def test_create_asset_with_purchase_date_and_project(client, auth_headers, make_user, company):
    manager = await make_user(role="phong_thiet_bi", company=company)
    resp = await client.post(
        "/api/assets",
        json={"name": "Máy khoan", "purchase_date": "2026-01-15", "project": "Công trình Hội An"},
        headers=auth_headers(manager),
    )
    assert resp.status_code == 201, resp.text

    detail = await client.get(f"/api/assets/{resp.json()['id']}", headers=auth_headers(manager))
    assert detail.json()["purchase_date"] == "2026-01-15"
    assert detail.json()["project"] == "Công trình Hội An"


async def test_update_asset_project(client, auth_headers, make_user, make_asset, company):
    manager = await make_user(role="phong_thiet_bi", company=company)
    asset = await make_asset(name="Máy ủi", company=company)

    resp = await client.put(
        f"/api/assets/{asset.id}", json={"project": "Công trình Đà Nẵng"}, headers=auth_headers(manager)
    )
    assert resp.status_code == 200, resp.text

    # response_model=AssetListItem on this endpoint doesn't carry `project`
    # (only the AssetOut detail response does) — verify via GET instead.
    detail = await client.get(f"/api/assets/{asset.id}", headers=auth_headers(manager))
    assert detail.json()["project"] == "Công trình Đà Nẵng"


async def test_transfer_with_project_scope_propagates_project_to_asset(
    client, auth_headers, make_user, make_asset, company
):
    requester = await make_user(role="cbnv", company=company)
    approver = await make_user(role="phong_thiet_bi", company=company)
    asset = await make_asset(name="Máy trộn bê tông", company=company)

    create = await client.post(
        "/api/requests",
        json={
            "type": "transfer",
            "scope": "project",
            "project": "Công trình Quảng Nam",
            "items": [{"asset_id": str(asset.id)}],
        },
        headers=auth_headers(requester),
    )
    assert create.status_code == 201, create.text
    request_id = create.json()["id"]
    assert create.json()["project"] == "Công trình Quảng Nam"

    decide = await client.post(
        f"/api/requests/{request_id}/decide", json={"approve": True}, headers=auth_headers(approver)
    )
    assert decide.status_code == 200, decide.text

    detail = await client.get(f"/api/assets/{asset.id}", headers=auth_headers(requester))
    assert detail.json()["project"] == "Công trình Quảng Nam"
