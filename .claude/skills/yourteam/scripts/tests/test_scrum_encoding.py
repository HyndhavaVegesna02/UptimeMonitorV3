"""`.scrum/` state files must be valid UTF-8 with no replacement characters.

Generic by construction: the only contract assumed is the standard `.scrum/`
layout. Where a project has no `.scrum/` (fresh checkout, partial adoption),
the check skips cleanly.

WHY THIS EXISTS (STORY-188, sprint-65). `.scrum/` is read and rewritten by
every session. Originally NO gate command read it -- the DoD's commands were
all test/lint/build tools pointed at source and infrastructure -- so an
encoding defect there was invisible to the entire mechanical floor and could
only be caught by a human reading a diff.

CORRECTED (STORY-224 fix round, 2026-08-14): THIS test now IS a gate command
-- `yt_selftest.py` joined the DoD as its 9th command, and this module is one
of the suites it runs. That is what surfaced the CRITICAL this module also
fixes: reading the .scrum/ WORKING TREE from inside a gate command breaks the
soundness of the gate's own "commit: X" evidence stamp (see
`committed_or_working_scrum_files` below). This module reads the COMMITTED
tree at HEAD now, not the working tree, for exactly that reason.

It is not hypothetical. Two distinct corruptions accumulated undetected in
one project's `.scrum/`:

  - raw cp1252 `0x97` bytes (EM DASH written in the wrong codec), which make
    a file outright invalid UTF-8; and
  - `U+FFFD` REPLACEMENT CHARACTER, the residue of an earlier lossy
    round-trip -- data already destroyed, unrecoverable from the file itself.

The second class is the dangerous one: an edit pipeline that opens such a
file with `errors="replace"` and writes it back silently converts every
invalid byte into `U+FFFD`, corrupting text it was never asked to touch. In
the motivating incident that happened to a role checklist during an
unrelated story and was caught only because the author read `git diff`
before committing. The damaged files included the retro-landed process
rules -- so a silent loss there loses a RULE, not just a character.

Both classes are checked, because either alone is insufficient: a file can
be perfectly valid UTF-8 and still be full of `U+FFFD`.
"""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[2]  # .../skills/yourteam

REPLACEMENT_CHAR = "�"

