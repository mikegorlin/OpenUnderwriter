"""Alembic migration environment for the knowledge store.

Configures Alembic to use the SQLAlchemy models from
do_uw.knowledge.models as the migration target metadata.
Supports both offline (SQL generation) and online (direct
database) migration modes, with batch mode for SQLite.
"""

from __future__ import annotations

from logging.config import fileConfig
from typing import Any

from alembic import context
from sqlalchemy import Connection, create_engine, pool

from do_uw.knowledge.models import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    Generates SQL scripts without connecting to the database.
    Useful for reviewing migration SQL before applying.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    Connects to the database and applies migrations directly.
    Uses batch mode for SQLite compatibility (ALTER TABLE
    limitations).
    """
    configuration: dict[str, Any] = config.get_section(
        config.config_ini_section, {}
    )
    url = configuration.get(
        "sqlalchemy.url", "sqlite:///knowledge.db"
    )
    connectable = create_engine(url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        _run_with_connection(connection)


def _run_with_connection(connection: Connection) -> None:
    """Configure and run migrations with an existing connection.

    Args:
        connection: Active SQLAlchemy connection.
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
