"""ZR-7 standing guard (STORY-197): every DynamoDB `.query(`/`.scan(` call site under
`adapters/persistence/` either loops on `LastEvaluatedKey` or is named, with a reason,
in `_EXEMPTIONS` below.

Cites: `docs/scrum/wiki/zone-rules.md` ZR-7 (an adapter must satisfy the port contract
it implements -- silently truncating a result set the port promises in full is a
boundary violation) and its Coverage verdict, which decides the implementable form this
test mechanises verbatim: assert the HARD, DECIDABLE half (does the call site's own
enclosing method loop on `LastEvaluatedKey`) rather than the undecidable half
("provably bounded" against an English port docstring), and carry a named exemption
list with a reason per entry -- the same shape ZR-1's own contract sketch uses.
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

Maintenance note for a future author (AC3): a new `adapters/persistence/*.py` file or
method is scanned automatically -- nothing to update for the common case (a method that
correctly loops on `LastEvaluatedKey` needs no exemption at all). The ONLY manual step
is `_EXEMPTIONS` below: a method that legitimately does not loop (either a genuinely
bounded query, like `list_recent`'s `Limit=limit`, or an accepted-but-not-yet-fixed
violation) must be added here BY NAME, with a reason and -- for a real violation, never
for a bounded-by-contract exemption -- the fix story that will remove the entry. An
unrecognised, unpaginated call site is always a guard FAILURE, never silently accepted.
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
    ): "NOT a ZR-7 violation, permanent exemption: list_recent's own port contract "
    "(publication_repository.py) promises only 'up to `limit` most-recent', a "
    "stated bound, not 'all' -- Limit=limit correctly honors it.",
}


def _contains_last_evaluated_key(node: ast.AST) -> bool:
    """True if `node`'s subtree references the string "LastEvaluatedKey" anywhere --
    the decidable proxy ZR-7's coverage verdict names for "this method loops"."""
    return any(
        isinstance(n, ast.Constant) and n.value == "LastEvaluatedKey"
        for n in ast.walk(node)
    )


def find_query_call_sites(persistence_dir: Path) -> list[tuple[str, int, str, bool]]:
    """Return (relative_file, lineno, "ClassName.method_name", loops_on_lek) for
    every `.query(`/`.scan(` call site inside a class method under `persistence_dir`.
    """
    sites: list[tuple[str, int, str, bool]] = []
    for path in sorted(persistence_dir.glob("*.py")):
        if path.name == "__init__.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        rel = path.relative_to(_REPO_ROOT).as_posix()
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            for child in node.body:
                if not isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                loops = _contains_last_evaluated_key(child)
                for call in ast.walk(child):
                    if (
                        isinstance(call, ast.Call)
                        and isinstance(call.func, ast.Attribute)
                        and call.func.attr in _QUERY_METHODS
                    ):
                        qualname = f"{node.name}.{child.name}"
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
        "dynamo_observation_repository.py::in_window for the pattern), or -- only "
        "if the query is genuinely bounded by its own port's contract -- add a "
        "reasoned entry to _EXEMPTIONS:\n" + "\n".join(unexempted)
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
            stale.append(f"{file}:{line} -- call site no longer found at all")
        elif by_coord[(file, line)] and "Fix: STORY-199" in reason:
            stale.append(
                f"{file}:{line} -- now loops on LastEvaluatedKey; remove this "
                f"exemption, the fix has landed"
            )

    assert not stale, (
        "Stale ZR-7 exemption(s) -- update _EXEMPTIONS:\n" + "\n".join(stale)
    )
