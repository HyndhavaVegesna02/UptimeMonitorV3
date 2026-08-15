"""Template↔instance parity — bootstrap copies must not drift silently.

Generic by construction: for each bootstrap-payload file that has an
instantiated counterpart in the enclosing project, the bytes must match;
where the project has no counterpart (fresh checkout, partial adoption),
the check skips cleanly. Divergence is legitimate ONLY via an explicit
version bump — which shows up here as a failure prompting the standup
drift-resync flow.
"""

from __future__ import annotations

import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[2]  # .../skills/yourteam


def project_root() -> Path | None:
    for p in SKILL.parents:
        if (p / ".scrum").is_dir():
            return p
    return None


PAIRS = [
    # Hooks are GLOBBED, not listed. A21 (sprint-72 retro) added a second hook and
    # the hardcoded single entry would have silently excluded it from parity -- the
    # test would have passed while the new hook drifted. Agents were already globbed;
    # this makes hooks self-maintaining the same way.
    *[
        (t, f".claude/hooks/{t.name}")
        for t in sorted((SKILL / "templates" / "hooks").glob("*.py"))
    ],
    *[
        (t, f".claude/agents/{t.name}")
        for t in sorted((SKILL / "templates" / "agents").glob("yt-*.md"))
    ],
]


class ParityTests(unittest.TestCase):
    def test_instantiated_copies_match_templates(self):
        root = project_root()
        if root is None:
            self.skipTest(
                "no enclosing project (.scrum) — nothing instantiated to compare"
            )
        mismatches = []
        for template, rel in PAIRS:
            instance = root / rel
            if not instance.exists():
                continue  # not instantiated here — fine (fresh/partial adoption)
            if template.read_bytes() != instance.read_bytes():
                mismatches.append(rel)
        self.assertEqual(
            mismatches,
            [],
            f"template/instance drift (run the standup re-sync): {mismatches}",
        )

    def test_bootstrap_payload_exists(self):
        self.assertTrue((SKILL / "templates" / "BOOTSTRAP.md").exists())
        self.assertGreaterEqual(
            len(list((SKILL / "templates" / "agents").glob("yt-*.md"))), 5
        )
        self.assertTrue(
            (SKILL / "templates" / "hooks" / "settings-fragment.json").exists()
        )
        self.assertGreaterEqual(
            len(list((SKILL / "templates" / "checklists").glob("*.md"))), 4
        )


if __name__ == "__main__":
    unittest.main()
