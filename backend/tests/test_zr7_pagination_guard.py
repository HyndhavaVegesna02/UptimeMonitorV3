"""ZR-7 standing guard (STORY-197): every DynamoDB `.query(`/`.scan(` call site under
`adapters/persistence/` either loops on `LastEvaluatedKey` or is named, with a reason,
in `_EXEMPTIONS` below.

Cites: `docs/scrum/wiki/zone-rules.md` ZR-7 (an adapter must satisfy the port contract
it implements -- silently truncating a result set the port promises in full is a
boundary violation) and its Coverage verdict, which decides the implementable form this
test mechanises verbatim: assert the HARD, DECIDABLE half (does THIS call site sit
inside a `LastEvaluatedKey`-bearing loop) rather than the undecidable half
("provably bounded" against an English port docstring), and carry a named exemption
list with a reason per entry -- the same shape ZR-1's own contract sketch uses.

WHAT THIS GUARD CANNOT SEE -- stated plainly, because a guard whose limits are unstated
gets trusted past them (STORY-197 quality review, 2026-07-31, which demonstrated each of
the first three as a silent green before they were closed):
  - CLOSED: a repository under `adapters/persistence/<subdir>/` (now `rglob`, not `glob`).
  - CLOSED: a module-level function calling `.query(`/`.scan(` (now every `FunctionDef`
    is walked, not only direct class-body members).
  - CLOSED: a SECOND unpaginated call site inside an otherwise-paginating method (the
    loop check is now per CALL SITE, not per method).
  - STILL OPEN: the loop test remains a PROXY. A `while`/`for` that references
    `LastEvaluatedKey` counts as paging even if it never re-assigns
    `ExclusiveStartKey`, and pagination delegated to a helper one frame up is invisible.
    So this guard proves a call site is NOT OBVIOUSLY unpaginated; it cannot prove the
    paging is correct. Never read a green here as "pagination verified".
`docs/scrum/sprints/2026-07-31-sprint-66/audit-core-adapters.md` §2c has the full
finding detail this test's exemptions cite.

Why an exemption list, not a hard zero-tolerance assertion (the live-violation problem,
STORY-197 AC5/C3): five of the seven call sites this file finds are REAL, unfixed ZR-7
violations today (STORY-199, filed, not fixed here per C1 -- this story guards, it does
not fix). Landing this guard with zero exemptions would fail the DoD gate on every
future story until STORY-199 lands, which C4 forbids as a side effect of a guard. So
this guard is green today only because of a named, reasoned exemption per known
violation, each citing STORY-199 -- and it fails loudly the moment a NEW, unlisted
unpaginated `.query(`/`.scan(` call site appears anywhere under `adapters/persistence/`,
including a REGRESSION of the one call site that is compliant today (verified by
mutation, see the story's report).

Maintenance note for a future author (AC3): any new `.py` file ANYWHERE under
`adapters/persistence/`, and any function in it, is scanned automatically -- nothing to
update for the common case (a call site inside a real pagination loop needs no exemption
at all). The ONLY manual step is `_EXEMPTIONS` below: a call site that does not page must
be added here BY COORDINATE, with a reason in one of exactly two forms --
  - starting with `PERMANENT` for a query genuinely bounded by its own port's contract
    (like `list_recent`'s `Limit=limit`); such entries are never staleness-checked; or
  - any other text, for a real, accepted-but-not-yet-fixed violation, which MUST name the
    fix story that will delete the entry.
An unrecognised, unpaginated call site is always a guard FAILURE, never silently accepted.

The exemption reason is prose, but the PERMANENT marker is structural: staleness keys on
that prefix, not on a story id embedded in free text, so rewording a reason cannot
silently switch staleness checking off (STORY-197 review finding).
"""

from __future__ import annotations

import ast
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_PERSISTENCE_DIR = _REPO_ROOT / "backend" / "src" / "adapters" / "persistence"

_QUERY_METHODS = {"query", "scan"}