#: Binary/derived files that legitimately are not UTF-8 text.
SKIP_SUFFIXES = {".pyc", ".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".db"}
SKIP_DIR_NAMES = {"__pycache__"}


def project_root() -> Path | None:
    for p in SKILL.parents:
        if (p / ".scrum").is_dir():
            return p
    return None


def _is_git_repo(root: Path) -> bool:
    return (root / ".git").exists()


def _skip(rel_path: str) -> bool:
    p = Path(rel_path)
    if p.suffix.lower() in SKIP_SUFFIXES:
        return True
    return any(part in SKIP_DIR_NAMES for part in p.parts)


def committed_or_working_scrum_files(root: Path) -> list[tuple[str, bytes]]:
    """[(relative_posix_path, content_bytes)] for every `.scrum/` text file.

    CRITICAL, STORY-224 fix round (both reviewers). This suite is now a gate
    command, so `yt_gate.py`'s A20 premise -- "`.scrum/` is read by NO gate
    command" -- is false for it. Walking the WORKING TREE let an uncommitted
    `.scrum/` edit change a result stamped `commit: X` in either direction: a
    real mojibake byte committed at X could be masked by an uncommitted
    working-tree fix ("dirty-tree-green" evidence -- demonstrated by the
    quality reviewer in a scratch repo), or the orchestrator's continuous,
    concurrent `.scrum/` edits (made even WHILE an agent's gate run is in
    flight) could red an unrelated agent's run -- precisely the box A20
    exists to remove.

    Reading the COMMITTED tree at HEAD instead makes `commit: X` in the
    gate's evidence mean what it says (soundness), and keeps A20's original
    intent (an uncommitted `.scrum/` edit cannot perturb a gate result) --
    both properties at once, with no exit-3 dirty-tree box reintroduced.

    Falls back to a working-tree walk OUTSIDE a git repository (no `.git`),
    so this module stays usable in a non-git checkout -- generic by
    construction, same as the rest of this suite.
    """
    if _is_git_repo(root):
        proc = subprocess.run(
            ["git", "ls-tree", "-r", "--name-only", "HEAD", "--", ".scrum"],
            cwd=root,
            capture_output=True,
            timeout=30,
        )
        if proc.returncode != 0:
            return []
        files = []
        for rel in sorted(proc.stdout.decode("utf-8", errors="replace").splitlines()):
            rel = rel.strip()
            if not rel or _skip(rel):
                continue
            show = subprocess.run(
                ["git", "show", f"HEAD:{rel}"],
                cwd=root,
                capture_output=True,
                timeout=30,
            )
            if show.returncode == 0:
                files.append((rel, show.stdout))
        return files
    files = []
    for p in sorted((root / ".scrum").rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(root).as_posix()
        if _skip(rel):
            continue
        files.append((rel, p.read_bytes()))
    return files


class ScrumEncodingTests(unittest.TestCase):
    def test_scrum_files_are_valid_utf8(self):
        """No `.scrum/` file may contain a byte sequence that is not valid UTF-8."""
        root = project_root()
        if root is None:
            self.skipTest("no enclosing project with a .scrum/ directory")
        offenders = []
        for rel, data in committed_or_working_scrum_files(root):
            try:
                data.decode("utf-8")
            except UnicodeDecodeError as exc:
                offenders.append(
                    f"{rel}: {exc.reason} at byte {exc.start} "
                    f"({hex(exc.object[exc.start])})"
                )
        self.assertEqual(
            [],
            offenders,
            "Invalid UTF-8 in .scrum/ (cp1252 bytes are the usual cause; an "
            "edit pipeline that round-trips these files WILL silently corrupt "
            "untouched text):\n  " + "\n  ".join(offenders),
        )

    def test_scrum_files_contain_no_replacement_characters(self):
        """No `.scrum/` file may contain U+FFFD -- that is already-lost data."""
        root = project_root()
        if root is None:
            self.skipTest("no enclosing project with a .scrum/ directory")
        offenders = []
        for rel, data in committed_or_working_scrum_files(root):
            try:
                text = data.decode("utf-8")
            except UnicodeDecodeError:
                continue  # reported by the sibling test; not double-counted here
            count = text.count(REPLACEMENT_CHAR)
            if count:
                offenders.append(f"{rel}: {count}")
        self.assertEqual(
            [],
            offenders,
            "U+FFFD REPLACEMENT CHARACTER in .scrum/ -- each one is a "
            "character that has ALREADY been destroyed and cannot be "
            "recovered from the file. Restore from git history:\n  "
            + "\n  ".join(offenders),
        )


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
    """CRITICAL, STORY-224 fix round -- same reasoning as
    `test_backlog_story_parity.py::CommittedHeadReadTests`.

    Falsified by: a committed-vs-working-tree divergence producing the
    working tree's answer instead of the committed one.
    """

    def _repo(self, filename: str, content: bytes) -> Path:
        root = Path(tempfile.mkdtemp())
        _init_git_repo(root)
        (root / ".scrum").mkdir()
        (root / ".scrum" / filename).write_bytes(content)
        _commit_all(root, "init")
        return root

    def test_uncommitted_mojibake_is_not_seen(self) -> None:
        root = self._repo("x.md", b"clean ascii text\n")
        # Dirty the working tree only, with the EXACT byte STORY-188 chased --
        # deliberately NOT committed.
        (root / ".scrum" / "x.md").write_bytes(b"an em dash \x97 written wrong\n")
        files = dict(committed_or_working_scrum_files(root))
        self.assertEqual(files[".scrum/x.md"], b"clean ascii text\n")

    def test_a_committed_mojibake_byte_IS_seen(self) -> None:
        root = self._repo("x.md", b"clean ascii text\n")
        (root / ".scrum" / "x.md").write_bytes(b"an em dash \x97 written wrong\n")
        _commit_all(root, "corrupt")
        files = dict(committed_or_working_scrum_files(root))
        self.assertEqual(files[".scrum/x.md"], b"an em dash \x97 written wrong\n")

    def test_non_git_directory_falls_back_to_the_working_tree(self) -> None:
        root = Path(tempfile.mkdtemp())
        (root / ".scrum").mkdir()
        (root / ".scrum" / "x.md").write_bytes(b"hello\n")
        files = dict(committed_or_working_scrum_files(root))
        self.assertEqual(files[".scrum/x.md"], b"hello\n")


if __name__ == "__main__":
    unittest.main()
