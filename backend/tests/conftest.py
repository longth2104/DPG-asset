import uuid

import asyncpg
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

# Import every model module so Base.metadata knows about all tables — the
# app never imports them all from one place itself (app/models/__init__.py
# is empty), so tests have to do it explicitly.
from app.models import asset, asset_event, company, council, document, notification, request, user  # noqa: F401
from app.core.config import settings
from app.core.database import Base, get_db
from app.core.security import create_access_token, hash_password
from app.api.deps import get_redis
from app.main import app
from app.models.asset import Asset
from app.models.company import Company
from app.models.user import User

# Run against a dedicated database on the same Postgres instance the app
# uses, never the dev/prod database itself — swap the db name only.
_base_url, _, _db_name = settings.DATABASE_URL.rpartition("/")
TEST_DB_NAME = f"{_db_name}_test"
TEST_DATABASE_URL = f"{_base_url}/{TEST_DB_NAME}"
_ADMIN_DATABASE_URL = f"{_base_url}/postgres"


async def _ensure_test_database_exists():
    dsn = _ADMIN_DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(dsn)
    try:
        exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", TEST_DB_NAME)
        if not exists:
            await conn.execute(f'CREATE DATABASE "{TEST_DB_NAME}"')
    finally:
        await conn.close()


class FakeRedis:
    """Stand-in for the token-blocklist check in get_current_user — no test
    ever blocklists a token, so a real Redis connection isn't needed."""

    async def get(self, _key):
        return None

    async def close(self):
        pass


@pytest_asyncio.fixture
async def db_session():
    """Function-scoped, own engine per test: asyncpg connections are bound
    to the event loop they were created on, and pytest-asyncio gives each
    async test its own loop, so a shared/session-scoped engine would be
    reused across loops and corrupt mid-flight (surfaces as asyncpg's
    "another operation is in progress"). One test = one outer transaction,
    rolled back at teardown — app code calling session.commit() only closes
    a nested SAVEPOINT (join_transaction_mode), so committed-looking data
    from the route under test never survives past the test that created it.
    """
    await _ensure_test_database_exists()
    eng = create_async_engine(TEST_DATABASE_URL)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with eng.connect() as conn:
        await conn.begin()
        session_factory = async_sessionmaker(
            bind=conn, expire_on_commit=False, join_transaction_mode="create_savepoint"
        )
        session = session_factory()
        yield session
        await session.close()
        await conn.rollback()
    await eng.dispose()


@pytest_asyncio.fixture
async def client(db_session):
    async def _get_db_override():
        yield db_session

    async def _get_redis_override():
        yield FakeRedis()

    app.dependency_overrides[get_db] = _get_db_override
    app.dependency_overrides[get_redis] = _get_redis_override
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


def _unique_email(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}@test.local"


@pytest_asyncio.fixture
async def make_company(db_session):
    async def _make(code: str, *, parent: Company | None = None, grants_global_access: bool = False):
        company = Company(
            code=code,
            name=code,
            parent_id=parent.id if parent else None,
            path="",  # set below once we have the id
            grants_global_access=grants_global_access,
        )
        db_session.add(company)
        await db_session.flush()
        company.path = f"{parent.path}/{company.id}" if parent else str(company.id)
        await db_session.flush()
        return company

    return _make


@pytest_asyncio.fixture
async def make_user(db_session):
    async def _make(*, role: str = "cbnv", company: Company | None = None, email: str | None = None):
        u = User(
            email=email or _unique_email(role),
            full_name=role,
            password_hash=hash_password("password123"),
            role=role,
            company_id=company.id if company else None,
        )
        db_session.add(u)
        await db_session.flush()
        return u

    return _make


@pytest_asyncio.fixture
async def make_asset(db_session):
    async def _make(*, name: str = "Test asset", company: Company | None = None, **kwargs):
        a = Asset(name=name, company_id=company.id if company else None, **kwargs)
        db_session.add(a)
        await db_session.flush()
        return a

    return _make


@pytest.fixture
def auth_headers():
    def _headers(user: User) -> dict:
        token = create_access_token(subject=user.id)
        return {"Authorization": f"Bearer {token}"}

    return _headers
