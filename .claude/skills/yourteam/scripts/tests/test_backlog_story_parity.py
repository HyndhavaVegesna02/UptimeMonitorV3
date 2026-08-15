"""Backlog entries and story files must not drift apart.

Generic by construction: the only contract assumed is the standard layout —
`.scrum/backlog.yaml` with a `stories` list, and story files under
`docs/scrum/stories/`. Where a project has neither, the check skips cleanly.

WHY THIS EXISTS (sprint-66 retro, amendment A11). The skill's own file map says
"one file per story, never moves" — but nothing enforced it, and the two states
drift in opposite directions with different consequences:

  - a `file:` pointing at a path that does not exist is ALWAYS wrong. It is a
    broken pointer: planning follows it, finds nothing, and the story's detail
    is simply lost. This is a hard failure.

  - a story file with NO backlog entry is an orphan. The backlog is what
    planning reads, so an orphan file is invisible to the process that decides
    what gets built — it can sit on disk for sprints. Also a hard failure.

  - an entry with `file: null` is NOT an error. A freshly-filed draft
    legitimately has no file until refinement writes one, and several projects
    file that way deliberately. It is reported as a NOTE so the count stays
    visible, because the failure mode is quiet accumulation, not any single
    entry.

The motivating incident (sprint 66): an audit sprint filed thirteen stories.
Four got story files; NINE existed only as backlog entries, with their actual
detail spread across two sprint reports and a YAML comment block. Every one was
findable at planning and invisible in `docs/scrum/stories/`. Nobody noticed
until the PO went looking for them and could not find them — which is exactly
the kind of gap a mechanical check should catch instead of a human.
"""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[2]  # .../skills/yourteam
sys.path.insert(0, str(SKILL / "scripts"))
import yt_board  # noqa: E402

STORY_ID_RE = re.compile(r"^STORY-(\d+)", re.IGNORECASE)


def project_root() -> Path | None:
    for p in SKILL.parents:
        if (p / ".scrum").is_dir():
            return p
    return None


def _is_git_repo(root: Path) -> bool:
    return (root / ".git").exists()


def read_committed_scrum_file(root: Path, rel_path: str):
    """Text of a `.scrum/` file as COMMITTED at HEAD, or None if unreadable.

    CRITICAL, STORY-224 fix round (both reviewers). This suite is now a gate
    command (AC1), so `yt_gate.py`'s A20 premise -- "`.scrum/` is read by NO
    gate command" -- is false for it. Reading the WORKING TREE let an
    uncommitted `.scrum/` edit change a result stamped `commit: X` in either
    direction: a real defect committed at X could be masked by an
    uncommitted working-tree fix ("dirty-tree-green" evidence -- demonstrated
    by the quality reviewer in a scratch repo), or the orchestrator's
    continuous, concurrent `.scrum/` edits (made even WHILE an agent's gate
    run is in flight) could red an unrelated agent's run -- precisely the box
    A20 exists to remove.

    Reading the COMMITTED blob instead makes `commit: X` in the gate's
    evidence mean what it says (soundness), and keeps A20's original intent
    (an uncommitted `.scrum/` edit cannot perturb a gate result) -- both
    properties at once, with no exit-3 dirty-tree box reintroduced.

    Falls back to a plain working-tree read OUTSIDE a git repository (no
    `.git`), so this module stays usable in a non-git checkout -- this suite
    is generic by construction. A path not tracked at HEAD (inside a git
    repo) is treated as absent, not as "read the working tree instead": a
    file that exists only in the working tree has not been committed, so it
    is not part of "what commit X contains" either.
    """
    if _is_git_repo(root):
        proc = subprocess.run(
            ["git", "show", f"HEAD:{rel_path}"],
            cwd=root,
            capture_output=True,
            timeout=30,
        )
        if proc.returncode != 0:
            return None
        return proc.stdout.decode("utf-8", errors="replace")
    path = root / rel_path
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8", errors="replace")