# (relative file path, call site line number) -> reason. Every entry is either a
# genuinely bounded query (permanent -- the port's own contract never promises "all")
# or a real ZR-7 finding awaiting its fix story (STORY-199) -- REMOVE the entry the
# moment that story lands and this file starts looping on `LastEvaluatedKey`
# (test_zr7_exemptions_are_still_needed below fails loudly if you forget).
_EXEMPTIONS: dict[tuple[str, int], str] = {
    (
        "backend/src/adapters/persistence/dynamo_component_repository.py",
        29,
    ): "ZR-7 finding: list_components silently truncates past a 1MB page against "
    "component_repository.py's 'retrieve all' contract. Fix: STORY-199.",
    (
        "backend/src/adapters/persistence/dynamo_maintenance_repository.py",
        68,
    ): "ZR-7 finding: list_windows silently truncates past a 1MB page against "
    "maintenance_repository.py's 'retrieve all' contract. Fix: STORY-199.",
    (
        "backend/src/adapters/persistence/dynamo_maintenance_repository.py",
        90,
    ): "ZR-7 finding, THE live defect: is_under_maintenance can silently return "
    "False for a component genuinely under maintenance once maintenance-window "
    "volume exceeds one DynamoDB page. Fix: STORY-199.",
    (
        "backend/src/adapters/persistence/dynamo_proposal_repository.py",
        174,
    ): "ZR-7 finding: list_open silently truncates past a 1MB page against "
    "proposal_repository.py's 'retrieve all' contract. Fix: STORY-199.",
    (
        "backend/src/adapters/persistence/dynamo_signal_repository.py",
        30,
    ): "ZR-7 finding: list_signals silently truncates past a 1MB page against "
    "signal_repository.py's 'retrieve all' contract. Fix: STORY-199.",
    (
        "backend/src/adapters/persistence/dynamo_publication_repository.py",
        53,
    ): "PERMANENT -- NOT a ZR-7 violation: list_recent's own port contract "
    "(publication_repository.py) promises only 'up to `limit` most-recent', a "
    "stated bound, not 'all' -- Limit=limit correctly honors it.",
}


def _enclosing_class_name(tree: ast.AST, target: ast.AST) -> str | None:
    """The name of the ClassDef whose body contains `target`, if any."""
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and any(
            child is target for child in node.body
        ):
            return node.name
    return None


def _mentions_last_evaluated_key(node: ast.AST) -> bool:
    """True if `node`'s subtree references the string "LastEvaluatedKey" anywhere."""
    return any(
        isinstance(n, ast.Constant) and n.value == "LastEvaluatedKey"
        for n in ast.walk(node)
    )


def _paginating_loop_bodies(func: ast.AST) -> list[ast.AST]:
    """Every `while`/`for` loop inside `func` whose own subtree references
    "LastEvaluatedKey" -- i.e. the loops that plausibly page.

    Tightened at STORY-197 review (2026-07-31). The first version asked only
    "does this METHOD mention LastEvaluatedKey anywhere", which admitted two
    demonstrated false passes: a mention in a comment or a dead branch counted
    as pagination, and a SECOND unpaginated call site inside an otherwise-
    paginating method inherited its method's verdict. Requiring the call site to
    sit INSIDE a LastEvaluatedKey-bearing loop closes both.
    """
    return [
        n
        for n in ast.walk(func)
        if isinstance(n, (ast.While, ast.For)) and _mentions_last_evaluated_key(n)
    ]


