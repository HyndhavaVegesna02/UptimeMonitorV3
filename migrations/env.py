import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Migrations run as a separate release step on the DIRECT (non-pooled) Neon
# connection — DDL misbehaves through PgBouncer transaction pooling (dossier §17).
# This is deliberately distinct from the app runtime, which reads the POOLED
# DATABASE_URL via src.composition.settings. Keep these two env vars distinct.
MIGRATION_DATABASE_URL_VAR = "DATABASE_URL_DIRECT"


def _normalize_url(url: str) -> str:
    """Force the psycopg3 dialect for SQLAlchemy 2.

    A bare ``postgresql://`` (or ``postgres://``) URL resolves to psycopg2 under
    SQLAlchemy; this project uses psycopg 3, whose dialect is ``postgresql+psycopg``.
    URLs that already name a driver are left untouched.
    """
    if url.startswith("postgresql+"):
        return url
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://"):]
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://"):]
    return url


def get_migration_url() -> str:
    """Resolve the DIRECT migration database URL from the environment."""
    return _normalize_url(os.environ[MIGRATION_DATABASE_URL_VAR])


# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# The migration URL comes from the DIRECT connection env var, not from
# alembic.ini (sqlalchemy.url there is intentionally blank).
config.set_main_option("sqlalchemy.url", get_migration_url())

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = None

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
