"""ZR-2 standing guard (STORY-207): vendor vocabulary never becomes an
identifier/annotation/signature/dict-key/stored-value inside `core/`.

Cites `docs/scrum/wiki/zone-rules.md` ZR-2. Built incrementally; see later
commits in this story for the full six-rule walk and its docstring.
"""

from __future__ import annotations

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_CORE_ROOT = _REPO_ROOT / "backend" / "src" / "core"


def _discover_core_modules() -> list[Path]:
    """Every `.py` file under `backend/src/core/` (`domain`, `ports`, `services`,
    `queries`, and the package root `core/__init__.py`) -- AC1's scan root."""
    return sorted(_CORE_ROOT.rglob("*.py"))


def test_discovers_at_least_25_core_modules() -> None:
    """AC9 -- non-vacuity floor. A wrong root or a moved package must go RED,
    never silently iterate over nothing and pass. Do not hardcode 31 -- later
    stories (STORY-206 AC6, STORY-220) each add a module under `core/`."""
    modules = _discover_core_modules()
    assert len(modules) >= 25, (
        f"expected at least 25 modules under {_CORE_ROOT}, found "
        f"{len(modules)}: {[str(m) for m in modules]} -- check "
        "_CORE_ROOT / _discover_core_modules before trusting this guard at all"
    )
