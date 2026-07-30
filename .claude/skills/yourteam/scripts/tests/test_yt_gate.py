"""Self-tests for yt_gate.py — DoD parsing, tail sanitizing, evidence shape.

These pin the exact behaviors that broke (or nearly broke) in live use:
unicode in command output (sprint-44: cp1252 crash), heading-declared cwd,
and the evidence fragment's schema.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import yt_gate  # noqa: E402

DOD_SAMPLE = """# Definition of Done
## Commands (backend)
- [ ] Tests pass: `pytest` -> exit 0
- [x] Lint clean: `ruff check .` -> exit 0
      (a continuation line that is not a command)
- not a checkbox: `never-parsed`

## Commands (frontend — live, run from `frontend/`)
- [ ] Frontend tests pass: `npm test` -> exit 0

## Standing rules (never parsed as commands)
- [ ] Every acceptance criterion has a test: `not-a-gate-command`
"""


class ParseDodTests(unittest.TestCase):
    def _parse(self, text: str):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "dod.md"
            p.write_text(text, encoding="utf-8")
            return yt_gate.parse_dod(p)

    def test_parses_commands_with_labels(self):
        cmds = self._parse(DOD_SAMPLE)
        self.assertEqual(
            [c["command"] for c in cmds], ["pytest", "ruff check .", "npm test"]
        )
        self.assertEqual(cmds[0]["label"], "Tests pass")

    def test_heading_sets_section_cwd(self):
        cmds = self._parse(DOD_SAMPLE)
        self.assertEqual(cmds[0]["cwd"], "")
        self.assertEqual(cmds[2]["cwd"], "frontend")

    def test_non_commands_sections_are_ignored(self):
        cmds = self._parse(DOD_SAMPLE)
        self.assertNotIn("not-a-gate-command", [c["command"] for c in cmds])

    def test_checked_boxes_still_parse(self):
        self.assertIn("ruff check .", [c["command"] for c in self._parse(DOD_SAMPLE)])


class TailTests(unittest.TestCase):
    def test_unicode_survives(self):
        tail = yt_gate.one_line_tail("built ✓ in 491ms\n✓ done")
        self.assertIn("✓", tail)
        self.assertIn(" | ", tail)

    def test_quotes_and_backslashes_escaped(self):
        tail = yt_gate.one_line_tail('path "C:\\x" ok')
        self.assertIn('\\"', tail)
        self.assertIn("\\\\", tail)

    def test_truncates_to_limit(self):
        tail = yt_gate.one_line_tail("a" * 5000, limit=100)
        self.assertLessEqual(len(tail), 120)

    def test_ansi_escapes_and_control_chars_are_stripped(self):
        """Amendment A10 (retro sprint-65): the emitted tail must be YAML-safe.

        The fragment is merged into the sprint board VERBATIM, and YAML forbids
        raw C0 control characters outright -- one stray ESC makes the whole
        board unparseable. Motivating incident: a colourised frontend build log
        was pasted exactly as instructed and corrupted the board.
        """
        tail = yt_gate.one_line_tail("\x1b[32m✓ built\x1b[39m in 601ms\x07")

        self.assertNotIn("\x1b", tail)
        self.assertNotIn("\x07", tail)
        self.assertFalse(
            [ch for ch in tail if ch < " "],
            "no C0 control character may survive into the YAML fragment",
        )
        # The MESSAGE must survive -- stripping is not censoring.
        self.assertIn("built", tail)
        self.assertIn("601ms", tail)
        self.assertIn("✓", tail)

    def test_emitted_fragment_with_colourised_output_is_parseable_yaml(self):
        """End-to-end guard on A10: the real emitter, then a real YAML parse.

        `one_line_tail` being clean is necessary but not sufficient -- what
        actually broke was the FRAGMENT. Parsed with a hand-rolled check rather
        than PyYAML because this suite is deliberately stdlib-only, so the
        assertion is the one property YAML cares about here: no C0 controls.
        """
        fragment = yt_gate.emit_yaml(
            [
                {
                    "command": "npm run build",
                    "exit_code": 0,
                    "output_tail": yt_gate.one_line_tail(
                        "\x1b[32m✓ built\x1b[39m in 601ms"
                    ),
                    "at": "2026-07-30T00:00:00+00:00",
                }
            ],
            "abc1234",
        )

        self.assertFalse(
            [ch for ch in fragment if ch < " " and ch not in "\n\t"],
            "the emitted dod_evidence fragment must contain no raw control "
            "characters -- YAML rejects them and the board becomes unparseable",
        )


class EmitYamlTests(unittest.TestCase):
    def test_fragment_schema(self):
        frag = yt_gate.emit_yaml(
            [
                {
                    "command": 'python -c "x"',
                    "exit_code": 0,
                    "output_tail": "ok",
                    "at": "2026-01-01T00:00:00+00:00",
                }
            ],
            "abc1234",
        )
        self.assertTrue(frag.startswith("dod_evidence:"))
        self.assertIn('- command: "python -c \\"x\\""', frag)
        self.assertIn("exit_code: 0", frag)
        self.assertIn("commit: abc1234", frag)
        self.assertIn('at: "2026-01-01T00:00:00+00:00"', frag)


class FindRootTests(unittest.TestCase):
    def test_walks_up_to_scrum_dir(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / ".scrum").mkdir()
            nested = root / "a" / "b"
            nested.mkdir(parents=True)
            self.assertEqual(yt_gate.find_root(nested), root)

    def test_none_when_absent(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertIsNone(yt_gate.find_root(Path(td)))


if __name__ == "__main__":
    unittest.main()
