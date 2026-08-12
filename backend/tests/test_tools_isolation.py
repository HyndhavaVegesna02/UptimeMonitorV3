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

**MAJOR 5 fix (sprint-70 fix round): also catches the BARE import shape,
which is the ONE this repo actually uses.** The original guard matched only
`tools`/`tools.<submodule>` (a DOTTED prefix). But `conftest.py:37` puts
`tools/` itself on `sys.path` -- including for `tools/evidence_check.py`'s
OWN `from import_provenance import ...` -- so every real `tools/` import
anywhere in this suite is bare (`import evidence_check`,
`from demo_engine import store`), never `tools.evidence_check`. Probed: the
pre-fix guard returned `[]` on both bare shapes while both import fine in a
real session -- the accident it exists to catch (green in CI,
`ModuleNotFoundError` in the production image, which never puts `tools/` on
`sys.path`) is precisely the bare form. Fixed by deriving the set of
importable top-level names under `tools/` from the directory listing itself
(never hand-listed -- STORY-220's own lesson), so a new `tools/` file is
covered automatically without touching this guard."""

from __future__ import annotations

import ast
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SRC_ROOT = _REPO_ROOT / "backend" / "src"
_TOOLS_ROOT = _REPO_ROOT / "tools"


def tools_top_level_names(tools_root: Path) -> set[str]:
    """Derive the set of importable top-level names under `tools_root`: any
    `<name>.py` module file directly under it, and any `<name>/` package
    directory containing an `__init__.py` -- never hand-listed (STORY-220's
    lesson), so a new `tools/` file or package is covered automatically. A
    directory without `__init__.py` (e.g. `tools/ui-sweep/`, a JS project;
    also `__pycache__`) is not a Python package and is excluded."""
    if not tools_root.is_dir():
        return set()
    names: set[str] = set()
    for entry in tools_root.iterdir():
        if entry.name == "__pycache__":
            continue
        if entry.is_file() and entry.suffix == ".py":
            names.add(entry.stem)
        elif entry.is_dir() and (entry / "__init__.py").is_file():
            names.add(entry.name)
    return names


def find_tools_imports(src_root: Path, tools_root: Path | None = None) -> list[str]:
    """Return `"<relative-path>:<line>"` for every `import tools[...]` /
    `from tools[...] import ...` statement anywhere under `src_root`.
    Catches the dotted package/submodule shape (`tools`, `tools.demo_engine`,
    `tools.demo_engine.store`, ...) AND the BARE shape this repo actually
    uses (`import evidence_check`, `from demo_engine import store`) --
    a bare `import X` / `from X import ...` is flagged when `X`'s top-level
    name matches a module or package present under `tools_root` (defaults to
    the real repo `tools/`), per `tools_top_level_names` above."""
    if tools_root is None:
        tools_root = _TOOLS_ROOT
    bare_names = tools_top_level_names(tools_root)
    violations: list[str] = []
    for path in sorted(src_root.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split(".")[0]
                    if (
                        alias.name == "tools"
                        or alias.name.startswith("tools.")
                        or top in bare_names
                    ):
                        violations.append(f"{path}:{node.lineno}")
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    top = node.module.split(".")[0]
                    if (
                        node.module == "tools"
                        or node.module.startswith("tools.")
                        or top in bare_names
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


def test_tools_top_level_names_derives_from_directory_listing(tmp_path: Path) -> None:
    """`tools_top_level_names` must be DERIVED, never hand-listed (STORY-220's
    lesson): a `.py` module file yields its stem, an `__init__.py`-bearing
    directory yields its own name, and a non-package directory (no
    `__init__.py`, e.g. the real `tools/ui-sweep/` JS project) plus
    `__pycache__` are both excluded."""
    tools_root = tmp_path / "tools"
    tools_root.mkdir()
    (tools_root / "citation_gate.py").write_text("", encoding="utf-8")
    pkg = tools_root / "demo_engine"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    non_pkg = tools_root / "ui-sweep"
    non_pkg.mkdir()
    (non_pkg / "package.json").write_text("{}", encoding="utf-8")
    pycache = tools_root / "__pycache__"
    pycache.mkdir()
    (pycache / "citation_gate.cpython-313.pyc").write_text("", encoding="utf-8")

    assert tools_top_level_names(tools_root) == {"citation_gate", "demo_engine"}


def test_tools_top_level_names_nonexistent_root_returns_empty_set(
    tmp_path: Path,
) -> None:
    """Explicit empty-input behaviour: a `tools_root` that does not exist
    (or is not yet created) yields the empty set, never a crash."""
    assert tools_top_level_names(tmp_path / "does_not_exist") == set()


def test_find_tools_imports_detects_bare_import_matching_tools_dir_contents(
    tmp_path: Path,
) -> None:
    """MAJOR 5 (sprint-70 fix round): the accident this guard exists to
    catch is a BARE import (`import evidence_check`,
    `from demo_engine import store`) -- exactly how every real `tools/`
    import in this repo is written, because `conftest.py` puts `tools/` on
    `sys.path` (including `evidence_check.py`'s own `from import_provenance
    import ...`). Probing the pre-fix guard: it returned `[]` on both of
    these while both import fine in a real session."""
    tools_root = tmp_path / "tools"
    tools_root.mkdir()
    (tools_root / "evidence_check.py").write_text("VALUE = 1\n", encoding="utf-8")
    demo_pkg = tools_root / "demo_engine"
    demo_pkg.mkdir()
    (demo_pkg / "__init__.py").write_text("", encoding="utf-8")

    src_root = tmp_path / "src"
    src_root.mkdir()
    offender = src_root / "offender.py"
    offender.write_text(
        "import evidence_check\nfrom demo_engine import store\n",
        encoding="utf-8",
    )

    violations = find_tools_imports(src_root, tools_root=tools_root)
    assert violations == [f"{offender}:1", f"{offender}:2"]


def test_find_tools_imports_ignores_bare_import_not_matching_tools_dir(
    tmp_path: Path,
) -> None:
    """The inverse: a bare import whose top-level name is NOT present under
    `tools_root` (e.g. a stdlib import) is never a false positive."""
    tools_root = tmp_path / "tools"
    tools_root.mkdir()
    (tools_root / "evidence_check.py").write_text("VALUE = 1\n", encoding="utf-8")

    src_root = tmp_path / "src"
    src_root.mkdir()
    clean = src_root / "clean.py"
    clean.write_text(
        "import os\nfrom collections import defaultdict\n", encoding="utf-8"
    )

    assert find_tools_imports(src_root, tools_root=tools_root) == []


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
