"""Evidence-artifact check helper, at the SCRIPT rung (STORY-212).

Six retro amendments (`.scrum/checklists/implementer.md` "Evidence discipline")
collapsed into one idea: *an evidence artifact that cannot fail is not
evidence.* Each of those six landed as CHECKLIST prose, and each landed
*because the previous one had not held* -- the enforcement ladder failing in
the direction it exists to prevent. This module is the mechanical rung six
retros named and declined, for reasons now removed (see the story's History).

**What this does NOT do (scope guard, restated from the story):** it does not
judge whether a proof was *meaningful* -- "could this assertion have
diverged" is bespoke per story and stays a human judgment call. It mechanises
exactly the three checks that are not bespoke at all:

1. `falsify <artifact> --bad-input <spec>` -- run `<artifact>` (plus the
   `--bad-input` spec, appended to its argv) and assert it exits non-zero.
   Exit 0 on bad input means the artifact is reported NOT A GATE.
2. `two-sided --left <cmd> --right <cmd>` -- run both sides, record both
   outcomes (exit code + stdout), and FAIL (non-zero exit) when they are
   IDENTICAL, whatever the value. `--import-provenance-module <name>` wraps
   `tools/import_provenance.py::assert_import_root` (STORY-187, reused not
   reimplemented, AC6) instead of running a shell command per side: `--left`/
   `--right` are then read as ROOT paths, and the recorded "outcome" per side
   is the resolved file path (or the `WrongImportRootError` text).
3. `mutate <patch> --tests <selector>` -- apply `<patch>` with `git apply`,
   run the pytest selector(s), report which went RED, then ALWAYS attempt
   `git apply -R` and assert `git diff -- <the files the patch names>` is
   empty afterwards. Zero RED exits non-zero (UNPINNED); a failed or
   incomplete restore also exits non-zero, never a silent pass.

**The mutation format is a patch file** (resolved open question, sprint-70
refinement, 2026-08-13): `git apply`/`git apply -R` is the only one of the
three options considered that cannot half-apply silently (`git apply` is
atomic where a repeated `sed` is not), the patch itself becomes a committable,
reviewable artifact alongside the red/green tail, and it expresses the
MULTI-LINE mutations this project's proofs actually use (STORY-216's three
ZR-8 edits were all multi-line -- a `<target> <old> <new>` triple could not
express them).

**AC4's restore check is scoped to the files the patch itself names, never
the whole tree** (corrected 2026-08-13 at plan verification): a whole-tree
`git diff` emptiness check fails on any legitimately dirty sprint tree, and
the tool would then exit non-zero on every correct run. The target list is
derived from the patch's own `+++ b/<path>` headers -- never a second,
separately-typed target argument that could drift from what the patch
actually touches.

Placement: `tools/`, dev-only, never in the production image, same rule as
`tools/import_provenance.py` (STORY-187) and `tools/zr3_duplicate_sweep.py`
(STORY-196) -- free to import `src.*`; nothing under `backend/src/` may
import this module or anything else under `tools/`
(`backend/tests/test_tools_isolation.py`, STORY-212 AC1).

Command strings (`<artifact>`, `--left`, `--right`) are split with `shlex`
(POSIX mode) -- use forward-slash paths, matching every other usage example
in this repo's `tools/`; a literal Windows backslash path would be
misinterpreted as a `shlex` escape sequence.

Usage::

    python tools/evidence_check.py falsify "python tools/some_gate.py" --bad-input "--file missing.json"
    python tools/evidence_check.py two-sided --left "python left.py" --right "python right.py"
    python tools/evidence_check.py two-sided --import-provenance-module pkg.mod --left /root/a --right /root/b
    python tools/evidence_check.py mutate mutation.patch --tests "backend/tests/test_foo.py::test_bar"
"""

from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from import_provenance import WrongImportRootError, assert_import_root

_REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class CommandRun:
    """The recorded outcome of running one shelled-out command (checklist:
    "the board records the EXIT CODE", never stdout alone)."""

    command: list[str]
    exit_code: int
    stdout: str
    stderr: str


def run_command(command: Sequence[str], *, cwd: Path | None = None) -> CommandRun:
    """Run `command` and capture its full outcome. Never raises on a
    non-zero exit -- a non-zero exit is exactly the signal every subcommand
    below needs to observe, not an error in this helper."""
    result = subprocess.run(list(command), cwd=cwd, capture_output=True, text=True)
    return CommandRun(
        command=list(command),
        exit_code=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
    )


# --- Subcommand 1: falsify ---------------------------------------------------


def check_falsify(
    artifact: Sequence[str], bad_input: Sequence[str], *, cwd: Path | None = None
) -> tuple[bool, str]:
    """Run `artifact` with `bad_input` appended to its argv and assert it
    exits non-zero. Returns `(is_gate, message)`: `is_gate` is True when the
    artifact correctly failed (exit code != 0), False when it is NOT A GATE
    (exit 0 on deliberately bad input)."""
    run = run_command(list(artifact) + list(bad_input), cwd=cwd)
    rendered = " ".join(run.command)
    if run.exit_code != 0:
        return True, (
            f"OK -- IS a gate: `{rendered}` exited {run.exit_code} on bad "
            f"input {list(bad_input)!r}."
        )
    return False, (
        f"NOT A GATE: `{rendered}` exited 0 on deliberately bad input "
        f"{list(bad_input)!r} -- stdout: {run.stdout.strip()!r}"
    )


