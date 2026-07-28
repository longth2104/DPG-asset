import asyncio
import sys
from logging.config import fileConfig
from pathlib import Path

# The `alembic` console script sets sys.path[0] to its own bin/ directory,
# not the CWD — so `app` isn't importable without this when invoked as a
# bare `alembic upgrade head` (as the Dockerfile CMD does).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings
from app.core.database import Base

# Import every model module so Base.metadata actually knows about all tables
# for autogenerate — migrations here are still hand-written (see 001_initial),
# but there's no reason to leave autogenerate half-blind for later phases.
from app.models import user  # noqa: F401
from app.models import asset  # noqa: F401
from app.models import asset_event  # noqa: F401
from app.models import document  # noqa: F401
from app.models import request  # noqa: F401
from app.models import company  # noqa: F401

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = create_async_engine(settings.DATABASE_URL)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
