"""Structured maintenance log per docs/cycle.md: report an issue, resolve
it, and confirm the asset's own status flips accordingly."""

import pytest


@pytest.fixture
async def company(make_company):
    return await make_company("C1")


async def test_report_issue_flips_asset_to_under_repair(
    client, auth_headers, make_user, make_asset, company
):
    manager = await make_user(role="phong_thiet_bi", company=company)
    asset = await make_asset(name="Máy in", company=company, status="dang_su_dung")

    resp = await client.post(
        f"/api/assets/{asset.id}/maintenance",
        json={"location": "Xưởng sửa chữa A", "cost": 150000, "condition_note": "Kẹt giấy liên tục"},
        headers=auth_headers(manager),
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["status"] == "reported"
    assert body["resolved_at"] is None
    assert body["location"] == "Xưởng sửa chữa A"

    detail = await client.get(f"/api/assets/{asset.id}", headers=auth_headers(manager))
    assert detail.json()["status"] == "dang_sua_chua"
    assert len(detail.json()["maintenance_records"]) == 1


async def test_report_issue_does_not_override_terminal_status(
    client, auth_headers, make_user, make_asset, company
):
    manager = await make_user(role="phong_thiet_bi", company=company)
    asset = await make_asset(name="Đã thanh lý", company=company, status="da_thanh_ly")

    resp = await client.post(
        f"/api/assets/{asset.id}/maintenance",
        json={"condition_note": "Ghi nhận muộn"},
        headers=auth_headers(manager),
    )
    assert resp.status_code == 201, resp.text

    detail = await client.get(f"/api/assets/{asset.id}", headers=auth_headers(manager))
    assert detail.json()["status"] == "da_thanh_ly"


async def test_resolve_reverts_asset_status(client, auth_headers, make_user, make_asset, company):
    manager = await make_user(role="phong_thiet_bi", company=company)
    asset = await make_asset(name="Laptop", company=company, status="dang_su_dung")

    create = await client.post(
        f"/api/assets/{asset.id}/maintenance",
        json={"cost": 500000},
        headers=auth_headers(manager),
    )
    record_id = create.json()["id"]

    resolve = await client.patch(
        f"/api/assets/{asset.id}/maintenance/{record_id}",
        json={"resolve": True, "condition_note": "Đã thay bàn phím, hoạt động bình thường"},
        headers=auth_headers(manager),
    )
    assert resolve.status_code == 200, resolve.text
    assert resolve.json()["status"] == "resolved"
    assert resolve.json()["resolved_at"] is not None
    assert resolve.json()["condition_note"] == "Đã thay bàn phím, hoạt động bình thường"

    detail = await client.get(f"/api/assets/{asset.id}", headers=auth_headers(manager))
    assert detail.json()["status"] == "dang_su_dung"


async def test_resolve_does_not_override_status_changed_elsewhere(
    client, auth_headers, make_user, make_asset, company
):
    manager = await make_user(role="phong_thiet_bi", company=company)
    asset = await make_asset(name="Đã điều động trong lúc sửa", company=company, status="dang_su_dung")

    create = await client.post(
        f"/api/assets/{asset.id}/maintenance", json={}, headers=auth_headers(manager)
    )
    record_id = create.json()["id"]

    # Someone completed a transfer while the asset was under repair.
    await client.put(
        f"/api/assets/{asset.id}", json={"status": "da_dieu_dong"}, headers=auth_headers(manager)
    )

    await client.patch(
        f"/api/assets/{asset.id}/maintenance/{record_id}",
        json={"resolve": True},
        headers=auth_headers(manager),
    )

    detail = await client.get(f"/api/assets/{asset.id}", headers=auth_headers(manager))
    assert detail.json()["status"] == "da_dieu_dong"


async def test_maintenance_record_not_found_for_other_asset(
    client, auth_headers, make_user, make_asset, company
):
    manager = await make_user(role="phong_thiet_bi", company=company)
    asset_a = await make_asset(name="A", company=company)
    asset_b = await make_asset(name="B", company=company)

    create = await client.post(
        f"/api/assets/{asset_a.id}/maintenance", json={}, headers=auth_headers(manager)
    )
    record_id = create.json()["id"]

    resp = await client.patch(
        f"/api/assets/{asset_b.id}/maintenance/{record_id}",
        json={"resolve": True},
        headers=auth_headers(manager),
    )
    assert resp.status_code == 404


async def test_document_upload_links_to_maintenance_record(
    client, auth_headers, make_user, make_asset, company
):
    manager = await make_user(role="phong_thiet_bi", company=company)
    asset = await make_asset(name="Máy chủ", company=company)

    create = await client.post(
        f"/api/assets/{asset.id}/maintenance", json={}, headers=auth_headers(manager)
    )
    record_id = create.json()["id"]

    upload = await client.post(
        f"/api/assets/{asset.id}/documents",
        data={"maintenance_record_id": record_id},
        files={"file": ("receipt.pdf", b"fake-pdf-bytes", "application/pdf")},
        headers=auth_headers(manager),
    )
    assert upload.status_code == 201, upload.text

    detail = await client.get(f"/api/assets/{asset.id}", headers=auth_headers(manager))
    records = detail.json()["maintenance_records"]
    assert len(records) == 1
    assert len(records[0]["documents"]) == 1
    assert records[0]["documents"][0]["filename"] == "receipt.pdf"
