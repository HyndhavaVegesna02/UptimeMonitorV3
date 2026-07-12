#!/usr/bin/env python3
"""YourTeam v2 gate runner (yourteam_version: 2.0.0).

Runs every command in the project's Definition of Done and emits the
`dod_evidence` YAML fragment for sprint-current.yaml — command, exit code,
output tail, commit SHA, timestamp — so evidence is captured mechanically
instead of transcribed by hand.

Rules this script enforces by construction:
  * Commands run SEQUENTIALLY, never concurrently (working agreement
    2026-07-02: two runners sharing one throwaway DB corrupt each other).
  * The gate refuses a dirty tree (working agreement 2026-06-29: a gate
    result only counts at a clean, committed HEAD). --allow-dirty overrides
    for diagnostic runs; such runs are NOT valid DoD evidence.
  * A contention false-red is proven, not assumed (working agreement
    2026-07-06): re-run the failing unit with --only in isolation; if it
    passes AND its diff since the sprint cut is empty, record the isolated
    re-run with a prominent note and file a determinism defect.

DoD file format (parsed from .scrum/definition-of-done.md):
  * Sections whose heading starts with `## Commands` hold gate commands.
  * A heading may set the working directory for its section with the
    phrase "run from <dir>/" (e.g. "## Commands (frontend — ..., run
    from `frontend/`)").
  * Command lines look like:  - [ ] <label>: `<command>` -> exit 0

Usage:
  python yt_gate.py                 # run the full gate, print YAML evidence
  python yt_gate.py --list          # parse and show what would run
  python yt_gate.py --only pytest   # run only commands containing "pytest"
  python yt_gate.py --out ev.yaml   # also write the fragment to a file

Exit codes: 0 all commands passed; 1 at least one failed; 3 dirty tree
(without --allow-dirty); 4 could not parse any commands.
"""

from __future__ import annotations

import argparse
import datetime
import os
import re
import subprocess
import sys
from pathlib import Path

CMD_RE = re.compile(r"^\s*-\s*\[[ xX]\]\s*(.+?):\s*`([^`]+)`")
HEADING_RE = re.compile(r"^##\s+(.*)$")
CWD_RE = re.compile(r"run from\s+`?([\w./\\-]+?)/?`?[\s),]", re.IGNORECASE)
TAIL_CHARS = 600


def find_root(start: Path) -> Path | None:
    for p in [start, *start.parents]:
        if (p / ".scrum").is_dir():
            return p
    return None


def parse_dod(dod_path: Path) -> list[dict]:
    """Return [{label, command, cwd}] from the DoD file's Commands sections."""
    commands: list[dict] = []
    in_commands, section_cwd = False, ""
    for line in dod_path.read_text(encoding="utf-8", errors="replace").splitlines():
        h = HEADING_RE.match(line)
        if h:
            heading = h.group(1)
            in_commands = heading.strip().lower().startswith("commands")
            m = CWD_RE.search(heading)
            section_cwd = m.group(1) if (in_commands and m) else ""
            continue
        if not in_commands:
            continue
        m = CMD_RE.match(line)
        if m:
            commands.append(
                {
                    "label": m.group(1).strip(),
                    "command": m.group(2).strip(),
                    "cwd": section_cwd,
                }
            )
    return commands


def git(root: Path, *args: str) -> str:
    out = subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, timeout=30
    )
    return out.stdout.strip()


def tree_state(root: Path) -> tuple[list[str], list[str]]:
    """Return (dirty_lines, untracked_lines) from git status --porcelain."""
    lines = [ln for ln in git(root, "status", "--porcelain").splitlines() if ln.strip()]
    untracked = [ln for ln in lines if ln.startswith("??")]
    dirty = [ln for ln in lines if not ln.startswith("??")]
    return dirty, untracked


def one_line_tail(text: str, limit: int = TAIL_CHARS) -> str:
    tail = text.strip()[-limit:]
    tail = " | ".join(part.strip() for part in tail.splitlines() if part.strip())
    return tail.replace("\\", "\\\\").replace('"', '\\"')


