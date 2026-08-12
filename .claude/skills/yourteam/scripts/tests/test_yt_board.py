"""Self-tests for yt_board.py — the backlog board generator.

Pins the two things that make the board trustworthy rather than merely pretty:

  1. AN UNESTIMATED STORY IS NEVER COUNTED AS ZERO. This is the defect the board was
     built to expose, not repeat: with 38 of 47 open stories unestimated, a naive sum
     reported "15 points remaining" against 47 stories, which reads as almost-done.
  2. --check FIRES AT SPRINT CLOSE ONLY. The board is a deliberate snapshot, so
     "differs from backlog.yaml" is the normal mid-sprint state; a check that fired
     then would be noise a reader learns to ignore.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import yt_board  # noqa: E402

BACKLOG = """\
next_story_id: 9
epics:
  alpha: Alpha epic
  omega: Omega epic (finished)
stories:
  - id: STORY-001
    title: done and estimated
    epic: alpha
    status: done
    points: 3
    type: chore
    file: docs/scrum/stories/STORY-001-x.md
  - id: STORY-002
    title: open and estimated
    epic: alpha
    status: ready
    points: 5
    type: feature
    file: docs/scrum/stories/STORY-002-x.md
  - id: STORY-003
    title: open with NO estimate
    epic: alpha
    status: draft
    type: feature
    file: null
  - id: STORY-004
    title: finished epic story
    epic: omega
    status: done
    points: 2
    type: chore
    file: docs/scrum/stories/STORY-004-x.md
  - id: STORY-005
    title: superseded, therefore terminal
    epic: omega
    status: superseded
    points: 1
    type: feature
    file: docs/scrum/stories/STORY-005-x.md
