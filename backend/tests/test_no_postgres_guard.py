"""Meta-test guarding against Postgres/SQLAlchemy residue under `backend/src`.

STORY-087 migrated all persistence to DynamoDB and retired the Neon Postgres
adapters; STORY-093 (sprint-49 review minor) adds this guard so a future
change cannot silently reintroduce a SQL ORM dependency into the backend
source tree. Mirrors the filesystem-scan meta-test pattern in
`test_zone_layout.py`.

Cites: STORY-093 AC3 (plan step 4).
"""

from pathlib import Path

FORBIDDEN_TOKENS = ("sqlalchemy", "create_engine", "psycopg")


def find_forbidden_token_hits(src_dir: Path) -> list[str]:
    """Scan every `.py` file under `src_dir` for forbidden tokens.

    Returns a list of `"path:token"` hit descriptions (empty if clean).
    Case-sensitive match, `.py` files only.
    """
    hits = []
    for py_file in src_dir.rglob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        for token in FORBIDDEN_TOKENS:
            if token in content:
                hits.append(f"{py_file}:{token}")
    return hits


def test_no_postgres_or_sqlalchemy_residue_under_backend_src() -> None:
    """No file under `backend/src` may contain `sqlalchemy`, `create_engine`,
    or `psycopg` — the DynamoDB cutover (STORY-087) retired all Postgres
    adapters; this guards against silent reintroduction."""
    test_dir = Path(__file__).resolve().parent
    src_dir = test_dir.parents[0] / "src"
    assert src_dir.is_dir(), f"expected {src_dir} to exist"

    hits = find_forbidden_token_hits(src_dir)
    assert hits == [], f"forbidden Postgres/SQLAlchemy tokens found: {hits}"