def load_backlog(root: Path):
    """Return the backlog's story list, or None when it cannot be read.

    Uses PyYAML when available and falls back to a line scan otherwise, so the
    check still works in a stdlib-only environment (the rest of this suite is
    stdlib-only by rule). Reads the COMMITTED `.scrum/backlog.yaml` -- see
    `read_committed_scrum_file`.
    """
    text = read_committed_scrum_file(root, ".scrum/backlog.yaml")
    if text is None:
        return None
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(text)
        if isinstance(data, dict) and isinstance(data.get("stories"), list):
            return [s for s in data["stories"] if isinstance(s, dict)]
    except Exception:
        pass
    # Fallback: pair each `- id:` with the `file:` that follows it.
    stories = []
    current = None
    for line in text.splitlines():
        m = re.match(r"\s*-\s+id:\s*(\S+)", line)
        if m:
            if current:
                stories.append(current)
            current = {"id": m.group(1).strip(), "file": None}
            continue
        if current is not None:
            m2 = re.match(r"\s*file:\s*(.+?)\s*$", line)
            if m2 and current.get("file") is None:
                val = m2.group(1)
                current["file"] = None if val in ("null", "~", "") else val
    if current:
        stories.append(current)
    return stories


def load_next_story_id(root: Path):
    """Return the backlog's `next_story_id`, or None when it cannot be read.

    Same PyYAML-with-fallback shape as `load_backlog` -- this suite stays
    stdlib-only-capable. Reads the COMMITTED `.scrum/backlog.yaml` -- see
    `read_committed_scrum_file`.
    """
    text = read_committed_scrum_file(root, ".scrum/backlog.yaml")
    if text is None:
        return None
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(text)
        if isinstance(data, dict) and isinstance(data.get("next_story_id"), int):
            return data["next_story_id"]
    except Exception:
        pass
    m = re.search(r"^next_story_id:\s*(\d+)", text, re.MULTILINE)
    return int(m.group(1)) if m else None


def max_filed_story_id(stories: list) -> int:
    """The highest numeric id across `stories`, parsed by NUMERIC PREFIX.

    AC8 trap: thirteen filed ids carry a non-numeric suffix (STORY-014b,
    015a..015g, 040a, 016a..016c). `STORY_ID_RE` matches only the leading
    digits, so a suffixed id contributes its numeric prefix and never raises.
    """
    ids = []
    for s in stories:
        m = STORY_ID_RE.match(str(s.get("id", "")))
        if m:
            ids.append(int(m.group(1)))
    return max(ids) if ids else 0


def entries_missing_file(stories: list) -> list:
    """Backlog entries with no `file:` pointer, excluding the CLOSED set.

    AC7 (STORY-224): this previously filtered on `status != "done"`, so 22+
    archived/superseded/split entries -- CLOSED per `yt_board.CLOSED_STATUSES`,
    just not literally "done" -- sat in the "refinement should write one"
    advisory forever. Reuses `yt_board.py`'s existing closed set rather than
    declaring a second list.
    """
    return [
        str(s.get("id"))
        for s in stories
        if not s.get("file")
        and str(s.get("status", "")).strip() not in yt_board.CLOSED_STATUSES
    ]


def load_board_statuses(root: Path):
    """`{story_id: status}` from the COMMITTED sprint board, or None.

    PyYAML only: the board's `status` lives one level inside a `board:` list of
    mappings, and a line scan for a nested key that also appears at the top of
    the same file (the SPRINT's own `status:`) is the kind of fragile parse this
    module exists to catch, not to commit. When PyYAML is absent the caller
    skips rather than guessing -- a check that cannot read its input must not
    report a verdict about it.
    """
    text = read_committed_scrum_file(root, ".scrum/sprint-current.yaml")
    if text is None:
        return None
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(text)
    except Exception:
        return None
    if not isinstance(data, dict) or not isinstance(data.get("board"), list):
        return None
    return {
        str(e["id"]): str(e.get("status", ""))
        for e in data["board"]
        if isinstance(e, dict) and e.get("id")
    }


