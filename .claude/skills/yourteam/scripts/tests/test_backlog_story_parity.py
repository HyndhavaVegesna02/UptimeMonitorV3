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
import sys
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


def load_backlog(root: Path):
    """Return the backlog's story list, or None when it cannot be read.

    Uses PyYAML when available and falls back to a line scan otherwise, so the
    check still works in a stdlib-only environment (the rest of this suite is
    stdlib-only by rule).
    """
    path = root / ".scrum" / "backlog.yaml"
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
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

    def test_reuses_yt_board_closed_statuses_not_a_second_list(self) -> None:
        self.assertTrue(
            yt_board.CLOSED_STATUSES.issuperset(
                {"archived", "superseded", "split", "done"}
            )
        )


if __name__ == "__main__":
    unittest.main()
