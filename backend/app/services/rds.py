import httpx

from app.core.config import settings

PAGE_SIZE = 100


async def fetch_all_assets() -> list[dict]:
    """Paginates through RDS's asset listing (tscd = tài sản cố định /
    fixed assets) and returns every row."""
    if not settings.RDS_BASE_URL or not settings.RDS_API_KEY:
        raise RuntimeError("RDS is not configured")

    assets: list[dict] = []
    offset = 0
    async with httpx.AsyncClient(timeout=30) as client:
        while True:
            resp = await client.get(
                f"{settings.RDS_BASE_URL}{settings.RDS_CATEGORIES_PATH}",
                params={"limit": PAGE_SIZE, "offset": offset},
                headers={"Authorization": f"Bearer {settings.RDS_API_KEY}"},
            )
            resp.raise_for_status()
            payload = resp.json()
            page = payload.get("data", [])
            assets.extend(page)
            total = payload.get("total", len(assets))
            offset += PAGE_SIZE
            if offset >= total or not page:
                break
    return assets
