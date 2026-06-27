#!/usr/bin/env python
"""Schema FK-direction CI check (dossier §9) — the non-LLM schema boundary floor.

The architecture's schema spine is a fixed allowlist of constant-core tables.
Feature domains may reference the spine inward (feature -> spine), but the spine
must never reference a feature table outward (spine -> feature). This check reads
the database's *actual* foreign keys from information_schema and fails the build
(nonzero exit) if any spine table references a non-spine (feature) table — making
a schema boundary violation a build failure, exactly like a forbidden import.

The decision logic (`find_violations`) is a pure function with no DB dependency,
so it is unit-tested directly. `main()` does the I/O: reads DATABASE_URL, queries
information_schema via psycopg, and exits 0/1.

Run as the bare DoD command:  python scripts/check_fk_direction.py
(requires the DATABASE_URL env var pointing at a migrated Postgres database).
"""

from __future__ import annotations

import os
import sys
from collections.abc import Iterable

# Dossier §9 SPINE allowlist — the explicit set of constant-core tables.
# Everything not in this set is a feature domain.
SPINE: frozenset[str] = frozenset(
    {
        "apps",
        "signals",
        "components",
        "observations",
        "watermarks",
        "rejected_observations",
        "problem_signals",
        "status_proposals",
        "approval_events",
        "publications",
        "maintenance_windows",
    }
)

# FK source/target table names in the public schema. Direction-only: a row exists
# per FK constraint mapping the referencing (source) table to the referenced
# (target) table.
_FK_QUERY = """
SELECT tc.table_name AS source_table, ccu.table_name AS target_table
FROM information_schema.table_constraints tc
JOIN information_schema.constraint_column_usage ccu
  ON tc.constraint_name = ccu.constraint_name
 AND tc.table_schema = ccu.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND tc.table_schema = 'public';
"""


def find_violations(
    foreign_keys: Iterable[tuple[str, str]],
    spine: Iterable[str] = SPINE,
) -> list[tuple[str, str]]:
    """Return the FK edges that violate the spine boundary.

    `foreign_keys` is an iterable of ``(source_table, target_table)`` pairs.
    A violation is an outward reference from the spine: the source table is in
    the spine and the target table is not. Direction matters — a feature table
    referencing the spine (feature -> spine) is correct and is not flagged.
    """
    spine_set = frozenset(spine)
    return [
        (source, target)
        for source, target in foreign_keys
        if source in spine_set and target not in spine_set
    ]


def _read_foreign_keys(database_url: str) -> list[tuple[str, str]]:
    """Read real FK (source_table, target_table) pairs from information_schema."""
    import psycopg

    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(_FK_QUERY)
            return [(row[0], row[1]) for row in cur.fetchall()]


def main() -> int:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print(
            "ERROR: DATABASE_URL is not set. Point it at the migrated database, "
            "e.g. postgresql://postgres:postgres@localhost:55432/uptime",
            file=sys.stderr,
        )
        return 2

    foreign_keys = _read_foreign_keys(database_url)
    violations = find_violations(foreign_keys, SPINE)

    if violations:
        print("Schema FK-direction violations (spine references a feature table):")
        for source, target in violations:
            print(f"  - {source} -> {target}")
        return 1

    print(f"FK-direction OK: {len(foreign_keys)} foreign key(s) checked, 0 violations.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
