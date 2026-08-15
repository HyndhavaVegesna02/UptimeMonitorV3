#!/usr/bin/env python3
"""YourTeam Window Check (yourteam_version: 2.3.0).

PreToolUse hook for agent dispatch. Reads the session's rate-limit window and
decides whether another subagent may be started, so a long agent run is never
begun inside a window that cannot finish it.

Landed as amendment A21 (sprint-72 retro, PO-approved 2026-08-15). This is a
RELOCATION of the PO-stated rule of 2026-07-29, not a new rule: the thresholds
and the data source are unchanged, only the rung is. The prose entry it
replaces was deleted in the same commit -- routing down the ladder is not
deletion (A15 s3), so keeping both would have kept the cost and the drift.

Why a hook rather than the script rung the original rule named for itself: the
rule's content is "read the window BEFORE dispatching an agent", and a
PreToolUse hook on the dispatch tool is that sentence mechanically. A script
still has to be remembered. The evidence it was not: the rule existed for nine
sprints and was run zero times across seven agent boundaries in sprint 72,
during which two agents died on the limit -- one of them costing that sprint
its last story.

Thresholds (verbatim from the 2026-07-29 rule):

    five_hour.used_percentage  < 85  -> allow silently
                              85-94  -> allow, but warn: finish work already in
                                        flight, do not start a new story
                              >= 95  -> BLOCK; park until resets_at and resume
                                        from the board
    seven_day.used_percentage >= 90  -> warn only, never block: a 7-day reset
                                        cannot be waited out inside a session,
                                        so the PO must be told instead

FAILS OPEN by construction. A missing, stale, or malformed statusline file
allows the dispatch with a note. This guard is a backstop, never an outage --
the same contract as yt_git_guard.py.

Project-generic (PO directive 2026-07-13): `~/.claude/statusline-latest.json`
is a Claude Code artifact, not a project one, and nothing here knows the
project's name, stack, or layout.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

STATUSLINE = Path(os.path.expanduser("~")) / ".claude" / "statusline-latest.json"

PARK_AT = 95
WARN_AT = 85
SEVEN_DAY_WARN_AT = 90


def _reset_clock(epoch: object) -> str:
    """`resets_at` as a local HH:MM string, or '?' if it is not a timestamp."""
    try:
        return time.strftime("%H:%M", time.localtime(float(epoch)))  # type: ignore[arg-type]
    except (TypeError, ValueError, OSError):
        return "?"


def main() -> int:
    try:
        raw = json.loads(STATUSLINE.read_text(encoding="utf-8"))
        limits = raw["rate_limits"]
        five = limits["five_hour"]
        used = float(five["used_percentage"])
        resets = _reset_clock(five.get("resets_at"))
        seven = float(limits.get("seven_day", {}).get("used_percentage", 0))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(
            f"yt_window_check: statusline unreadable ({exc.__class__.__name__}) -- "
            f"allowing dispatch. Read the window by hand if this persists: {STATUSLINE}",
            file=sys.stderr,
        )
        return 0

    if seven >= SEVEN_DAY_WARN_AT:
        print(
            f"yt_window_check: 7-day window at {seven:.0f}% -- TELL THE PO. A 7-day "
            "reset cannot be waited out inside a session, so parking will not help.",
            file=sys.stderr,
        )

    if used >= PARK_AT:
        print(
            f"yt_window_check: BLOCKED -- 5h window at {used:.0f}% (>= {PARK_AT}%), "
            f"resets {resets}. Park now: commit the board, write the next step into "
            ".scrum/session.lock, and resume from it after the reset. Dispatching "
            "here risks the agent dying mid-task, which costs more than waiting.",
            file=sys.stderr,
        )
        return 2

    if used >= WARN_AT:
        print(
            f"yt_window_check: 5h window at {used:.0f}% (>= {WARN_AT}%), resets "
            f"{resets}. Finish work already in flight on the CURRENT story, but do "
            "not start a new story's implementer.",
            file=sys.stderr,
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