def run_command(entry: dict, root: Path, env: dict, timeout: int) -> dict:
    cwd = root / entry["cwd"] if entry["cwd"] else root
    started = datetime.datetime.now(datetime.timezone.utc)
    try:
        proc = subprocess.run(
            entry["command"],
            shell=True,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        exit_code, output = proc.returncode, (proc.stdout or "") + (proc.stderr or "")
    except subprocess.TimeoutExpired as exc:
        exit_code = -1
        output = f"TIMEOUT after {timeout}s: {exc}"
    return {
        "label": entry["label"],
        "command": entry["command"],
        "cwd": entry["cwd"],
        "exit_code": exit_code,
        "output_tail": one_line_tail(output),
        "at": started.isoformat(timespec="seconds"),
    }


def emit_yaml(results: list[dict], commit: str) -> str:
    lines = ["dod_evidence:"]
    for r in results:
        cmd = r["command"].replace("\\", "\\\\").replace('"', '\\"')
        lines.append(f'  - command: "{cmd}"')
        lines.append(f"    exit_code: {r['exit_code']}")
        lines.append(f'    output_tail: "{r["output_tail"]}"')
        lines.append(f"    commit: {commit}")
        lines.append(f'    at: "{r["at"]}"')
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--dod",
        default=None,
        help="path to the DoD file (default .scrum/definition-of-done.md)",
    )
    ap.add_argument(
        "--list", action="store_true", help="parse and list commands without running"
    )
    ap.add_argument(
        "--only",
        action="append",
        default=[],
        help="run only commands containing this substring (repeatable)",
    )
    ap.add_argument(
        "--allow-dirty",
        action="store_true",
        help="run despite a dirty tree (NOT valid DoD evidence)",
    )
    ap.add_argument(
        "--timeout",
        type=int,
        default=1800,
        help="per-command timeout in seconds (default 1800)",
    )
    ap.add_argument(
        "--out", default=None, help="also write the YAML fragment to this file"
    )
    args = ap.parse_args()

    root = find_root(Path.cwd().resolve())
    if root is None:
        print(
            "yt_gate: no .scrum/ directory found walking up from cwd", file=sys.stderr
        )
        return 4

    dod_path = Path(args.dod) if args.dod else root / ".scrum" / "definition-of-done.md"
    if not dod_path.exists():
        print(f"yt_gate: DoD file not found: {dod_path}", file=sys.stderr)
        return 4

    commands = parse_dod(dod_path)
    if args.only:
        commands = [
            c
            for c in commands
            if any(s.lower() in c["command"].lower() for s in args.only)
        ]
    if not commands:
        print(
            "yt_gate: no gate commands parsed (check the DoD file format)",
            file=sys.stderr,
        )
        return 4

    if args.list:
        for c in commands:
            loc = f" [cwd: {c['cwd']}]" if c["cwd"] else ""
            print(f"{c['label']}: {c['command']}{loc}")
        return 0

    dirty, untracked = tree_state(root)
    if untracked:
        print(
            f"yt_gate: WARNING {len(untracked)} untracked file(s) present (not gating)",
            file=sys.stderr,
        )
    if dirty:
        for ln in dirty:
            print(f"yt_gate: dirty: {ln}", file=sys.stderr)
        if not args.allow_dirty:
            print(
                "yt_gate: REFUSING dirty tree — the gate counts only at a clean committed HEAD "
                "(agreement 2026-06-29). Commit or discard, then re-run. --allow-dirty for "
                "diagnostics only.",
                file=sys.stderr,
            )
            return 3
        print(
            "yt_gate: --allow-dirty set — this run is NOT valid DoD evidence",
            file=sys.stderr,
        )

    # Make venv-sibling binaries (pytest, ruff, alembic, lint-imports) resolvable.
    env = dict(os.environ)
    env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")

    commit = git(root, "rev-parse", "--short", "HEAD")
    results, all_green = [], True
    for i, entry in enumerate(commands, 1):
        print(
            f"yt_gate: [{i}/{len(commands)}] {entry['command']}",
            file=sys.stderr,
            flush=True,
        )
        r = run_command(entry, root, env, args.timeout)
        status = "PASS" if r["exit_code"] == 0 else f"FAIL ({r['exit_code']})"
        print(f"yt_gate:   -> {status}", file=sys.stderr, flush=True)
        all_green = all_green and r["exit_code"] == 0
        results.append(r)

    fragment = emit_yaml(results, commit)
    print(fragment)
    if args.out:
        Path(args.out).write_text(fragment, encoding="utf-8")

    if not all_green:
        print(
            "yt_gate: RED. If you suspect resource contention: prove it (empty diff since the "
            "sprint cut AND passes with --only in isolation) before discounting — agreement "
            "2026-07-06.",
            file=sys.stderr,
        )
    return 0 if all_green else 1


if __name__ == "__main__":
    sys.exit(main())