# --- Subcommand 2: two-sided --------------------------------------------------


def check_two_sided(
    left: Sequence[str], right: Sequence[str], *, cwd: Path | None = None
) -> tuple[bool, str]:
    """Run both sides, record `(exit_code, stdout)` per side, and FAIL
    (return `differ=False`) when the two outcomes are IDENTICAL -- whatever
    the value. Never compares exit code alone: two sides that both exit 0
    while printing different numbers must still be caught as DIFFERENT, and
    two sides that both exit 1 printing the identical message must still be
    caught as IDENTICAL."""
    left_run = run_command(left, cwd=cwd)
    right_run = run_command(right, cwd=cwd)
    left_outcome = (left_run.exit_code, left_run.stdout.strip())
    right_outcome = (right_run.exit_code, right_run.stdout.strip())

    if left_outcome == right_outcome:
        return False, (
            f"IDENTICAL outcomes -- FAILED proof (this argues AGAINST a "
            f"correct fix, not for one). left={left_outcome!r} "
            f"right={right_outcome!r}"
        )
    return (
        True,
        f"DIFFER -- valid two-sided proof. left={left_outcome!r} right={right_outcome!r}",
    )


def check_two_sided_import_provenance(
    module_name: str, left_root: Path | str, right_root: Path | str
) -> tuple[bool, str]:
    """`two-sided`'s import-provenance wrap (AC6, STORY-187 reused not
    reimplemented): the outcome per side is `assert_import_root`'s resolved
    file path on success, or the `WrongImportRootError` text on failure --
    never a shell command. Two sides that BOTH resolve `module_name` under
    the SAME root (the exact sprint-63 STORY-180 trap `import_provenance.py`
    itself documents) are IDENTICAL and this correctly fails."""

    def resolve(root: Path | str) -> str:
        try:
            provenance = assert_import_root(module_name, root)
            return str(provenance.file_path)
        except WrongImportRootError as exc:
            return f"ERROR: {exc}"

    left_outcome = resolve(left_root)
    right_outcome = resolve(right_root)

    if left_outcome == right_outcome:
        return False, (
            f"IDENTICAL provenance -- FAILED proof: {module_name!r} "
            f"resolved to the same place on both sides ({left_outcome!r}). "
            f"This is the exact wrong-tree trap import_provenance.py exists "
            f"to catch."
        )
    return True, (
        f"DIFFER -- valid two-sided provenance proof. "
        f"left={left_outcome!r} right={right_outcome!r}"
    )


# --- Subcommand 3: mutate -----------------------------------------------------


def parse_patch_targets(patch_path: Path) -> list[str]:
    """Return the repo-relative path(s) a unified-diff patch touches, read
    from its own `+++ b/<path>` headers -- never a second, separately-typed
    target argument (AC4's correction: the restore check must be scoped to
    what the patch ACTUALLY names, and the only source of truth for that is
    the patch itself). `/dev/null` (a pure deletion) is excluded -- there is
    no post-image file to scope a `git diff` at."""
    text = patch_path.read_text(encoding="utf-8")
    targets: list[str] = []
    for line in text.splitlines():
        if not line.startswith("+++ "):
            continue
        raw = line[len("+++ ") :].strip()
        # A real `git diff`/`git apply`-compatible patch always tabs or
        # spaces off any trailing timestamp; splitting on whitespace and
        # taking the first token is the same rule `git apply` itself uses.
        raw = raw.split("\t")[0].split(" ")[0]
        if raw == "/dev/null":
            continue
        if raw.startswith("b/"):
            raw = raw[2:]
        if raw not in targets:
            targets.append(raw)
    return targets


def apply_patch(
    patch_path: Path, *, cwd: Path, reverse: bool = False
) -> subprocess.CompletedProcess:
    args = ["git", "apply"] + (["-R"] if reverse else []) + [str(patch_path)]
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True)


_RESULT_RE_TOKENS = ("PASSED", "FAILED", "ERROR")


