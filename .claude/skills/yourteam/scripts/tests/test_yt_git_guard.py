"""Self-tests for the git-guard hook — the block/allow matrix, end to end.

Runs the TEMPLATE copy (always present inside the skill) as a real subprocess
with JSON on stdin, exactly as the harness invokes it. Uses a throwaway git
repo per case. Covers: bulk-add block, wrong-branch commit block, scoped-add
allow, closed-sprint allow, non-git allow, and fail-open on garbage input.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parents[2] / "templates" / "hooks" / "yt_git_guard.py"


def run_hook(payload, cwd: Path | None = None) -> int:
    data = payload if isinstance(payload, str) else json.dumps(payload)
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input=data,
        capture_output=True,
        text=True,
        timeout=30,
        cwd=cwd or HOOK.parent,
    )
    return proc.returncode


class GuardMatrixTests(unittest.TestCase):
    def _fixture(
        self, td: str, status: str = "active", branch: str = "sprint-99"
    ) -> Path:
        root = Path(td)
        (root / ".scrum").mkdir()
        (root / ".scrum" / "sprint-current.yaml").write_text(
            f"sprint: 99\nstatus: {status}\nbranch: {branch}\n", encoding="utf-8"
        )
        subprocess.run(
            ["git", "init", "-q", "-b", "main", "."],
            cwd=root,
            capture_output=True,
            timeout=30,
        )
        return root

    def test_bulk_add_blocked_during_active_sprint(self):
        with tempfile.TemporaryDirectory() as td:
            root = self._fixture(td)
            cmd = {
                "tool_input": {"command": "git add -A && git commit -m x"},
                "cwd": str(root),
            }
            self.assertEqual(run_hook(cmd), 2)

    def test_commit_on_wrong_branch_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            root = self._fixture(td)  # repo on main; sprint branch is sprint-99
            cmd = {"tool_input": {"command": "git commit -m step"}, "cwd": str(root)}
            self.assertEqual(run_hook(cmd), 2)

    def test_scoped_add_allowed(self):
        with tempfile.TemporaryDirectory() as td:
            root = self._fixture(td)
            cmd = {
                "tool_input": {"command": "git add src/a.py tests/test_a.py"},
                "cwd": str(root),
            }
            self.assertEqual(run_hook(cmd), 0)

    def test_closed_sprint_allows_everything(self):
        with tempfile.TemporaryDirectory() as td:
            root = self._fixture(td, status="closed")
            cmd = {"tool_input": {"command": "git add -A"}, "cwd": str(root)}
            self.assertEqual(run_hook(cmd), 0)

    def test_non_git_command_allowed(self):
        with tempfile.TemporaryDirectory() as td:
            root = self._fixture(td)
            cmd = {"tool_input": {"command": "ls -la"}, "cwd": str(root)}
            self.assertEqual(run_hook(cmd), 0)

    def test_fail_open_on_garbage_stdin(self):
        self.assertEqual(run_hook("not json at all"), 0)


if __name__ == "__main__":
    unittest.main()
