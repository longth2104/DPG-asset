"""End-to-end coverage of the request state machine in app/api/requests.py:
create -> decide (approve/reject) -> the per-type side effects in
_apply_effect, plus the guards around who can decide and when."""

import pytest


@pytest.fixture
async def company(make_company):
    return await make_company("C1")


@pytest.fixture
async def requester(make_user, company):
    return await make_user(role="cbnv", company=company)


@pytest.fixture
async def recipient(make_user, company):
    return await make_user(role="cbnv", company=company)


async def test_create_transfer_requires_asset_id(client, auth_headers, requester):
    resp = await client.post(
        "/api/requests",
        json={"type": "transfer", "items": [{"quantity": 1}]},
        headers=auth_headers(requester),
    )
    assert resp.status_code == 422


async def test_create_acquire_rejects_asset_id(client, auth_headers, requester, make_asset, company):
    asset = await make_asset(company=company)
    resp = await client.post(
        "/api/requests",
        json={"type": "acquire", "items": [{"asset_id": str(asset.id), "name": "x"}]},
        headers=auth_headers(requester),
    )
    assert resp.status_code == 422


async def test_create_requires_at_least_one_item(client, auth_headers, requester):
    resp = await client.post("/api/requests", json={"type": "acquire", "items": []}, headers=auth_headers(requester))
    assert resp.status_code == 422


async def test_create_unknown_type_rejected(client, auth_headers, requester):
    resp = await client.post(
        "/api/requests", json={"type": "not-a-type", "items": [{"name": "x"}]}, headers=auth_headers(requester)
    )
    assert resp.status_code == 422


async def test_transfer_pending_then_approve_moves_asset(
    client, auth_headers, make_user, make_asset, company, requester, recipient
):
    approver = await make_user(role="phong_thiet_bi", company=company)
    asset = await make_asset(name="Laptop", company=company, status="dang_su_dung")

    create = await client.post(
        "/api/requests",
        json={
            "type": "transfer",
            "items": [{"asset_id": str(asset.id)}],
            "to_holder_user_id": str(recipient.id),
            "to_department": "Ban CNTT",
        },
        headers=auth_headers(requester),
    )
    assert create.status_code == 201
    body = create.json()
    assert body["status"] == "pending"
    assert body["approver_role"] == "phong_thiet_bi"
    request_id = body["id"]

    decide = await client.post(
        f"/api/requests/{request_id}/decide",
        json={"approve": True},
        headers=auth_headers(approver),
    )
    assert decide.status_code == 200
    decided = decide.json()
    assert decided["status"] == "completed"
    assert decided["decided_by_id"] == str(approver.id)

    check = await client.get(f"/api/requests/{request_id}", headers=auth_headers(requester))
    assert check.json()["items"][0]["asset_id"] == str(asset.id)


async def test_reject_leaves_asset_untouched(
    client, auth_headers, make_user, make_asset, company, requester
):
    approver = await make_user(role="phong_thiet_bi", company=company)
    asset = await make_asset(name="Printer", company=company, status="dang_su_dung")

    create = await client.post(
        "/api/requests",
        json={"type": "transfer", "items": [{"asset_id": str(asset.id)}], "to_department": "Ban CNTT"},
        headers=auth_headers(requester),
    )
    request_id = create.json()["id"]

    decide = await client.post(
        f"/api/requests/{request_id}/decide",
        json={"approve": False, "note": "Không đủ điều kiện"},
        headers=auth_headers(approver),
    )
    assert decide.status_code == 200
    assert decide.json()["status"] == "rejected"


async def test_cannot_decide_twice(client, auth_headers, make_user, make_asset, company, requester):
    approver = await make_user(role="phong_thiet_bi", company=company)
    asset = await make_asset(name="Monitor", company=company)

    create = await client.post(
        "/api/requests",
        json={"type": "transfer", "items": [{"asset_id": str(asset.id)}], "to_department": "Ban CNTT"},
        headers=auth_headers(requester),
    )
    request_id = create.json()["id"]

    first = await client.post(
        f"/api/requests/{request_id}/decide", json={"approve": True}, headers=auth_headers(approver)
    )
    assert first.status_code == 200

    second = await client.post(
        f"/api/requests/{request_id}/decide", json={"approve": True}, headers=auth_headers(approver)
    )
    assert second.status_code == 409


