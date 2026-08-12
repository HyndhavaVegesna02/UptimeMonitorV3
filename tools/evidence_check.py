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
   Exit 0 on bad input means the artifact is reported NOT A GATE. `--bad-
   input` is REQUIRED to be non-empty (MAJOR 4, sprint-70 fix round): an
   artifact run with no bad input at all is reported NO BAD INPUT SUPPLIED,
   never a vacuous "OK -- IS a gate".
2. `two-sided --left <cmd> --right <cmd>` -- run both sides, record both
   outcomes (exit code + stdout), and FAIL (non-zero exit) when they are
   IDENTICAL, whatever the value. `--import-provenance-module <name>` wraps
   `tools/import_provenance.py::assert_import_root` (STORY-187, reused not
   reimplemented, AC6) instead of running a shell command per side: `--left`/
   `--right` are then read as ROOT paths, and the recorded "outcome" per side
   is the resolved file path (or the `WrongImportRootError` text).
3. `mutate <patch> --tests <selector>` -- first run the pytest selector(s) on
   the UNMUTATED pre-image and require them GREEN (sprint-70 fix round: an
   already-red selector cannot be distinguished from "the mutation turned it
   red", and would otherwise pass ANY mutation, comment-only ones included);
   then apply `<patch>` with `git apply`, run the selector(s) again, report
   which went RED, then ALWAYS attempt `git apply -R` and assert `git status
   --porcelain -- <the files the patch names>` is empty afterwards (`git
   status`, not `git diff` -- a CREATION patch's target is UNTRACKED by
   construction and invisible to `git diff`). Zero RED exits non-zero
   (UNPINNED); a selector run that never produced a real pass/fail verdict at
   all (pytest exit 2/3/4/5 -- a collection error, an unknown selector path)
   is its OWN distinct non-zero outcome, never folded into "zero RED"; a
   failed or incomplete restore also exits non-zero, never a silent pass.

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

Command strings (`<artifact>`, `--left`, `--right`) are split with
`shlex.split(..., posix=False)` -- chosen over the POSIX default specifically
because this project's own interpreter path (`sys.executable`) is a Windows
backslash path, and POSIX-mode `shlex` treats a bare backslash as an escape
character and silently eats it. Non-POSIX mode does not strip surrounding
quotes from a token, so a spec containing an embedded space still needs to
be a single argv element some other way (e.g. avoid the space, or invoke the
underlying `check_*` function directly instead of the CLI) -- not supported
by this CLI layer today.

Usage::

    python tools/evidence_check.py falsify "python tools/some_gate.py" --bad-input "--file missing.json"
    python tools/evidence_check.py two-sided --left "python left.py" --right "python right.py"
    python tools/evidence_check.py two-sided --import-provenance-module pkg.mod --left /root/a --right /root/b
    python tools/evidence_check.py mutate mutation.patch --tests "backend/tests/test_foo.py::test_bar"
"""

from __future__ import annotations

import argparse
import os
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
    below needs to observe, not an error in this helper. Also never raises
    on a command that cannot even be LAUNCHED (ALSO FIX, sprint-70 fix
    round): a missing/unlaunchable binary previously raised
    `FileNotFoundError` straight through every caller, a traceback instead
    of a diagnosis, and inconsistent with `check_mutate`'s own OSError
    handling around its pytest call -- folded into the same `CommandRun`
    shape instead, exit code -1, the exception text in stderr."""
    try:
        result = subprocess.run(list(command), cwd=cwd, capture_output=True, text=True)
    except OSError as exc:
        return CommandRun(
            command=list(command),
            exit_code=-1,
            stdout="",
            stderr=f"{type(exc).__name__}: could not launch {list(command)!r}: {exc}",
        )
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
    (exit 0 on deliberately bad input).

    An empty `bad_input` is itself reported as NOT a demonstrated gate
    (MAJOR 4, sprint-70 fix round): nothing bad was actually fed to the
    artifact, so an artifact that exits non-zero for some OTHER reason (a
    missing required argument, a crash on a bare invocation) would
    otherwise be reported "OK -- IS a gate" having never been shown to
    reject BAD input specifically -- a vacuous pass in the one tool whose
    entire job is rejecting vacuous evidence. `bad_input=[]` is still a
    valid, non-crashing CALL (the checklist's explicit empty-input
    requirement); it just does not run the artifact at all, since there is
    nothing to falsify with."""
    if not list(bad_input):
        rendered = " ".join(artifact)
        return False, (
            f"NO BAD INPUT SUPPLIED: `{rendered}` was never given a "
            f"deliberately bad input to reject -- an artifact that exits "
            f"non-zero for some OTHER reason (a missing required argument, "
            f"a crash) proves nothing about whether it rejects BAD input "
            f"specifically. Nothing was falsified; pass --bad-input (or a "
            f"non-empty bad_input list)."
        )
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
    caught as IDENTICAL.

    Raw-stdout comparison is UNSAFE on nondeterministic output (ALSO FIX,
    sprint-70 fix round): a difference caused by a duration, a timestamp, or
    an absolute path that varies run-to-run is reported DIFFER exactly the
    same as a difference caused by the behaviour actually under test -- this
    function cannot tell the two apart. Confirm by reading the two stdouts
    that the difference is the ONE YOU INTENDED, not noise, before trusting
    a DIFFER result as evidence."""
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
        f"DIFFER -- valid two-sided proof IF this difference is the one you "
        f"intended, not noise from nondeterministic output (a duration, a "
        f"path, a timestamp) -- confirm by reading both stdouts. "
        f"left={left_outcome!r} right={right_outcome!r}",
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
        # A real `git diff`/`git apply`-compatible patch TAB-delimits any
        # trailing timestamp -- never a space, which is a legal character
        # inside the path itself. An additional `.split(" ")[0]` here (ALSO
        # FIX, sprint-70 fix round) truncated any path with an embedded
        # space at the first space, with no upside: the restore check then
        # scopes `git diff`/`git status` at the wrong, truncated target,
        # which reports empty regardless of the real file's state.
        raw = raw.split("\t")[0]
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


#: The verbose-mode result words that mean RED. Deliberately excludes
#: "PASSED" -- an earlier draft of this function used one combined tuple for
#: "is this even a result line" and then, by the same membership check,
#: accidentally counted every PASSED line as red too (caught by
#: `test_check_mutate_zero_red_is_a_failure`: a comment-only, behaviour
#: -preserving mutation reported RED regardless, which is exactly the wrong-
#: -reason-red defect this story's own brief warns about).
_RED_TOKENS = ("FAILED", "ERROR")

#: pytest exit codes documented by pytest itself that mean the selector run
#: never produced a real pass/fail verdict at all: 2 = execution interrupted
#: (a collection error is reported this way), 3 = internal error, 4 = usage
#: error (e.g. a `--tests` selector naming a file that does not exist), 5 =
#: no tests collected. Deliberately excludes 0 (all green) and 1 (something
#: genuinely failed) -- those two are exactly what `red` above already
#: distinguishes correctly (CRITICAL fix, sprint-70 fix round: a collection
#: ERROR was previously indistinguishable from a real RED result, and the
#: exit code that would have caught it was discarded entirely).
_SELECTOR_DID_NOT_RUN_EXIT_CODES = (2, 3, 4, 5)


def run_pytest_selectors(
    selectors: Sequence[str], *, cwd: Path
) -> tuple[int, list[str], str]:
    """Run `python -m pytest -v <selectors>` under `cwd` and return
    `(exit_code, red_test_ids, stdout)`. `red_test_ids` is every test node id
    whose verbose-mode result line reads FAILED or ERROR -- module form,
    matching this repo's own blocked-shim convention
    (`python -m pytest`, never the `pytest` exe).

    A result word alone is not enough: pytest's collection-error banner
    (`____________ ERROR collecting test_x.py ____________`) also has
    "ERROR" as its SECOND whitespace token, so `parts[0]` must additionally
    look like a real node id (`path/to/test.py` or containing `::`) before
    the line counts as red -- otherwise the banner's own dashes get
    reported as a "red test id" (CRITICAL fix, sprint-70 fix round; probed
    by renaming the symbol a test imports, producing an ImportError while
    collecting).

    Runs with `PYTHONDONTWRITEBYTECODE=1` (discovered via `check_mutate`'s
    own MAJOR 2 baseline fix, sprint-70 fix round): `check_mutate` now calls
    this twice against the SAME files -- once pre-mutation, once post -- and
    CPython's default timestamp-based `.pyc` cache stores the source mtime
    at SECOND resolution. A baseline compile followed by a same-second
    mutation left the post-mutation run silently importing the STALE
    pre-mutation bytecode (probed directly: a real `VALUE=1`->`VALUE=2`
    mutation reported "1 passed", not "1 failed" -- the mutation never took
    effect from the interpreter's point of view). Disabling bytecode writing
    forces a fresh compile from source on every call, closing that window."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", *selectors, "-v"],
        cwd=cwd,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    red: list[str] = []
    for line in result.stdout.splitlines():
        parts = line.split()
        if (
            len(parts) >= 2
            and parts[1] in _RED_TOKENS
            and ("::" in parts[0] or parts[0].endswith(".py"))
        ):
            red.append(parts[0])
    return result.returncode, red, result.stdout


def check_mutate(
    patch_path: Path, selectors: Sequence[str], *, repo_root: Path
) -> tuple[bool, str]:
    """Apply `patch_path`, run `selectors`, ALWAYS attempt to restore, and
    return `(turned_red, message)`. `turned_red` is True only when: the
    selector(s) were GREEN on the pre-image (the baseline check below), the
    patch applied, at least one selected test went RED, the post-mutation
    pytest run actually produced a verdict (never one of
    `_SELECTOR_DID_NOT_RUN_EXIT_CODES`), AND the restore (`git apply -R` +
    `git status --porcelain -- <patch's own targets>` empty) succeeded. A
    failure to restore is reported as a failure in its own right, never
    folded silently into a pass."""
    targets = parse_patch_targets(patch_path)
    if not targets:
        return False, (
            f"Patch {patch_path} names no target file (no '+++ b/<path>' "
            f"header found) -- cannot scope a restore check to it."
        )

    # Baseline (MAJOR 2 fix, sprint-70 fix round): "turned RED" cannot be
    # distinguished from "was already red" unless the selector(s) are known
    # to be GREEN on the pre-image, before the mutation is applied at all. An
    # already-failing selector would otherwise pass ANY mutation, including
    # a purely comment-only, behaviour-preserving one.
    baseline_exit, baseline_red, baseline_stdout = run_pytest_selectors(
        selectors, cwd=repo_root
    )
    if baseline_exit != 0 or baseline_red:
        return False, (
            f"BASELINE NOT GREEN (pytest exit {baseline_exit}, red="
            f"{baseline_red}) BEFORE {patch_path} was ever applied -- "
            f"{list(selectors)!r} must pass on the pre-image, or a "
            f"subsequent RED result cannot be attributed to this mutation.\n"
            f"baseline stdout tail:\n{baseline_stdout[-2000:]}"
        )

    apply_result = apply_patch(patch_path, cwd=repo_root)
    if apply_result.returncode != 0:
        return False, (
            f"git apply {patch_path} failed (exit {apply_result.returncode}): "
            f"{apply_result.stderr.strip()}"
        )

    try:
        exit_code, red, stdout = run_pytest_selectors(selectors, cwd=repo_root)
    except OSError as exc:
        revert_result = apply_patch(patch_path, cwd=repo_root, reverse=True)
        return False, (
            f"pytest run raised {exc!r} while the mutation was applied "
            f"(attempted revert, exit {revert_result.returncode}) -- verify "
            f"`git status --porcelain -- {' '.join(targets)}` by hand before "
            f"trusting the tree."
        )

    revert_result = apply_patch(patch_path, cwd=repo_root, reverse=True)
    if revert_result.returncode != 0:
        return False, (
            f"RESTORE FAILED: `git apply -R {patch_path}` exited "
            f"{revert_result.returncode}: {revert_result.stderr.strip()} -- "
            f"the tree may still carry the mutation; never a silent pass."
        )

    # MAJOR 3 fix (sprint-70 fix round): `git diff` cannot see UNTRACKED
    # files, and a CREATION patch's target is untracked by construction --
    # `git status --porcelain` sees untracked, staged AND unstaged changes,
    # so it also catches a reverse-apply that REPORTS success (exit 0) while
    # leaving a newly-created file on disk. Its own exit code is checked too
    # (a fatal invocation, e.g. exit 128 outside a git repo, must not read as
    # a clean restore either).
    status_result = subprocess.run(
        ["git", "status", "--porcelain", "--", *targets],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    if status_result.returncode != 0:
        return False, (
            f"RESTORE CHECK FAILED: `git status --porcelain -- "
            f"{' '.join(targets)}` exited {status_result.returncode}: "
            f"{status_result.stderr.strip()} -- cannot confirm a clean "
            f"restore; never a silent pass."
        )
    if status_result.stdout.strip():
        return False, (
            f"RESTORE INCOMPLETE: `git status --porcelain -- "
            f"{' '.join(targets)}` is non-empty after reverting "
            f"{patch_path}:\n{status_result.stdout}"
        )

    # CRITICAL fix, second half (sprint-70 fix round): the post-mutation
    # pytest run may never have produced a real pass/fail verdict at all --
    # a collection error, an internal error, a usage error, or "no tests
    # collected" -- which is NOT a RED proof and must not be folded into
    # "ZERO RED" (that diagnosis means "ran clean, nothing was pinned";
    # this one means "never ran to a verdict in the first place").
    if exit_code in _SELECTOR_DID_NOT_RUN_EXIT_CODES:
        return False, (
            f"SELECTOR DID NOT RUN (pytest exit {exit_code}): "
            f"{list(selectors)!r} never produced a pass/fail verdict under "
            f"the mutation {patch_path} -- a collection error or an unknown "
            f"selector path reads this way. NOT a RED proof, and distinct "
            f"from ZERO RED.\nstdout tail:\n{stdout[-2000:]}"
        )

    if not red:
        return False, (
            f"ZERO RED: mutation {patch_path} applied, {list(selectors)!r} "
            f"run (pytest exit {exit_code}), restored cleanly, but NOTHING "
            f"went red -- UNPINNED.\nstdout tail:\n{stdout[-2000:]}"
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
        "artifact",
        help=(
            "The artifact command, e.g. 'python tools/foo.py'. Split with "
            "shlex (non-POSIX mode) -- a path/argument containing an "
            "embedded SPACE is silently split into two argv tokens, no "
            "error raised; avoid the space or call check_falsify directly."
        ),
    )
    p_falsify.add_argument(
        "--bad-input",
        default="",
        help=(
            "Extra argv appended to the artifact invocation -- REQUIRED to "
            "be non-empty (MAJOR 4, sprint-70 fix round): an empty spec "
            "falsifies nothing and is reported NO BAD INPUT SUPPLIED, never "
            "a vacuous 'OK -- IS a gate'. Same shlex embedded-space caveat "
            "as `artifact` above."
        ),
    )
    p_falsify.add_argument("--cwd", default=None)

    p_two_sided = sub.add_parser(
        "two-sided", help="Assert two sides of a proof produce different outcomes."
    )
    p_two_sided.add_argument(
        "--left",
        required=True,
        help=(
            "The left-side command (or, with --import-provenance-module, a "
            "root path). Same shlex embedded-space caveat as `falsify`'s "
            "`artifact` -- a space inside the command silently splits into "
            "two argv tokens."
        ),
    )
    p_two_sided.add_argument(
        "--right", required=True, help="The right-side command/root path -- see --left."
    )
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
            shlex.split(args.artifact, posix=False),
            shlex.split(args.bad_input, posix=False),
            cwd=cwd,
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
                shlex.split(args.left, posix=False),
                shlex.split(args.right, posix=False),
                cwd=cwd,
            )
        print(message)
        return 0 if differ else 1

    if args.command == "mutate":
        repo_root = Path(args.repo_root).resolve() if args.repo_root else _REPO_ROOT
        turned_red, message = check_mutate(
            Path(args.patch), shlex.split(args.tests, posix=False), repo_root=repo_root
        )
        print(message)
        return 0 if turned_red else 1

    raise AssertionError(
        f"unhandled command {args.command!r}"
    )  # argparse enforces choices


if __name__ == "__main__":
    sys.exit(main())
