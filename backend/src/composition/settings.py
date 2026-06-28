"""App runtime settings (composition zone).

The application runtime talks to Neon through the POOLED PgBouncer connection,
read from the ``DATABASE_URL`` env var (dossier §3, §17). This is deliberately
distinct from the migration path, which uses the DIRECT connection
(``DATABASE_URL_DIRECT``) — DDL misbehaves through transaction pooling, so
migrations run as a separate release step on the direct connection
(see ``migrations/env.py``).

Reading env vars and owning configuration belongs in the composition zone, never
in ``core/`` (the import-linter boundary forbids core importing infrastructure).
"""

from __future__ import annotations

import os
from dataclasses import dataclass

# The env var the application runtime reads for its (pooled) database URL.
APP_DATABASE_URL_VAR = "DATABASE_URL"


@dataclass(frozen=True)
class Settings:
    """Immutable app settings resolved from the environment."""

    database_url: str
    config_dir: str


def load_settings() -> Settings:
    """Load runtime settings from the environment.

    Reads the POOLED connection string from ``DATABASE_URL``. Raises
    ``KeyError`` if it is unset — the app must not start without a database URL.
    Also reads config_dir from ``CONFIG_DIR`` env var, defaulting to ``"config/apps"``.
    """
    return Settings(
        database_url=os.environ[APP_DATABASE_URL_VAR],
        config_dir=os.environ.get("CONFIG_DIR", "config/apps"),
    )
