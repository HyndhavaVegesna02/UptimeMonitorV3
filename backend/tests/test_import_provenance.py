"""Tests for the import-provenance helper (STORY-187).

Every reality-gate/discrimination proof in this repo must be able to answer
"which code did I actually run?" before it reports a score — the working
agreement A1 refinement and A3 (`.scrum/checklists/implementer.md`) both name
this as a checklist LINE with no tool behind it. This module tests the tool.

The mechanism this guards against is a plain absolute `sys.path` entry (the
editable install's `.pth` file, `__editable__.uptime_monitor_v3-0.1.0.pth`,
containing exactly `C:\\Hyn\\uptime_monitor_v3\\backend`) — NOT a setuptools
`MetaPathFinder`, whatever the story text says. See `import_provenance.py`'s
own docstring for the verified mechanism.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest
from import_provenance import ImportProvenance, WrongImportRootError, assert_import_root

# --- AC2: it FAILS when provenance is wrong, with a named error ------------


def test_assert_import_root_raises_named_error_when_module_resolves_outside_root(
    tmp_path,
):
    """A module that exists but resolves OUTSIDE the expected root raises
    `WrongImportRootError`, whose message names BOTH the expected root and
    the actual resolved path (AC2) — the message content is asserted, not
    just the exception type.
    """
    actual_root = tmp_path / "actual_root"
    actual_root.mkdir()
    module_path = actual_root / "_story187_ac2_probe.py"
    module_path.write_text("MARKER = 'ac2'\n", encoding="utf-8")

    wrong_expected_root = tmp_path / "wrong_expected_root"
    wrong_expected_root.mkdir()

    sys.path.insert(0, str(actual_root))
    try:
        with pytest.raises(WrongImportRootError) as excinfo:
            assert_import_root("_story187_ac2_probe", expected_root=wrong_expected_root)
        message = str(excinfo.value)
        assert str(wrong_expected_root.resolve()) in message
        assert str(module_path.resolve()) in message
    finally:
        sys.path.remove(str(actual_root))
        sys.modules.pop("_story187_ac2_probe", None)


# --- AC1: it reports provenance ---------------------------------------------


def test_assert_import_root_reports_file_and_root_when_correct(tmp_path):
    """When the module DOES resolve under the expected root, the helper
    returns the resolved `__file__` and the root it was resolved under
    (AC1), and formats readably enough for a proof to print directly.
    """
    root = tmp_path / "expected_root"
    root.mkdir()
    module_path = root / "_story187_ac1_probe.py"
    module_path.write_text("MARKER = 'ac1'\n", encoding="utf-8")

    sys.path.insert(0, str(root))
    try:
        provenance = assert_import_root("_story187_ac1_probe", expected_root=root)

        assert isinstance(provenance, ImportProvenance)
        assert provenance.module_name == "_story187_ac1_probe"
        assert provenance.file_path == module_path.resolve()
        assert provenance.expected_root == root.resolve()

        report_line = str(provenance)
        assert "_story187_ac1_probe" in report_line
        assert str(module_path.resolve()) in report_line
        assert str(root.resolve()) in report_line
    finally:
        sys.path.remove(str(root))
        sys.modules.pop("_story187_ac1_probe", None)


# --- AC3: the editable-install trap is the regression test ------------------


def test_assert_import_root_catches_the_editable_install_pth_trap(tmp_path):
    """Reproduces the ACTUAL sprint-63 STORY-180 failure mechanism.

    LABELLED SIMULATION (AC3 permits a labelled `sys.path` reproduction and
    forbids an unlabelled one): the real trap is that this repo's editable
    install is a single absolute `sys.path` ENTRY — the `.pth` file
    `__editable__.uptime_monitor_v3-0.1.0.pth` contains exactly one line,
    `C:\\Hyn\\uptime_monitor_v3\\backend` — not a setuptools `MetaPathFinder`
    (verified pre-lock; see `import_provenance.py`'s module docstring). A
    `.pth` entry is registered on `sys.path` once, early, and stays there for
    the rest of the process — so a module name that is *also* importable
    from a different, later-added root still resolves to whichever entry
    Python's import system reaches FIRST, exactly like `.pth`-vs-worktree
    here. This test reproduces that shape directly with two real directories
    and a real `sys.path` ordering — it does not invent a fake finder.

    STORY-180's actual failure: a discrimination proof run in a git worktree
    expected `src.*` to resolve to the WORKTREE's copy, but the `.pth` entry
    (pointing at the MAIN tree) was reached first, so both "sides" executed
    identical code and the proof reported green on both sides.

    Per finding B8 (sprint-64 plan verification): the trap must be proven
    LIVE before the helper is consulted — a plain `import` of the module
    really does resolve to the wrong root — otherwise the test only proves
    `Path.is_relative_to` works, not that the trap is caught.
    """
    main_tree_root = tmp_path / "main_tree"
    main_tree_root.mkdir()
    worktree_root = tmp_path / "worktree"
    worktree_root.mkdir()

    module_name = "_story187_ac3_probe"
    (main_tree_root / f"{module_name}.py").write_text(
        "ORIGIN = 'main_tree'\n", encoding="utf-8"
    )
    (worktree_root / f"{module_name}.py").write_text(
        "ORIGIN = 'worktree'\n", encoding="utf-8"
    )

    # Simulate the `.pth` entry: registered on sys.path FIRST, exactly as the
    # editable install's `.pth` is processed once at interpreter/site start,
    # ahead of anything a later worktree-scoped path insertion could add.
    sys.path.insert(0, str(main_tree_root))
    # The worktree's own copy is added AFTER — e.g. a later, well-intentioned
    # `PYTHONPATH`/`sys.path` addition meant to select the worktree's code.
    sys.path.insert(1, str(worktree_root))

    try:
        # First, prove the trap is LIVE: a plain import really resolves to
        # the WRONG root (the main tree), not the worktree the caller wanted
        # to test — this is finding B8, closing the "any stdlib module would
        # do" gap in the first draft of this gate.
        module = importlib.import_module(module_name)
        resolved_file = Path(module.__file__).resolve()
        assert resolved_file == (main_tree_root / f"{module_name}.py").resolve()
        assert resolved_file != (worktree_root / f"{module_name}.py").resolve()

        # Now the helper, told to expect the WORKTREE root, must catch it.
        with pytest.raises(WrongImportRootError) as excinfo:
            assert_import_root(module_name, expected_root=worktree_root)

        message = str(excinfo.value)
        assert str(worktree_root.resolve()) in message
        assert str(resolved_file) in message
    finally:
        sys.path.remove(str(main_tree_root))
        sys.path.remove(str(worktree_root))
        sys.modules.pop(module_name, None)