def load_backlog_statuses(root: Path):
    """`{story_id: status}` from the COMMITTED backlog, or None. PyYAML only."""
    text = read_committed_scrum_file(root, ".scrum/backlog.yaml")
    if text is None:
        return None
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(text)
    except Exception:
        return None
    if not isinstance(data, dict) or not isinstance(data.get("stories"), list):
        return None
    return {
        str(s["id"]): str(s.get("status", ""))
        for s in data["stories"]
        if isinstance(s, dict) and s.get("id")
    }


def board_backlog_done_drift(board: dict, backlog: dict) -> list:
    """Stories the BOARD calls `done` that the BACKLOG does not. One-way.

    Deliberately asymmetric. Board-`done` implies backlog-`done`; the converse
    is NOT asserted, because a backlog entry may legitimately be `done` from an
    earlier sprint while this sprint's board never mentions it. Do not
    "tighten" this into a symmetry -- it would fire on every sprint.

    A board id absent from the backlog is skipped here rather than reported:
    that is a different defect (orphan board entry) and conflating the two
    produces a message that names the wrong fix.
    """
    drift = []
    for sid, board_status in sorted(board.items()):
        if board_status != "done":
            continue
        actual = backlog.get(sid)
        if actual is None or actual == "done":
            continue
        drift.append(f"{sid}: board=done but backlog={actual}")
    return drift


class BacklogStoryParityTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = project_root()
        if self.root is None:
            self.skipTest(
                "no .scrum/ directory found — project has not adopted YourTeam"
            )
        self.stories = load_backlog(self.root)
        if self.stories is None:
            self.skipTest("no .scrum/backlog.yaml to check")

    def test_every_file_pointer_resolves(self) -> None:
        """A `file:` that names a path must name one that EXISTS."""
        broken = []
        for s in self.stories:
            ref = s.get("file")
            if not ref or not isinstance(ref, str):
                continue
            if not (self.root / ref).is_file():
                broken.append(f"{s.get('id')}: file: {ref} does not exist")
        self.assertEqual(
            [],
            broken,
            "Backlog entries point at story files that are not on disk. Planning "
            "follows these pointers, so a broken one loses the story's detail "
            "entirely. Either create the file or set `file: null`:\n  "
            + "\n  ".join(broken),
        )

    def test_no_orphan_story_files(self) -> None:
        """A story file must have a backlog entry, or planning cannot see it."""
        stories_dir = self.root / "docs" / "scrum" / "stories"
        if not stories_dir.is_dir():
            self.skipTest("no docs/scrum/stories/ directory")
        known = set()
        for s in self.stories:
            m = STORY_ID_RE.match(str(s.get("id", "")))
            if m:
                known.add(int(m.group(1)))
        orphans = []
        for path in sorted(stories_dir.glob("STORY-*.md")):
            m = STORY_ID_RE.match(path.name)
            if not m:
                continue
            if int(m.group(1)) not in known:
                orphans.append(path.name)
        self.assertEqual(
            [],
            orphans,
            "Story files exist with no entry in .scrum/backlog.yaml. The backlog "
            "is what planning reads, so these are invisible to it and can sit "
            "unbuilt for sprints:\n  " + "\n  ".join(orphans),
        )

    def test_report_entries_without_a_file(self) -> None:
        """ADVISORY: entries with `file: null` are counted, never failed.

        A freshly-filed draft legitimately has no file until refinement writes
        one. The hazard is quiet accumulation — a dozen stories whose detail
        lives only in a YAML comment — so the count is printed and the test
        always passes.
        """
        missing = entries_missing_file(self.stories)
        if missing:
            print(
                f"\n  note: {len(missing)} not-done backlog entr"
                f"{'y has' if len(missing) == 1 else 'ies have'} no story file "
                f"(fine for fresh drafts; refinement should write one): "
                + ", ".join(missing[:12])
                + (" ..." if len(missing) > 12 else "")
            )
        self.assertTrue(True)


