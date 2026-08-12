"""STORY-212 AC1 (corrected 2026-08-13 at plan verification): no EXISTING
mechanism covers this. All nine import-linter contracts are over `src.*`,
`pyproject.toml` never names `tools`, and the only pre-existing `tools`
reference anywhere in the suite is `conftest.py:37`, which ADDS `tools/` to
`sys.path` -- nothing asserts the reverse direction. This is therefore a NEW,
grep-shaped test, in the style of the existing ZR guards (e.g.
`test_zone_layout.py::find_hand_built_topology_key_dicts`), not a tenth
import-linter contract: `tools/` is dev-only (never in the production image,
same rule as `demo_engine/`), so nothing under `backend/src/` may import it.

AST-based, not text `grep` -- a docstring or comment mentioning the word
"tools" is never a false positive, and the measurement warning against
recursive `grep -r` silently including `__pycache__` (RC-1) is sidestepped
by construction: `ast.parse` only ever sees real `.py` source, and
`__pycache__` entries are skipped explicitly below regardless.
"""

from __future__ import annotations

import ast
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SRC_ROOT = _REPO_ROOT / "backend" / "src"


def find_tools_imports(src_root: Path) -> list[str]:
    """Return `"<relative-path>:<line>"` for every `import tools[...]` /
    `from tools[...] import ...` statement anywhere under `src_root`.
    Catches both the bare package (`tools`) and any dotted submodule
    (`tools.demo_engine`, `tools.demo_engine.store`, ...)."""
    violations: list[str] = []
    for path in sorted(src_root.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "tools" or alias.name.startswith("tools."):
                        violations.append(f"{path}:{node.lineno}")
            elif isinstance(node, ast.ImportFrom):
                if node.module and (
                    node.module == "tools" or node.module.startswith("tools.")
                ):
                    violations.append(f"{path}:{node.lineno}")
    return violations


def test_find_tools_imports_detects_offender(tmp_path: Path) -> None:
    """Meta-test for the guard itself: prove it fires on a throwaway
    offender -- both the `import tools...` and `from tools... import ...`
    shapes -- before trusting it against the real tree."""
    offender = tmp_path / "offender.py"
    offender.write_text(
        "import tools.demo_engine\nfrom tools.demo_engine import store\n",
        encoding="utf-8",
    )
    assert find_tools_imports(tmp_path) == [f"{offender}:1", f"{offender}:2"]


def test_find_tools_imports_ignores_unrelated_imports(tmp_path: Path) -> None:
    """A file with no `tools` import at all -- including one mentioning the
    substring "tools" only in a docstring/comment, never as an import
    statement -- yields no violation (AST-based, not text `grep`)."""
    clean = tmp_path / "clean.py"
    clean.write_text(
        '"""Uses tools like a hammer, not the tools/ package."""\n'
        "from src.core.ports.clock import Clock\n\n\n"
        "def f(clock: Clock) -> None:\n    return None\n",
        encoding="utf-8",
    )
    assert find_tools_imports(tmp_path) == []


def test_find_tools_imports_empty_dir_returns_empty_list(tmp_path: Path) -> None:
    """Explicit empty-input behaviour (checklist): an empty directory is a
    valid, non-error input and yields the empty list."""
    assert find_tools_imports(tmp_path) == []


def test_no_backend_src_file_imports_tools() -> None:
    """The real guard (STORY-212 AC1): `backend/src/` never imports
    `tools/`, which is dev-only and never ships in the production image."""
    violations = find_tools_imports(_SRC_ROOT)
    assert not violations, (
        "backend/src/ file(s) import `tools/`, which is dev-only and never "
        "ships in the production image:\n" + "\n".join(violations)
    )