def run_pytest_selectors(
    selectors: Sequence[str], *, cwd: Path
) -> tuple[int, list[str], str]:
    """Run `python -m pytest -v <selectors>` under `cwd` and return
    `(exit_code, red_test_ids, stdout)`. `red_test_ids` is every test node id
    whose verbose-mode result line reads FAILED or ERROR -- module form,
    matching this repo's own blocked-shim convention
    (`python -m pytest`, never the `pytest` exe)."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", *selectors, "-v"],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    red: list[str] = []
    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[1] in _RESULT_RE_TOKENS:
            red.append(parts[0])
    return result.returncode, red, result.stdout


def check_mutate(
    patch_path: Path, selectors: Sequence[str], *, repo_root: Path
) -> tuple[bool, str]:
    """Apply `patch_path`, run `selectors`, ALWAYS attempt to restore, and
    return `(turned_red, message)`. `turned_red` is True only when: the patch
    applied, at least one selected test went RED, AND the restore (`git
    apply -R` + `git diff -- <patch's own targets>` empty) succeeded. A
    failure to restore is reported as a failure in its own right, never
    folded silently into a pass."""
    targets = parse_patch_targets(patch_path)
    if not targets:
        return False, (
            f"Patch {patch_path} names no target file (no '+++ b/<path>' "
            f"header found) -- cannot scope a restore check to it."
        )

    apply_result = apply_patch(patch_path, cwd=repo_root)
    if apply_result.returncode != 0:
        return False, (
            f"git apply {patch_path} failed (exit {apply_result.returncode}): "
            f"{apply_result.stderr.strip()}"
        )

    try:
        _exit_code, red, stdout = run_pytest_selectors(selectors, cwd=repo_root)
    except OSError as exc:
        revert_result = apply_patch(patch_path, cwd=repo_root, reverse=True)
        return False, (
            f"pytest run raised {exc!r} while the mutation was applied "
            f"(attempted revert, exit {revert_result.returncode}) -- verify "
            f"`git diff -- {' '.join(targets)}` by hand before trusting the "
            f"tree."
        )

    revert_result = apply_patch(patch_path, cwd=repo_root, reverse=True)
    if revert_result.returncode != 0:
        return False, (
            f"RESTORE FAILED: `git apply -R {patch_path}` exited "
            f"{revert_result.returncode}: {revert_result.stderr.strip()} -- "
            f"the tree may still carry the mutation; never a silent pass."
        )

    diff_result = subprocess.run(
        ["git", "diff", "--", *targets],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    if diff_result.stdout.strip():
        return False, (
            f"RESTORE INCOMPLETE: `git diff -- {' '.join(targets)}` is "
            f"non-empty after reverting {patch_path}:\n{diff_result.stdout}"
        )

    if not red:
        return False, (
            f"ZERO RED: mutation {patch_path} applied, {list(selectors)!r} "
            f"run, restored cleanly, but NOTHING went red -- UNPINNED.\n"
            f"stdout tail:\n{stdout[-2000:]}"
        )
    return True, f"OK: mutation turned RED: {red}"


# --- CLI -----------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="evidence_check.py",
        description="Mechanise the three non-bespoke evidence checks (STORY-212).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_falsify = sub.add_parser(
        "falsify", help="Assert an artifact exits non-zero on deliberately bad input."
    )
    p_falsify.add_argument(
        "artifact", help="The artifact command, e.g. 'python tools/foo.py'."
    )
    p_falsify.add_argument(
        "--bad-input",
        default="",
        help="Extra argv appended to the artifact invocation.",
    )
    p_falsify.add_argument("--cwd", default=None)

    p_two_sided = sub.add_parser(
        "two-sided", help="Assert two sides of a proof produce different outcomes."
    )
    p_two_sided.add_argument("--left", required=True)
    p_two_sided.add_argument("--right", required=True)
    p_two_sided.add_argument(
        "--import-provenance-module",
        default=None,
        help=(
            "If set, --left/--right are read as ROOT paths and both sides "
            "are resolved via assert_import_root for this module name, "
            "instead of running a shell command."
        ),
    )
    p_two_sided.add_argument("--cwd", default=None)

    p_mutate = sub.add_parser(
        "mutate",
        help="Apply a mutation patch, run tests, assert something went RED, restore.",
    )
    p_mutate.add_argument(
        "patch", help="Path to a unified-diff patch file (git apply-able)."
    )
    p_mutate.add_argument(
        "--tests", required=True, help="pytest selector(s), space-separated."
    )
    p_mutate.add_argument("--repo-root", default=None)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    if args.command == "falsify":
        cwd = Path(args.cwd).resolve() if args.cwd else None
        is_gate, message = check_falsify(
            shlex.split(args.artifact), shlex.split(args.bad_input), cwd=cwd
        )
        print(message)
        return 0 if is_gate else 1

    if args.command == "two-sided":
        cwd = Path(args.cwd).resolve() if args.cwd else None
        if args.import_provenance_module:
            differ, message = check_two_sided_import_provenance(
                args.import_provenance_module, args.left, args.right
            )
        else:
            differ, message = check_two_sided(
                shlex.split(args.left), shlex.split(args.right), cwd=cwd
            )
        print(message)
        return 0 if differ else 1

    if args.command == "mutate":
        repo_root = Path(args.repo_root).resolve() if args.repo_root else _REPO_ROOT
        turned_red, message = check_mutate(
            Path(args.patch), shlex.split(args.tests), repo_root=repo_root
        )
        print(message)
        return 0 if turned_red else 1

    raise AssertionError(
        f"unhandled command {args.command!r}"
    )  # argparse enforces choices


if __name__ == "__main__":
    sys.exit(main())