class ClosedSetAdvisoryTests(unittest.TestCase):
    """AC7 (STORY-224): the advisory's filter uses the FULL closed set.

    Falsified by: an archived/superseded/split entry with no `file:` pointer
    still appearing in `entries_missing_file`'s output.
    """

    def test_archived_entry_with_no_file_is_excluded(self) -> None:
        stories = [
            {"id": "STORY-001", "status": "archived", "file": None},
            {"id": "STORY-002", "status": "superseded", "file": None},
            {"id": "STORY-003", "status": "split", "file": None},
            {"id": "STORY-004", "status": "done", "file": None},
            {"id": "STORY-005", "status": "draft", "file": None},
        ]
        self.assertEqual(entries_missing_file(stories), ["STORY-005"])

    def test_closed_statuses_constant_covers_the_known_terminal_statuses(self) -> None:
        """Sanity check on the CONSTANT alone -- does not exercise delegation.

        See `test_entries_missing_file_actually_reads_yt_board_closed_statuses`
        below for the test that proves `entries_missing_file` reuses this
        constant rather than a parallel hardcoded copy.
        """
        self.assertTrue(
            yt_board.CLOSED_STATUSES.issuperset(
                {"archived", "superseded", "split", "done"}
            )
        )

    def test_entries_missing_file_actually_reads_yt_board_closed_statuses(self) -> None:
        """MINOR, STORY-224 fix round (quality reviewer).

        The renamed test above proves nothing about `entries_missing_file` --
        replacing its `yt_board.CLOSED_STATUSES` reference with a copied
        literal `{"done", "superseded", "archived", "split"}` left the whole
        suite green (`Ran 99 tests ... OK`). This monkeypatches the shared
        constant and checks the EFFECT propagates through
        `entries_missing_file`, which only a real attribute lookup (not a
        hardcoded copy) can produce.

        Falsified by: `entries_missing_file` internally using a literal set
        instead of `yt_board.CLOSED_STATUSES` -- this patch would then have
        no effect and the assertion below would fail.
        """
        original = yt_board.CLOSED_STATUSES
        try:
            yt_board.CLOSED_STATUSES = frozenset({"totally_custom_closed_status"})
            stories = [
                # Closed only under the PATCHED set -- must be excluded.
                {
                    "id": "STORY-001",
                    "status": "totally_custom_closed_status",
                    "file": None,
                },
                # "archived" is closed under the REAL constant but not the
                # patched one -- must now be INCLUDED if delegation is real.
                {"id": "STORY-002", "status": "archived", "file": None},
            ]
            self.assertEqual(entries_missing_file(stories), ["STORY-002"])
        finally:
            yt_board.CLOSED_STATUSES = original


