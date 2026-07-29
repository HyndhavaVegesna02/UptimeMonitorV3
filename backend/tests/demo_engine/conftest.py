"""Make the repo-root `tools/` dir importable, so `demo_engine` (STORY-148)
resolves as a top-level package under test.

Mirrors the existing `scripts/` precedent one directory up
(`backend/tests/conftest.py:16-19`): that file inserts the repo-root
`scripts/` dir itself onto `sys.path` and imports `dynamo_local` as a
top-level module (not `scripts.dynamo_local`). This conftest does the same
for `tools/`, so `demo_engine` (the STORY-148 AC9 package name — `demo-engine`
is not importable) resolves the same way, scoped to this test subpackage only.
"""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_TOOLS = _REPO_ROOT / "tools"
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))