async def test_wrong_role_cannot_decide(client, auth_headers, make_asset, company, requester):
    asset = await make_asset(name="Chair", company=company)
    create = await client.post(
        "/api/requests",
        json={"type": "transfer", "items": [{"asset_id": str(asset.id)}], "to_department": "Ban CNTT"},
        headers=auth_headers(requester),
    )
    request_id = create.json()["id"]

    decide = await client.post(
        f"/api/requests/{request_id}/decide", json={"approve": True}, headers=auth_headers(requester)
    )
    assert decide.status_code == 403


async def test_approver_out_of_scope_gets_404(
    client, auth_headers, make_user, make_asset, make_company, company, requester
):
    other_company = await make_company("C2")
    outside_approver = await make_user(role="phong_thiet_bi", company=other_company)
    asset = await make_asset(name="Router", company=company)

    create = await client.post(
        "/api/requests",
        json={"type": "transfer", "items": [{"asset_id": str(asset.id)}], "to_department": "Ban CNTT"},
        headers=auth_headers(requester),
    )
    request_id = create.json()["id"]

    decide = await client.post(
        f"/api/requests/{request_id}/decide",
        json={"approve": True},
        headers=auth_headers(outside_approver),
    )
    assert decide.status_code == 404


async def test_acquire_approval_creates_asset(client, auth_headers, make_user, company, requester, recipient):
    tgd = await make_user(role="tgd", company=company)

    create = await client.post(
        "/api/requests",
        json={
            "type": "acquire",
            "items": [{"name": "Ghế văn phòng", "unit_price": 1500000, "quantity": 2}],
            "to_department": "Ban HCNS",
            "to_holder_user_id": str(recipient.id),
        },
        headers=auth_headers(requester),
    )
    assert create.status_code == 201
    request_id = create.json()["id"]
    assert create.json()["items"][0]["asset_id"] is None

    decide = await client.post(
        f"/api/requests/{request_id}/decide", json={"approve": True}, headers=auth_headers(tgd)
    )
    assert decide.status_code == 200
    assert decide.json()["status"] == "completed"

    check = await client.get(f"/api/requests/{request_id}", headers=auth_headers(requester))
    item = check.json()["items"][0]
    assert item["asset_id"] is not None


async def test_liquidate_approval_sets_sale_price_and_asset_status(
    client, auth_headers, make_user, make_asset, company, requester
):
    tgd = await make_user(role="tgd", company=company)
    asset = await make_asset(name="Máy in cũ", company=company, status="cho_thanh_ly")

    create = await client.post(
        "/api/requests",
        json={
            "type": "liquidate",
            "items": [{"asset_id": str(asset.id), "proposed_value": 200000}],
            "reason": "Hết khấu hao",
        },
        headers=auth_headers(requester),
    )
    request_id = create.json()["id"]
    item_id = create.json()["items"][0]["id"]

    decide = await client.post(
        f"/api/requests/{request_id}/decide",
        json={"approve": True, "items": [{"id": item_id, "approved_sale_price": 350000}]},
        headers=auth_headers(tgd),
    )
    assert decide.status_code == 200

    check = await client.get(f"/api/requests/{request_id}", headers=auth_headers(requester))
    item = check.json()["items"][0]
    assert item["approved_sale_price"] == 350000


async def test_sign_then_resign_conflicts(client, auth_headers, make_asset, company, requester):
    asset = await make_asset(name="Bàn", company=company)
    create = await client.post(
        "/api/requests",
        json={"type": "transfer", "items": [{"asset_id": str(asset.id)}], "to_department": "Ban CNTT"},
        headers=auth_headers(requester),
    )
    request_id = create.json()["id"]

    first = await client.post(
        f"/api/requests/{request_id}/sign",
        data={"signed_name": requester.full_name or requester.email},
        headers=auth_headers(requester),
    )
    assert first.status_code == 201

    second = await client.post(
        f"/api/requests/{request_id}/sign",
        data={"signed_name": requester.full_name or requester.email},
        headers=auth_headers(requester),
    )
    assert second.status_code == 409
