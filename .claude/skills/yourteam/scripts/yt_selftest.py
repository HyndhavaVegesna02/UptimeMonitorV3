#!/usr/bin/env python3
"""YourTeam v2 skill self-test (yourteam_version: 2.1.0).

Runs the test suite for the skill's OWN enforcement scripts (yt_gate, yt_wiki,
the git-guard hook, template/instance parity). Stdlib-only (unittest) so it
works in any project regardless of stack. Run at every standup — a red here
means the mechanical floor itself is broken and must be fixed before it gates
anything (sprint-44 retro amendment #1: the gate gets a gate).

Usage: python yt_selftest.py [-v]
Exit codes: 0 all green; 1 failures; 4 setup error.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

#: STORY-224 AC4: `unittest` discovery fails SILENTLY when a module stops
#: being discovered -- an import error surfaces as a loud synthetic failing
#: test, but a rename or a file falling outside the `test_*.py` glob makes
#: the count drop with no error at all. Once this script is a gate command
#: (AC1), that silent drop must fail the RUN, not just change what the next
#: standup happens to see. 7 is the module count at STORY-224 refinement.
MIN_TEST_MODULES = 7


def _module_names(suite: unittest.TestSuite) -> set[str]:
    """Unique `__module__` names of every test case inside a (nested) suite."""
    names: set[str] = set()
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            names |= _module_names(item)
        else:
            names.add(type(item).__module__)
    return names


def discovered_test_modules(tests_dir: Path) -> set[str]:
    """Names of the test modules `unittest` discovery finds under `tests_dir`."""
    suite = unittest.defaultTestLoader.discover(
        start_dir=str(tests_dir), pattern="test_*.py"
    )
    return _module_names(suite)


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    tests_dir = Path(__file__).resolve().parent / "tests"
    if not tests_dir.is_dir():
        print(f"yt_selftest: tests dir not found: {tests_dir}", file=sys.stderr)
        return 4
    verbosity = 2 if "-v" in sys.argv else 1
    suite = unittest.defaultTestLoader.discover(
        start_dir=str(tests_dir), pattern="test_*.py"
    )
    modules = _module_names(suite)
    if len(modules) < MIN_TEST_MODULES:
        print(
            f"yt_selftest: only {len(modules)} test module(s) discovered under "
            f"{tests_dir} (expected at least {MIN_TEST_MODULES}) -- discovery "
            "drops silently on a rename or a file falling outside the "
            f"`test_*.py` pattern. Discovered: {sorted(modules)}",
            file=sys.stderr,
        )
        return 1
    result = unittest.TextTestRunner(verbosity=verbosity).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