def find_query_call_sites(persistence_dir: Path) -> list[tuple[str, int, str, bool]]:
    """Return (relative_file, lineno, "ClassName.method_name", loops_on_lek) for
    every `.query(`/`.scan(` call site inside a class method under `persistence_dir`.
    """
    sites: list[tuple[str, int, str, bool]] = []
    # rglob, not glob: a repository added under adapters/persistence/<subdir>/ must
    # not be invisible to this guard (STORY-197 review, 2026-07-31).
    for path in sorted(persistence_dir.rglob("*.py")):
        if path.name == "__init__.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        rel = path.relative_to(_REPO_ROOT).as_posix()
        # EVERY function, not only direct class-body members: a module-level
        # helper calling .query()/.scan() truncates just as silently as a method
        # does (STORY-197 review, 2026-07-31).
        for func in ast.walk(tree):
            if not isinstance(func, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            owner = _enclosing_class_name(tree, func)
            qualname = f"{owner}.{func.name}" if owner else func.name
            paging_loops = _paginating_loop_bodies(func)
            for call in ast.walk(func):
                if not (
                    isinstance(call, ast.Call)
                    and isinstance(call.func, ast.Attribute)
                    and call.func.attr in _QUERY_METHODS
                ):
                    continue
                # THIS call site must sit inside a paginating loop -- its method
                # merely containing one elsewhere is not enough.
                loops = any(
                    call is inner for loop in paging_loops for inner in ast.walk(loop)
                )
                sites.append((rel, call.lineno, qualname, loops))
    return sites


def test_no_unexempted_unpaginated_persistence_query() -> None:
    """Guard (STORY-197, ZR-7): every `.query(`/`.scan(` call site under
    `adapters/persistence/` loops on `LastEvaluatedKey`, or is named in
    `_EXEMPTIONS` with a reason. A NEW unpaginated call site -- including a
    regression of a call site that loops today -- fails this test.
    """
    sites = find_query_call_sites(_PERSISTENCE_DIR)
    assert sites, (
        "No .query()/.scan() call sites found under adapters/persistence/ -- "
        "the scan itself is broken (this directory has DynamoDB repositories "
        "with query calls today)."
    )

    unexempted = [
        f"{file}:{line} [{qualname}] does not loop on LastEvaluatedKey and has no "
        f"exemption entry"
        for file, line, qualname, loops in sites
        if not loops and (file, line) not in _EXEMPTIONS
    ]

    assert not unexempted, (
        "ZR-7 violation(s): a persistence adapter reads only the first DynamoDB "
        "page against a port contract, with no exemption on record. Either add "
        "the LastEvaluatedKey pagination loop (see "
        "dynamo_observation_repository.py::in_window for the pattern), or add a "
        "reasoned entry to _EXEMPTIONS -- either 'PERMANENT -- ...' when the query "
        "is genuinely bounded by its own port's contract, or a real ZR-7 finding "
        "naming the fix story that will remove it:\n" + "\n".join(unexempted)
    )


def test_zr7_exemptions_are_still_needed() -> None:
    """Every _EXEMPTIONS entry must still correspond to a real call site that
    still fails the natural (loops-on-LastEvaluatedKey) check. A stale entry
    (its call site now loops, or vanished) means either STORY-199 landed and the
    exemption should be REMOVED, or the guard itself regressed -- either way it
    should not sit unnoticed."""
    sites = find_query_call_sites(_PERSISTENCE_DIR)
    by_coord = {(file, line): loops for file, line, _qualname, loops in sites}

    stale = []
    for (file, line), reason in _EXEMPTIONS.items():
        if (file, line) not in by_coord:
            stale.append(
                f"{file}:{line} -- no .query()/.scan() call site here any more. "
                f"Most likely the LINE MOVED (an edit above it): update this "
                f"entry's line number. Otherwise the call was removed and so "
                f"should this entry"
            )
        elif by_coord[(file, line)] and not reason.startswith("PERMANENT"):
            stale.append(
                f"{file}:{line} -- this call site now sits inside a "
                f"LastEvaluatedKey-bearing loop. VERIFY IT ACTUALLY PAGES before "
                f"removing this exemption: the check is a PROXY, and merely "
                f"REFERENCING LastEvaluatedKey (e.g. a warn-on-truncation stopgap "
                f"that still reads one page) is NOT a fix. If it pages, remove the "
                f"entry; if it does not, the entry stays and the code is broken"
            )

    assert not stale, "Stale ZR-7 exemption(s) -- update _EXEMPTIONS:\n" + "\n".join(
        stale
    )
