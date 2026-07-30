"""Import-provenance helper for proofs (STORY-187).

A reality-gate/discrimination proof must be able to answer "which code did I
actually run?" BEFORE it reports a score — the working agreement A1
refinement and A3 (`.scrum/checklists/implementer.md`) both name this as a
checklist line with no tool behind it. Sprint 63's STORY-180 discrimination
proof ran in a git worktree and reported 4/4 on BOTH sides because the wrong
tree executed on both; "green both sides" would have argued AGAINST a
correct fix. This module is the mechanical rung: it is not bespoke per
proof, because "which file did this module actually come from, and is it the
tree I think I am testing?" is the same question every time.

**The mechanism is a plain absolute `sys.path` entry, NOT a setuptools
`MetaPathFinder`** — the story text and the first sprint-64 plan draft both
said "finder"; verified wrong pre-lock. This repo is installed editable via
`package-dir = {"" = "backend"}` (`pyproject.toml:23`), and the resulting
`.venv/Lib/site-packages/__editable__.uptime_monitor_v3-0.1.0.pth` contains
EXACTLY ONE LINE: the absolute path to `backend`. That single `sys.path`
entry is what resolves `src.*` to the main tree from inside any worktree,
whatever the process's cwd is — no import hook is involved. This makes AC3's
regression test easier than the story assumed: a `sys.path`-ordering
reproduction is not an approximation of the real mechanism, it IS the real
mechanism, reproduced with two ordinary directories instead of a worktree.

Placement: `tools/`, alongside the demo engine (STORY-148) — dev-only, never
in the production image, free to import `src.*`. Nothing under
`backend/src/` may import this module (STORY-187 AC6); nothing here is
imported by anything under `backend/src/`.

Usable from a bare `python -c` one-liner (AC4), e.g.::

    python -c "from import_provenance import assert_import_root; \\
        print(assert_import_root('src.composition.vendor_health', 'C:/Hyn/uptime_monitor_v3/backend'))"

A caller names the module AND the root it expects, per call — there is no
single global "under cwd?" check, because provenance can be split-brain in
this repo: under pytest run from a worktree, `demo_engine.*` resolves to the
worktree (`backend/tests/conftest.py:37-39` inserts the worktree's own
`tools/` at `sys.path[0]`) while `src.*` and `tests.*` resolve to the MAIN
tree via the `.pth` entry above. A caller must therefore pass the root it
expects for THAT module, never assume `Path.cwd()`.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from pathlib import Path


class WrongImportRootError(ImportError):
    """A module resolved outside the root a proof expected it to come from.

    Raised by `assert_import_root` (STORY-187 AC2). The message always names
    BOTH the expected root and the actual resolved `__file__` — a proof must
    be able to read, from the exception text alone, which tree it actually
    ran against.
    """


@dataclass(frozen=True)
class ImportProvenance:
    """The resolved provenance of a successfully-verified import (AC1).

    `module_name` is the dotted name passed in; `file_path` is the module's
    resolved `__file__`; `expected_root` is the resolved root it was
    confirmed to lie under. `str()` formats a single line a proof can print
    directly (AC1's "so a proof can put that line in its own output").
    """

    module_name: str
    file_path: Path
    expected_root: Path

    def __str__(self) -> str:
        return (
            f"{self.module_name} -> {self.file_path} "
            f"(under expected root {self.expected_root})"
        )


def assert_import_root(module_name: str, expected_root: Path | str) -> ImportProvenance:
    """Import `module_name` and assert it resolved under `expected_root`.

    Resolves `expected_root` to an absolute path, imports `module_name` (via
    `importlib.import_module` — reusing whatever `sys.modules` already holds,
    exactly as any other import in the process would), and reads the
    resulting module's `__file__`.

    Returns an `ImportProvenance` (AC1) — printable via `str()` — when the
    resolved file lies under `expected_root`. Raises `WrongImportRootError`
    (AC2) naming BOTH `expected_root` and the actual resolved file when it
    does not, or when the module has no `__file__` at all (a namespace
    package or a built-in — there is no file to verify).
    """
    root = Path(expected_root).resolve()
    module = importlib.import_module(module_name)

    file_attr = getattr(module, "__file__", None)
    if file_attr is None:
        raise WrongImportRootError(
            f"{module_name!r} has no __file__ (built-in or namespace "
            f"package) -- cannot verify it resolved under expected root "
            f"{root}"
        )

    file_path = Path(file_attr).resolve()
    if not file_path.is_relative_to(root):
        raise WrongImportRootError(
            f"{module_name!r} resolved to {file_path}, which is NOT under "
            f"the expected root {root} -- wrong tree executed"
        )

    return ImportProvenance(
        module_name=module_name, file_path=file_path, expected_root=root
    )
