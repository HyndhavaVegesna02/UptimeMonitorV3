"""Test config: make the repo-root `scripts/` dir importable.

`scripts/` holds standalone CI scripts (e.g. check_fk_direction.py) that are not
part of the `src` package but whose pure logic is unit-tested. This repo-root is
two levels up from this file (backend/tests/conftest.py -> repo root).
"""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPTS = _REPO_ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
