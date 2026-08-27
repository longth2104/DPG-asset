"""GET /api/assets search — matches name/code/holder text same as before,
plus (new) the linked holder's HRIS email, so typing a person's email finds
whatever asset they currently hold."""

import pytest


@pytest.fixture
async def company(make_company):
    return await make_company("C1")


async def test_search_by_holder_email_finds_their_asset(
    client, auth_headers, make_user, make_asset, company
):
    viewer = await make_user(role="cbnv", company=company)
    holder = await make_user(role="cbnv", company=company, email="nguyen.van.a@datphuong.vn")
    await make_asset(name="Laptop Dell", company=company, holder_user_id=holder.id)
    await make_asset(name="Máy in HP", company=company)

    resp = await client.get(
        "/api/assets", params={"search": "nguyen.van.a@datphuong.vn"}, headers=auth_headers(viewer)
    )
    assert resp.status_code == 200
    names = [a["name"] for a in resp.json()]
    assert names == ["Laptop Dell"]
    assert resp.json()[0]["holder_email"] == "nguyen.van.a@datphuong.vn"


async def test_search_by_email_is_case_insensitive_partial(
    client, auth_headers, make_user, make_asset, company
):
    viewer = await make_user(role="cbnv", company=company)
    holder = await make_user(role="cbnv", company=company, email="tuan.le@datphuong.vn")
    await make_asset(name="Màn hình", company=company, holder_user_id=holder.id)

    resp = await client.get("/api/assets", params={"search": "TUAN.LE"}, headers=auth_headers(viewer))
    assert resp.status_code == 200
    assert [a["name"] for a in resp.json()] == ["Màn hình"]


async def test_search_by_unrelated_email_finds_nothing(client, auth_headers, make_user, make_asset, company):
    viewer = await make_user(role="cbnv", company=company)
    await make_asset(name="Laptop Dell", company=company)

    resp = await client.get(
        "/api/assets", params={"search": "nobody@datphuong.vn"}, headers=auth_headers(viewer)
    )
    assert resp.status_code == 200
    assert resp.json() == []


async def test_list_response_includes_holder_email_field(client, auth_headers, make_user, make_asset, company):
    viewer = await make_user(role="cbnv", company=company)
    await make_asset(name="Bàn làm việc", company=company)

    resp = await client.get("/api/assets", headers=auth_headers(viewer))
    assert resp.status_code == 200
    assert resp.json()[0]["holder_email"] is None


async def test_asset_detail_includes_linked_holder_email(client, auth_headers, make_user, make_asset, company):
    viewer = await make_user(role="cbnv", company=company)
    holder = await make_user(role="cbnv", company=company, email="linked.holder@datphuong.vn")
    asset = await make_asset(name="Laptop có chủ", company=company, holder_user_id=holder.id)

    resp = await client.get(f"/api/assets/{asset.id}", headers=auth_headers(viewer))
    assert resp.status_code == 200
    assert resp.json()["holder_email"] == "linked.holder@datphuong.vn"


async def test_asset_detail_holder_email_null_when_unlinked(client, auth_headers, make_user, make_asset, company):
    viewer = await make_user(role="cbnv", company=company)
    asset = await make_asset(name="Laptop chưa liên kết", company=company, holder="Ai đó")

    resp = await client.get(f"/api/assets/{asset.id}", headers=auth_headers(viewer))
    assert resp.status_code == 200
    assert resp.json()["holder_email"] is None
