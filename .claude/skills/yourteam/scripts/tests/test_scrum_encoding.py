"""`.scrum/` state files must be valid UTF-8 with no replacement characters.

Generic by construction: the only contract assumed is the standard `.scrum/`
layout. Where a project has no `.scrum/` (fresh checkout, partial adoption),
the check skips cleanly.

WHY THIS EXISTS (STORY-188, sprint-65). `.scrum/` is read and rewritten by
every session, but NO gate command reads it -- the DoD's commands are all
test/lint/build tools pointed at source and infrastructure. So an encoding
defect there is invisible to the entire mechanical floor and can only be
caught by a human reading a diff.

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


def scrum_text_files(root: Path) -> list[Path]:
    files = []
    for p in sorted((root / ".scrum").rglob("*")):
        if not p.is_file():
            continue
        if p.suffix.lower() in SKIP_SUFFIXES:
            continue
        if any(part in SKIP_DIR_NAMES for part in p.parts):
            continue
        files.append(p)
    return files


class ScrumEncodingTests(unittest.TestCase):
    def test_scrum_files_are_valid_utf8(self):
        """No `.scrum/` file may contain a byte sequence that is not valid UTF-8."""
        root = project_root()
        if root is None:
            self.skipTest("no enclosing project with a .scrum/ directory")
        offenders = []
        for p in scrum_text_files(root):
            try:
                p.read_bytes().decode("utf-8")
            except UnicodeDecodeError as exc:
                offenders.append(
                    f"{p.relative_to(root).as_posix()}: {exc.reason} "
                    f"at byte {exc.start} ({hex(exc.object[exc.start])})"
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
        for p in scrum_text_files(root):
            try:
                text = p.read_bytes().decode("utf-8")
            except UnicodeDecodeError:
                continue  # reported by the sibling test; not double-counted here
            count = text.count(REPLACEMENT_CHAR)
            if count:
                offenders.append(f"{p.relative_to(root).as_posix()}: {count}")
        self.assertEqual(
            [],
            offenders,
            "U+FFFD REPLACEMENT CHARACTER in .scrum/ -- each one is a "
            "character that has ALREADY been destroyed and cannot be "
            "recovered from the file. Restore from git history:\n  "
            + "\n  ".join(offenders),
        )


if __name__ == "__main__":
    unittest.main()
