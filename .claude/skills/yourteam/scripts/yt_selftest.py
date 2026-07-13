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
    result = unittest.TextTestRunner(verbosity=verbosity).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