"""

SPRINT = "sprint: 42\nstories: []\n"


def _project(backlog: str = BACKLOG, sprint: str = SPRINT) -> Path:
    root = Path(tempfile.mkdtemp())
    (root / ".scrum").mkdir()
    (root / ".scrum" / "backlog.yaml").write_text(backlog, encoding="utf-8")
    (root / ".scrum" / "sprint-current.yaml").write_text(sprint, encoding="utf-8")
    return root


class PointsHonestyTests(unittest.TestCase):
    def test_missing_points_is_none_not_zero(self):
        self.assertIsNone(yt_board.points({"id": "S"}))
        self.assertIsNone(yt_board.points({"points": None}))
        self.assertIsNone(yt_board.points({"points": ""}))
        self.assertIsNone(yt_board.points({"points": "tbd"}))
        self.assertEqual(yt_board.points({"points": 5}), 5)
        self.assertEqual(yt_board.points({"points": "5"}), 5)

    def test_board_names_the_unestimated_count_and_refuses_a_total(self):
        board = yt_board.render(_project())
        self.assertIn("1 estimated (5 pts) + **1 unestimated**", board)
        self.assertIn("Total work remaining is NOT computable", board)

    def test_no_warning_when_every_open_story_is_estimated(self):
        backlog = BACKLOG.replace(
            "    title: open with NO estimate\n    epic: alpha\n    status: draft\n",
            "    title: now estimated\n    epic: alpha\n    status: draft\n    points: 2\n",
        )
        board = yt_board.render(_project(backlog))
        self.assertNotIn("NOT computable", board)
        self.assertIn("2 estimated (7 pts)", board)


class GroupingTests(unittest.TestCase):
    def test_finished_epic_collapses_out_of_open_work(self):
        board = yt_board.render(_project())
        open_section = board.split("## Complete")[0]
        self.assertIn("Alpha epic", open_section)
        self.assertNotIn("Omega epic", open_section)
        self.assertIn("Omega epic (finished)", board.split("## Complete")[1])

    def test_superseded_and_split_count_as_closed_not_open(self):
        # The work moved to another id; counting it open would double-count it.
        self.assertTrue(yt_board.is_closed({"status": "superseded"}))
        self.assertTrue(yt_board.is_closed({"status": "split"}))
        self.assertTrue(yt_board.is_closed({"status": "archived"}))
        self.assertFalse(yt_board.is_closed({"status": "draft"}))
        self.assertFalse(yt_board.is_closed({"status": "ready"}))
        self.assertFalse(yt_board.is_closed({"status": "blocked"}))

    def test_closed_total_counts_every_terminal_status(self):
        self.assertIn("3/5 stories closed", yt_board.render(_project()))

    def test_story_with_null_file_is_marked_not_linked(self):
        board = yt_board.render(_project())
        self.assertIn("STORY-003 _(no story file yet)_", board)
        self.assertIn("[STORY-002](docs/scrum/stories/STORY-002-x.md)", board)

    def test_bar_is_proportional(self):
        self.assertEqual(yt_board.bar(0, 4), "..........")
        self.assertEqual(yt_board.bar(4, 4), "##########")
        self.assertEqual(yt_board.bar(2, 4), "#####.....")
        self.assertEqual(yt_board.bar(0, 0), "..........")  # no ZeroDivisionError


class CheckTests(unittest.TestCase):
    """--check fires at sprint close, and NOT on ordinary mid-sprint backlog edits."""

    def _write_board(self, root: Path, text: str) -> None:
        board = root / yt_board.BOARD_REL
        board.parent.mkdir(parents=True, exist_ok=True)
        board.write_text(text, encoding="utf-8")

    def test_current_board_passes(self):
        root = _project()
        self._write_board(
            root, "**Snapshot at sprint-42, commit `abc1234`, generated x.**"
        )
        self.assertEqual(yt_board.check(root), 0)

    def test_board_from_a_previous_sprint_fails(self):
        root = _project()
        self._write_board(
            root, "**Snapshot at sprint-41, commit `abc1234`, generated x.**"
        )
        self.assertEqual(yt_board.check(root), 1)

    def test_backlog_edited_mid_sprint_does_NOT_fail(self):
        # The whole point of the snapshot design: the board lags and that is correct.
        root = _project()
        self._write_board(
            root, "**Snapshot at sprint-42, commit `abc1234`, generated x.**"
        )
        (root / ".scrum" / "backlog.yaml").write_text(
            BACKLOG + "  - id: STORY-006\n    title: filed mid-sprint\n"
            "    epic: alpha\n    status: draft\n    type: chore\n    file: null\n",
            encoding="utf-8",
        )
        self.assertEqual(yt_board.check(root), 0)

    def test_missing_board_fails(self):
        self.assertEqual(yt_board.check(_project()), 1)

    def test_board_without_a_snapshot_line_fails(self):
        root = _project()
        self._write_board(root, "# Backlog board\n\nsome hand-written thing\n")
        self.assertEqual(yt_board.check(root), 1)


class HtmlTests(unittest.TestCase):
    """The HTML board inherits the project's tokens; it never invents a palette."""

    def test_every_colour_token_is_defined_on_bare_root(self):
        # The classic unreadable-artifact bug: a colour whose ONLY definition sits
        # inside a media query or [data-theme] block never applies in the un-stamped
        # "system" state, so the page renders one theme's text on the other's ground.
        html = yt_board.render_html(_project())
        bare = html.split(":root{")[1].split("}")[0]
        for token in (
            "--canvas",
            "--s1",
            "--ink",
            "--accent",
            "--h-up",
            "--h-degraded",
        ):
            self.assertIn(token, bare, f"{token} missing from the bare :root block")
        self.assertIn("background:var(--canvas)", html)  # body paints its own ground

    def test_all_three_theme_states_are_covered(self):
        html = yt_board.render_html(_project())
        self.assertIn("@media (prefers-color-scheme:light)", html)
        self.assertIn(':root:not([data-theme="dark"])', html)
        self.assertIn(':root[data-theme="light"]', html)

    def test_no_external_requests(self):
        html = yt_board.render_html(_project())
        for bad in ("http://", "https://", "//fonts.", "<link"):
            self.assertNotIn(bad, html, f"artifact CSP forbids {bad}")

    def test_says_so_when_the_project_fonts_are_absent(self):
        html = yt_board.render_html(_project())  # tmpdir: no frontend/node_modules
        self.assertIn("system font stack", html)
        self.assertNotIn("@font-face", html)

    def test_titles_are_escaped(self):
        # Story titles are author-written text landing inside HTML. Single-quoted so the
        # fixture stays valid YAML — the first version of this test broke the parser
        # rather than the escaping, which proved nothing about escaping at all.
        backlog = BACKLOG.replace(
            "title: open and estimated", "title: '<script>alert(1)</script> & \"q\"'"
        )
        html = yt_board.render_html(_project(backlog))
        self.assertNotIn("<script>alert(1)</script>", html)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", html)
        self.assertIn("&amp;", html)

    def test_unestimated_story_is_labelled_not_zeroed(self):
        html = yt_board.render_html(_project())
        self.assertIn("unestimated", html)
        self.assertIn("not computable yet", html)


class CliTests(unittest.TestCase):
    def _run(self, root: Path, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(Path(yt_board.__file__)), *args],
            cwd=root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

    def test_stdout_mode_writes_no_file(self):
        root = _project()
        proc = self._run(root, "--stdout")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("# Backlog board", proc.stdout)
        self.assertFalse((root / yt_board.BOARD_REL).exists())

    def test_generate_writes_the_board(self):
        root = _project()
        proc = self._run(root)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue((root / yt_board.BOARD_REL).is_file())

    def test_html_flag_writes_both_outputs(self):
        root = _project()
        dest = root / "out" / "board.html"
        proc = self._run(root, "--html", str(dest))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue((root / yt_board.BOARD_REL).is_file())
        self.assertTrue(dest.is_file())
        self.assertIn("Backlog board", dest.read_text(encoding="utf-8"))

    def test_setup_error_outside_a_project(self):
        proc = self._run(Path(tempfile.mkdtemp()))
        self.assertEqual(proc.returncode, 4)
        self.assertIn("no .scrum/", proc.stderr)


if __name__ == "__main__":
    unittest.main()