class NextStoryIdCounterTests(unittest.TestCase):
    """AC8 (STORY-224): `next_story_id` must stay ahead of every filed id.

    TRAP (pre-lock verification): thirteen ids are NOT purely numeric --
    STORY-014b, 014c, 015a..015g, 040a, 016a..016c. `int(sid.split("-")[1])`
    raises ValueError on the first of them, reddening the gate for a reason
    that has nothing to do with the counter. `max_filed_story_id` parses with
    `STORY_ID_RE`'s numeric-PREFIX match instead, and this suite pins a
    suffixed id explicitly so that trap cannot silently return.
    """

    def setUp(self) -> None:
        self.root = project_root()
        if self.root is None:
            self.skipTest("no .scrum/ directory found")
        self.stories = load_backlog(self.root)
        if self.stories is None:
            self.skipTest("no .scrum/backlog.yaml to check")
        self.next_id = load_next_story_id(self.root)
        if self.next_id is None:
            self.skipTest("no next_story_id in .scrum/backlog.yaml")

    def test_next_story_id_exceeds_every_filed_numeric_id(self) -> None:
        max_id = max_filed_story_id(self.stories)
        self.assertGreater(
            self.next_id,
            max_id,
            f"next_story_id ({self.next_id}) does not exceed the max filed id "
            f"({max_id}) -- the next filing would collide with an existing story.",
        )

    def test_suffixed_id_parses_by_numeric_prefix_without_raising(self) -> None:
        """The trap: a naive int(sid.split('-')[1]) raises on 'STORY-014b'."""
        max_id = max_filed_story_id(
            [
                {"id": "STORY-014b"},
                {"id": "STORY-015g"},
                {"id": "STORY-040a"},
                {"id": "STORY-099"},
            ]
        )
        self.assertEqual(max_id, 99)

    def test_empty_story_list_has_max_id_zero(self) -> None:
        self.assertEqual(max_filed_story_id([]), 0)


def _init_git_repo(root: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "t@t"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "t"], cwd=root, check=True, capture_output=True
    )


def _commit_all(root: Path, message: str) -> None:
    subprocess.run(["git", "add", "-A"], cwd=root, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-q", "-m", message],
        cwd=root,
        check=True,
        capture_output=True,
    )


class CommittedHeadReadTests(unittest.TestCase):
    """CRITICAL, STORY-224 fix round (both reviewers).

    This suite is now a gate command (AC1), so `yt_gate.py`'s A20 premise --
    "`.scrum/` is read by NO gate command" -- is false for it. Reading the
    WORKING TREE let an uncommitted `.scrum/` edit change a result stamped
    `commit: X` in either direction: a real defect committed at X could be
    masked by an uncommitted working-tree fix (dirty-tree-green evidence,
    demonstrated by the quality reviewer), or the orchestrator's continuous,
    concurrent `.scrum/` edits could red an unrelated agent's run -- exactly
    the box A20 exists to remove. `load_backlog`/`load_next_story_id` now
    read the COMMITTED blob at HEAD, falling back to the working tree only
    outside a git repository.

    Falsified by: a committed-vs-working-tree divergence producing the
    working tree's answer instead of the committed one.
    """

    def _repo(self, backlog_text: str) -> Path:
        root = Path(tempfile.mkdtemp())
        _init_git_repo(root)
        (root / ".scrum").mkdir()
        (root / ".scrum" / "backlog.yaml").write_text(backlog_text, encoding="utf-8")
        _commit_all(root, "init")
        return root

    def test_uncommitted_edit_does_not_change_the_result(self) -> None:
        root = self._repo("next_story_id: 5\nstories: []\n")
        # Dirty the working tree only -- deliberately NOT committed.
        (root / ".scrum" / "backlog.yaml").write_text(
            "next_story_id: 999\nstories: []\n", encoding="utf-8"
        )
        self.assertEqual(load_next_story_id(root), 5)

    def test_uncommitted_edit_does_not_change_the_stories_list_either(self) -> None:
        root = self._repo(
            "next_story_id: 2\nstories:\n  - id: STORY-001\n    file: null\n"
        )
        (root / ".scrum" / "backlog.yaml").write_text(
            "next_story_id: 2\nstories:\n"
            "  - id: STORY-001\n    file: null\n"
            "  - id: STORY-999\n    file: null\n",
            encoding="utf-8",
        )
        stories = load_backlog(root)
        self.assertEqual([s["id"] for s in stories], ["STORY-001"])

    def test_a_committed_edit_IS_seen(self) -> None:
        root = self._repo("next_story_id: 5\nstories: []\n")
        (root / ".scrum" / "backlog.yaml").write_text(
            "next_story_id: 6\nstories: []\n", encoding="utf-8"
        )
        _commit_all(root, "bump")
        self.assertEqual(load_next_story_id(root), 6)

    def test_non_git_directory_falls_back_to_the_working_tree(self) -> None:
        root = Path(tempfile.mkdtemp())
        (root / ".scrum").mkdir()
        (root / ".scrum" / "backlog.yaml").write_text(
            "next_story_id: 42\nstories: []\n", encoding="utf-8"
        )
        self.assertEqual(load_next_story_id(root), 42)


