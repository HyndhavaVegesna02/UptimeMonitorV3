#!/usr/bin/env python3
"""YourTeam v2 gate runner (yourteam_version: 2.1.0).

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
    EXCEPTION (A20, sprint-71 retro): modified ORCHESTRATOR-OWNED paths
    (`.scrum/`) are reported but never gate. They are read by no gate
    command, so they cannot change a result — while the orchestrator edits
    them continuously, including while an agent runs. Refusing on them
    bought nothing and left agents with no sanctioned move.
  * A contention false-red is proven, not assumed (working agreement
    2026-07-06): re-run the failing unit with --only in isolation; if it
    passes AND its diff since the sprint cut is empty, record the isolated
    re-run with a prominent note and file a determinism defect.
  * A command that looks environment-blocked (a Windows Device Guard /
    Application Control policy, not the code) is LABELLED as such —
    `is_policy_block()`, platform-level signatures only — but the label
    never downgrades a red: exit_code is recorded faithfully and still
    fails the gate (STORY-210, sprint-67).

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
# Optional per-command env-precondition annotation on a DoD line:
# `(requires-env: DATABASE_URL, DATABASE_URL_DIRECT)`. Project-supplied — the
# runner hardcodes no var names, staying generic (sprint-47 retro, 2026-07-15).
REQUIRES_ENV_RE = re.compile(r"\(requires-env:\s*([^)]*)\)", re.IGNORECASE)
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
            # Optional, project-supplied: `(requires-env: VAR1, VAR2)` anywhere on
            # the DoD line declares env preconditions the gate warns about up front
            # when unset. The project names its own vars, so the runner stays
            # generic (sprint-47 retro, 2026-07-15).
            rm = REQUIRES_ENV_RE.search(line)
            requires_env = (
                [v.strip() for v in rm.group(1).split(",") if v.strip()] if rm else []
            )
            commands.append(
                {
                    "label": m.group(1).strip(),
                    "command": m.group(2).strip(),
                    "cwd": section_cwd,
                    "requires_env": requires_env,
                }
            )
    return commands


def git(root: Path, *args: str) -> str:
    out = subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, timeout=30
    )
    return out.stdout.strip()


#: Paths owned by the orchestrator, not by any agent, and exempted from the
#: dirty-tree refusal below. A20 (sprint-71 retro): an orchestrator's edit to
#: these paths must not force an agent into a `git stash` corner, since the
#: orchestrator edits them CONTINUOUSLY, including while an agent runs. That
#: combination left an agent needing clean-tree evidence with no sanctioned
#: move, and TWO agents in one sprint independently reached for `git stash`
#: to escape it. One stashed the orchestrator's board file; the other popped
#: an unrelated 2026-07-14 stash and left merge-conflict markers across three
#: `backend/src/` files mid-sprint. Neither was careless — they were boxed in.
#: This removes the incentive; the "never write .scrum/" prohibition stays.
#:
#: CORRECTED (STORY-224 fix round, 2026-08-14): this comment used to claim
#: "`.scrum/` is read by NO gate command" — STORY-224 made that FALSE by
#: adding a 9th command (`yt_selftest.py`), two of whose suites
#: (`test_backlog_story_parity.py`, `test_scrum_encoding.py`) read `.scrum/`.
#: A20's SAFETY still holds, but no longer because nothing reads these paths
#: — it holds because those two suites read the COMMITTED tree at HEAD, not
#: the working tree (see `read_committed_scrum_file` /
#: `committed_or_working_scrum_files` in that pair of test modules), so an
#: uncommitted `.scrum/` edit — exempted here from the dirty check — cannot
#: change what a gate run stamped `commit: X` actually sees. Any FUTURE
#: `.scrum/`-reading check added without that same committed-HEAD discipline
#: reopens the hole this exemption depends on: a result stamped `commit: X`
#: could reflect a working-tree state `X` never contained ("dirty-tree-green"
#: evidence — demonstrated in the STORY-224 fix round before the read was
#: corrected).
_ORCHESTRATOR_OWNED_PREFIXES = (".scrum/",)


def _status_path(line: str) -> str:
    """The path from a `git status --porcelain` line, normalised to forward slashes.

    Porcelain v1 is `XY <path>`, with a rename as `XY <old> -> <new>`; the
    destination is what matters. Quoted paths (non-ASCII, spaces) keep their
    quotes — harmless here, since we only prefix-match a known ASCII directory.

    *** DO NOT slice at a fixed offset. *** `git()` calls `.strip()` on the whole
    output, so the FIRST line of a run loses its leading space: ` M .scrum/x`
    arrives as `M .scrum/x`. A `line[3:]` slice then eats the leading `.` and
    `.scrum/x` silently stops matching — which is precisely the bug this function
    shipped with, caught only by running the gate for real against a tree dirtied
    by exactly one `.scrum/` file. Split on whitespace instead; the status code is
    always a 1-2 char non-space token.
    """
    parts = line.strip().split(None, 1)
    path = parts[1] if len(parts) > 1 else ""
    if " -> " in path:
        path = path.split(" -> ", 1)[1]
    return path.strip().strip('"').replace("\\", "/")


def is_orchestrator_owned(line: str) -> bool:
    """True if this status line names a path the orchestrator owns (A20)."""
    return _status_path(line).startswith(_ORCHESTRATOR_OWNED_PREFIXES)


def tree_state(root: Path) -> tuple[list[str], list[str], list[str]]:
    """Return (dirty_lines, untracked_lines, orchestrator_owned_lines).

    A20: modified ORCHESTRATOR-OWNED paths are split out of `dirty` and reported
    separately rather than refused. They are read by no gate command, so they
    cannot change a result. Every other modified tracked file still refuses.
    """
    lines = [ln for ln in git(root, "status", "--porcelain").splitlines() if ln.strip()]
    untracked = [ln for ln in lines if ln.startswith("??")]
    tracked = [ln for ln in lines if not ln.startswith("??")]
    owned = [ln for ln in tracked if is_orchestrator_owned(ln)]
    dirty = [ln for ln in tracked if not is_orchestrator_owned(ln)]
    return dirty, untracked, owned


def _is_banner(line: str) -> bool:
    """Decorative ASCII-art line (e.g. import-linter's box-drawing logo)?

    Such lines carry zero evidence signal but cost bytes in sprint-current.yaml
    forever (retro sprint-45, 2026-07-14). A line is a banner when box-drawing/
    block/geometric glyphs (U+2500-U+25FF) dominate it; lines with a stray
    glyph (vite's `140 kB │ gzip: 76 kB`) are kept.
    """
    solid = [ch for ch in line if not ch.isspace()]
    if not solid:
        return False
    deco = sum(1 for ch in solid if "─" <= ch <= "◿")
    return deco / len(solid) > 0.5


#: ANSI/VT escape sequences (colour, cursor moves) emitted by tools that detect
#: — or merely assume — a terminal. `\x1b[32m`, `\x1b[0m`, and friends.
_ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]|\x1b[@-Z\\-_]")


def _strip_control_chars(text: str) -> str:
    """Remove ANSI escapes and C0 control characters from captured output.

    The emitted `dod_evidence` fragment is meant to be merged into the sprint
    board VERBATIM, and YAML **forbids** raw C0 control characters outright:
    a single stray `\\x1b` makes the whole board unparseable
    (`yaml.reader.ReaderError: special characters are not allowed`), which is a
    far worse failure than a slightly less pretty tail.

    Amendment A10 (retro sprint-65, PO-approved 2026-07-30). Motivating
    incident: a project's frontend build colourised its output, the tail was
    pasted verbatim exactly as instructed, and the sprint board became
    unreadable. Sanitising here fixes it for every project rather than warning
    each one — any build tool that colourises hits this.

    Tabs and newlines are preserved; `one_line_tail` collapses newlines itself.
    """
    return "".join(ch for ch in _ANSI_ESCAPE.sub("", text) if ch >= " " or ch in "\n\t")


def one_line_tail(text: str, limit: int = TAIL_CHARS) -> str:
    # Sanitise BEFORE slicing: escape sequences are multi-byte, so trimming
    # first can leave a half-sequence whose ESC survives the filter's intent.
    tail = _strip_control_chars(text).strip()[-limit:]
    tail = " | ".join(
        part.strip()
        for part in tail.splitlines()
        if part.strip() and not _is_banner(part)
    )
    return tail.replace("\\", "\\\\").replace('"', '\\"')


#: STORY-210 (AC3/AC5/AC6): observed signatures of a Windows Device Guard /
#: Application Control policy blocking a process, rather than the invoked
#: command genuinely failing. Platform-level, not project-level — no project
#: names, paths or command names belong here, which is why this lives in the
#: generic runner instead of a per-project DoD note.
POLICY_BLOCK_EXIT_CODE = 4551
_POLICY_BLOCK_MARKERS = (
    re.compile(r"blocked by your organization", re.IGNORECASE),
    re.compile(r"application control policy has blocked", re.IGNORECASE),
)

#: The 2026-07-06 working agreement's proof protocol, restated here so AC3's
#: label always ships with it: a policy-block classification is not license
#: to discount a red on sight.
POLICY_BLOCK_PROOF_NOTE = (
    "This is a LABEL, not an escape hatch (agreement 2026-07-06): a policy-blocked "
    "command still exits nonzero, still records its exit code faithfully, and still "
    "fails the gate. Before discounting it, prove BOTH: (1) an EMPTY diff on the "
    "affected command/file since the sprint cut, AND (2) the command passes when "
    "re-run in isolation with --only. A red without both proven stays a red."
)


def is_policy_block(exit_code: int, output: str) -> bool:
    """Classify a command result as an environment (policy) block, not a code failure.

    AC5 (two-sided): fires on the observed signatures — exit code 4551 and/or
    the marker text a Windows Application Control policy itself emits in its
    block message — and must NOT fire on a genuine failure's output (e.g. a
    pytest assertion failure). A zero exit is never a block: a command that
    merely prints marker-like text while succeeding is not blocked (AC4 —
    the label only ever attaches to something that is already a red).
    """
    if exit_code == 0:
        return False
    if exit_code == POLICY_BLOCK_EXIT_CODE:
        return True
    return any(pattern.search(output) for pattern in _POLICY_BLOCK_MARKERS)


_ENV_REF = re.compile(r"\$\{(\w+)\}|\$(\w+)|%(\w+)%")


def preflight_env(commands: list, env: dict) -> list:
    """Generic, project-agnostic precondition scan.

    A command whose env precondition is unset produces a false-red that looks
    nothing like the code failing — e.g. a DB-backed migration/consistency
    command left without its connection URL surfaces a raw KeyError, costing a
    diagnose-and-re-run cycle (sprint-47 retro, 2026-07-15). This warns UP FRONT
    and names the missing vars, without hardcoding any project's var names.

    Two signals, both project-supplied (the runner stays generic):
      - a `(requires-env: VAR, ...)` annotation on the DoD line — the reliable
        signal, since the dependency is usually INSIDE the invoked code
        (`os.environ[...]`), not literally in the command string; and
      - a literal `$VAR` / `${VAR}` / `%VAR%` reference in the command text
        (fallback, for shell-style commands).

    Returns the sorted list of required-but-unset var names (empty = clean).
    Advisory only: it never blocks — the command still runs and reds honestly
    if the missing var truly breaks it.
    """
    missing = set()
    for entry in commands:
        for name in entry.get("requires_env", []):
            if name not in env:
                missing.add(name)
        for m in _ENV_REF.finditer(entry["command"]):
            name = next(g for g in m.groups() if g)
            if name not in env:
                missing.add(name)
    return sorted(missing)


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
        # AC3/AC4: a LABEL only — exit_code above is recorded faithfully either
        # way and is the sole input to the gate's pass/fail decision.
        "policy_block": is_policy_block(exit_code, output),
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
    # Windows consoles default to cp1252; captured tails are UTF-8 (may carry
    # npm's ✓ etc.), so force UTF-8 on our own streams or the evidence print
    # crashes after a fully green run.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
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

    dirty, untracked, owned = tree_state(root)
    if untracked:
        print(
            f"yt_gate: WARNING {len(untracked)} untracked file(s) present (not gating)",
            file=sys.stderr,
        )
    if owned:
        # A20: informational, never gating. Named individually so the run's
        # evidence records exactly what was modified and by whom it is owned.
        print(
            f"yt_gate: {len(owned)} orchestrator-owned path(s) modified, NOT gating "
            "(read by no gate command — see A20):",
            file=sys.stderr,
        )
        for ln in owned:
            print(f"yt_gate:   orchestrator-owned: {ln}", file=sys.stderr)
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
    # Force UTF-8 in every gate subprocess (retro sprint-45, 2026-07-13): without it,
    # import-linter's rich banner crashes the Windows cp1252 pipe writer
    # (UnicodeEncodeError in rich/_win32_console.py) and reds an otherwise-green gate.
    # setdefault so a deliberately-exported PYTHONUTF8 still wins.
    env.setdefault("PYTHONUTF8", "1")

    # Precondition scan (sprint-47 retro, 2026-07-15): a command referencing an
    # unset env var reds in a way that looks nothing like the code failing (a raw
    # KeyError / connection error), costing a diagnose-and-re-run cycle. Warn up
    # front and name the missing vars — generically, no project var names hardcoded.
    unset = preflight_env(commands, env)
    if unset:
        print(
            "yt_gate: WARNING these commands reference unset env var(s): "
            + ", ".join(unset)
            + " — a missing precondition (e.g. an unprovisioned DB/service) reds as a "
            "false failure. Set them (or provision the backing resource) before trusting "
            "the result. Running anyway.",
            file=sys.stderr,
            flush=True,
        )

    commit = git(root, "rev-parse", "--short", "HEAD")
    results, all_green = [], True
    for i, entry in enumerate(commands, 1):
        print(
            f"yt_gate: [{i}/{len(commands)}] {entry['command']}",
            file=sys.stderr,
            flush=True,
        )
        r = run_command(entry, root, env, args.timeout)
        # AC3: a policy block is reported distinctly from a plain code failure,
        # but it is still a FAIL for the purpose of all_green below (AC4).
        if r["policy_block"]:
            status = f"POLICY BLOCK (environment, exit {r['exit_code']})"
        elif r["exit_code"] == 0:
            status = "PASS"
        else:
            status = f"FAIL ({r['exit_code']})"
        print(f"yt_gate:   -> {status}", file=sys.stderr, flush=True)
        all_green = all_green and r["exit_code"] == 0
        results.append(r)

    fragment = emit_yaml(results, commit)
    print(fragment)
    if args.out:
        Path(args.out).write_text(fragment, encoding="utf-8")

    policy_blocked = [r for r in results if r["policy_block"]]
    if policy_blocked:
        print(
            f"yt_gate: POLICY BLOCK — {len(policy_blocked)} command(s) look like an "
            "environment block (a Windows Device Guard / Application Control policy), "
            "not a code failure:",
            file=sys.stderr,
        )
        for r in policy_blocked:
            print(
                f"yt_gate:   POLICY BLOCK: {r['command']} (exit {r['exit_code']})",
                file=sys.stderr,
            )
        print(f"yt_gate: {POLICY_BLOCK_PROOF_NOTE}", file=sys.stderr)

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
