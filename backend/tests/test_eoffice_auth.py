"""require_eoffice_key (app/api/deps.py) — the inbound e-office integration
accepts its shared key however the caller sends it (Bearer, X-API-Key,
Api-Key, or ?api_key=), since e-office's own client isn't ours to configure."""

from app.core.config import settings

TEST_KEY = "test-eoffice-key-123"


async def _set_key(monkeypatch, value):
    monkeypatch.setattr(settings, "EOFFICE_API_KEY", value)


async def test_no_key_provided_is_rejected(client, monkeypatch):
    await _set_key(monkeypatch, TEST_KEY)
    resp = await client.get("/api/eoffice/assets")
    assert resp.status_code == 401


async def test_wrong_key_is_rejected(client, monkeypatch):
    await _set_key(monkeypatch, TEST_KEY)
    resp = await client.get("/api/eoffice/assets", headers={"Authorization": "Bearer wrong-key"})
    assert resp.status_code == 401


async def test_integration_disabled_when_no_key_configured(client, monkeypatch):
    await _set_key(monkeypatch, "")
    resp = await client.get("/api/eoffice/assets", headers={"Authorization": f"Bearer {TEST_KEY}"})
    assert resp.status_code == 503


async def test_accepts_authorization_bearer(client, monkeypatch):
    await _set_key(monkeypatch, TEST_KEY)
    resp = await client.get("/api/eoffice/assets", headers={"Authorization": f"Bearer {TEST_KEY}"})
    assert resp.status_code == 200


async def test_accepts_x_api_key_header(client, monkeypatch):
    await _set_key(monkeypatch, TEST_KEY)
    resp = await client.get("/api/eoffice/assets", headers={"X-API-Key": TEST_KEY})
    assert resp.status_code == 200


async def test_accepts_api_key_header(client, monkeypatch):
    await _set_key(monkeypatch, TEST_KEY)
    resp = await client.get("/api/eoffice/assets", headers={"Api-Key": TEST_KEY})
    assert resp.status_code == 200


async def test_accepts_api_key_query_param(client, monkeypatch):
    await _set_key(monkeypatch, TEST_KEY)
    resp = await client.get("/api/eoffice/assets", params={"api_key": TEST_KEY})
    assert resp.status_code == 200