class BoardBacklogStatusParityTests(unittest.TestCase):
    """A story the sprint board calls DONE must be DONE in the backlog.

    Landed 2026-08-15 as enforcement-ladder work (A14 exempts the ladder from
    the tooling freeze), NOT as a story -- one assertion at a rung that already
    runs in the gate is an owed one-liner, not backlog.

    THE OCCURRENCE, and it is not hypothetical: on 2026-08-15, one day after
    sprint 72 closed, `sprint-current.yaml` recorded STORY-221, STORY-224 and
    STORY-173 as `done` and PO-ACCEPTED, while `backlog.yaml` -- the file the
    skill calls "the source of truth for story status" -- still said `ready`
    for all three. The full 9-command gate was green at every one of those
    commits, because nothing compared the two files. Planning then read the
    backlog and offered all three as candidates for the next sprint.

    Root cause: the two files are written by the same actor at different
    moments (the board at each transition, the backlog at close) and nothing
    tied the second write to the first. "Remember to update both" is the prose
    rung; this is the rung below it.
    """

    def test_board_done_implies_backlog_done(self):
        root = project_root()
        if root is None:
            self.skipTest("no enclosing project (.scrum)")
        board = load_board_statuses(root)
        backlog = load_backlog_statuses(root)
        if board is None or backlog is None:
            self.skipTest("board or backlog unreadable at HEAD (PyYAML absent?)")
        drift = board_backlog_done_drift(board, backlog)
        self.assertEqual(
            drift,
            [],
            "sprint board and backlog disagree about completed work. The backlog "
            "is the source of truth for story status, so it is the file to fix: "
            "set these entries to `done` in .scrum/backlog.yaml. " + str(drift),
        )

    def test_mid_sprint_states_do_not_trip_it(self):
        """The half that decides whether this guard is worth having.

        A gate command that reds on ordinary bookkeeping trains people to
        discount reds -- which is what STORY-221 spent three points on. Every
        legitimate mid-sprint combination must stay green.
        """
        backlog = {"STORY-1": "ready", "STORY-2": "ready", "STORY-3": "blocked"}
        for board_status in ("todo", "in_progress", "dropped", "blocked", "review"):
            with self.subTest(board_status=board_status):
                self.assertEqual(
                    board_backlog_done_drift({"STORY-1": board_status}, backlog), []
                )

    def test_board_entry_absent_from_backlog_is_not_reported_here(self):
        self.assertEqual(
            board_backlog_done_drift({"STORY-999": "done"}, {"STORY-1": "ready"}), []
        )

    def test_backlog_done_without_a_board_entry_is_not_drift(self):
        """The asymmetry, pinned so it is not 'fixed' into a symmetry later."""
        self.assertEqual(board_backlog_done_drift({}, {"STORY-1": "done"}), [])

    def test_the_real_drift_is_detected_and_named(self):
        """Shown RED against the exact 2026-08-15 occurrence.

        STORY-173 is `done` in both files here on purpose: it proves the check
        reports only the entries that actually drifted, not every done story on
        the board.
        """
        drift = board_backlog_done_drift(
            {"STORY-221": "done", "STORY-224": "done", "STORY-173": "done"},
            {"STORY-221": "ready", "STORY-224": "ready", "STORY-173": "done"},
        )
        self.assertEqual(
            drift,
            [
                "STORY-221: board=done but backlog=ready",
                "STORY-224: board=done but backlog=ready",
            ],
        )


if __name__ == "__main__":
    unittest.main()
