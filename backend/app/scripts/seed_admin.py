"""Idempotently creates one admin user from SEED_ADMIN_EMAIL/SEED_ADMIN_PASSWORD.

Run with: docker compose exec backend python -m app.scripts.seed_admin
"""

import asyncio

from sqlalchemy import select

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.user import User


async def main() -> None:
    if not settings.SEED_ADMIN_EMAIL or not settings.SEED_ADMIN_PASSWORD:
        raise SystemExit("SEED_ADMIN_EMAIL and SEED_ADMIN_PASSWORD must be set")

    async with AsyncSessionLocal() as db:
        existing = await db.execute(select(User).where(User.email == settings.SEED_ADMIN_EMAIL))
        if existing.scalar_one_or_none():
            print(f"Admin user {settings.SEED_ADMIN_EMAIL} already exists — skipping")
            return

        user = User(
            email=settings.SEED_ADMIN_EMAIL,
            full_name="Admin",
            password_hash=hash_password(settings.SEED_ADMIN_PASSWORD),
            role="admin",
        )
        db.add(user)
        await db.commit()
        print(f"Created admin user {settings.SEED_ADMIN_EMAIL}")


if __name__ == "__main__":
    asyncio.run(main())
