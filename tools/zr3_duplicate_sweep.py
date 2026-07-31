"""ZR-3 duplicated-declaration sweep (STORY-196, `docs/scrum/wiki/zone-rules.md` ZR-3).

Finds every value colliding between the two `backend/src/` declaration shapes ZR-3
pins and every literal under `tools/` (module level or inside a function body).
Adjudication (`MUST-IMPORT-FROM-SRC` vs `INDEPENDENT`) is NOT automated here — that
requires reading each hit for whether the `tools/` side actually obtains the value
from `src` at runtime (ZR-3's own "import-edge is not the criterion, this-value-was-
obtained-from-src is"). See `docs/scrum/sprints/2026-07-31-sprint-66/
audit-api-composition-tools.md` §3 for the adjudicated results this sweep produced.

Scope, exactly as pinned by `zone-rules.md` ZR-3 (STORY-194 acceptance correction,
2026-07-31):

- `backend/src/` side — TWO declaration shapes: (i) a module-level UPPER_CASE
  constant assignment (`Assign` or `AnnAssign`), anywhere under `backend/src/`;
  (ii) a settings/config field default — scoped here to
  `backend/src/composition/settings.py` and `backend/src/composition/config.py`
  (the two files literally named settings/config, matching ZR-3's own illustrative
  citation `backend/src/composition/settings.py:21-22`): every class-level
  annotated field assignment with a literal (`str`/`int`/`float`/`bool`) default,
  inside a class decorated `@dataclass` or subclassing `BaseModel`.
- `tools/` side — every literal (`str`/`int`/`float`/`bool`) ANYWHERE under
  `tools/`, including inside function bodies, per ZR-3's corrected scope.

**Stated limitation (STORY-196 quality-review fix round, 2026-07-31):** the
`backend/src/` side collects only `ast.Constant`-valued declarations. A module-level
UPPER_CASE name assigned a `dict`/`tuple`/function-call value (e.g.
`PROVISIONAL_STATUS_MAPPING`, `_DQL_BREAKING_CHARS`, `STATUS_SEVERITY`,
`DEFAULT_OVERLAP`, `FUTURE_TOLERANCE`, `_SECTION_10_DEFAULTS`) is invisible to this
sweep's literal-equality comparison — unpacking every nested literal inside those
would reintroduce the "wide reading finds 101, mostly noise" problem ZR-3's own
measurement note already rejected. Verified at STORY-196 sprint-66: 20 module-level
UPPER_CASE constants exist under `backend/src/`; 8 are `ast.Constant`-valued (visible
to this sweep) and 12 are not (invisible). None of the 12 hides a live violation this
sweep would have caught by unpacking it (checked by reading, not by an exhaustive
nested sweep) — but a reader of a `0` collision count on any of those 12 should not
read it as "checked and clean," only as "not this sweep's job."

**Self-exclusion (STORY-197):** the `tools/`-side scan skips this script's own source
and its sibling `tools/citation_sweep.py` -- committing both under `tools/` (STORY-196
quality-review fix round) made the sweep self-referential, finding coincidental numeral
hits inside their OWN source (tuple-index literals, argv-length comparisons, an exit
code) that STORY-196's audit report had to adjudicate `INDEPENDENT` by hand every run.
`find_collisions` is the shared collection+comparison logic this module's own CLI
(`main`, below) and the STORY-197 standing guard
(`backend/tests/test_zr3_duplicate_declarations.py`) both call, so the two can never
silently drift out of sync with each other.

Usage: ``python tools/zr3_duplicate_sweep.py [repo_root]`` (defaults to CWD).
"""

from __future__ import annotations

import ast
import sys
from collections import defaultdict
from pathlib import Path

#: Values too generic to be worth reporting even when they collide (pure noise --
#: 0/1/True/False/None/""/"utf-8" collide constantly and were exactly what the wide
#: reading in zone-rules.md flagged as unusable). Kept SMALL and stated openly --
#: everything else is reported.
_NOISE_VALUES = {0, 1, -1, True, False, None, "", "utf-8"}

#: Sweep-infrastructure files excluded from the `tools/`-side scan (STORY-197): these
#: two scripts live under `tools/` themselves, so an unqualified scan finds
#: coincidental numeral hits inside their OWN source (tuple-index literals, argv-length
#: comparisons, an exit code) that carry no relationship to any backend/src/
#: declaration. Add a future sweep/report script's filename here if it is committed
#: under `tools/` too.
_SELF_EXCLUDE_NAMES = {"zr3_duplicate_sweep.py", "citation_sweep.py"}

_NOT_LITERAL = object()


def _is_upper_case_name(name: str) -> bool:
    return name.isupper() and any(c.isalpha() for c in name)


def _literal_value(node: ast.AST):
    if (
        isinstance(node, ast.Constant)
        and isinstance(node.value, (str, int, float, bool))
        and not isinstance(node.value, complex)
    ):
        return node.value
    return _NOT_LITERAL


def collect_src_declarations(src_root: Path) -> list[tuple]:
    """Return ``[(value, file, line, kind, name), ...]`` for `backend/src/` shape
    (i) [module-level UPPER_CASE constants, anywhere] and shape (ii)
    [settings.py/config.py field defaults]."""
    out: list[tuple] = []
    for path in sorted(src_root.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError:
            continue
        rel = path.relative_to(src_root.parent.parent).as_posix()

        # Shape (i): module-level UPPER_CASE constant, any file.
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and _is_upper_case_name(target.id):
                        val = _literal_value(node.value)
                        if val is not _NOT_LITERAL:
                            out.append((val, rel, node.lineno, "shape-i", target.id))
            elif isinstance(node, ast.AnnAssign):
                if isinstance(node.target, ast.Name) and _is_upper_case_name(
                    node.target.id
                ):
                    if node.value is not None:
                        val = _literal_value(node.value)
                        if val is not _NOT_LITERAL:
                            out.append(
                                (val, rel, node.lineno, "shape-i", node.target.id)
                            )

        # Shape (ii): settings.py / config.py class-level field defaults.
        if (
            path.name in ("settings.py", "config.py")
            and path.parent.name == "composition"
        ):
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for stmt in node.body:
                        if isinstance(stmt, ast.AnnAssign) and isinstance(
                            stmt.target, ast.Name
                        ):
                            if stmt.value is not None:
                                val = _literal_value(stmt.value)
                                if val is not _NOT_LITERAL:
                                    out.append(
                                        (
                                            val,
                                            rel,
                                            stmt.lineno,
                                            "shape-ii",
                                            f"{node.name}.{stmt.target.id}",
                                        )
                                    )
    return out


def collect_tools_literals(tools_root: Path) -> list[tuple]:
    """Return ``[(value, file, line, context), ...]`` for EVERY literal anywhere
    under `tools/` (module level or inside a function body), excluding the sweep's
    own infrastructure files (see `_SELF_EXCLUDE_NAMES`)."""
    out: list[tuple] = []
    for path in sorted(tools_root.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        if path.name in _SELF_EXCLUDE_NAMES:
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError:
            continue
        rel = path.relative_to(tools_root.parent).as_posix()
        for node in ast.walk(tree):
            val = _literal_value(node)
            if val is not _NOT_LITERAL:
                out.append((val, rel, node.lineno, "literal"))
    return out


def _dedupe_hits(src_decls: list[tuple], tools_lits: list[tuple]) -> list[tuple]:
    """Pure comparison step: every (backend/src declared value) == (tools/ literal)
    collision, noise excluded, deduped by (value, src_file, src_line, tools_file,
    tools_line). Split out of `find_collisions` so a caller that already has both
    lists (e.g. `main`, for its header counts) does not re-walk the filesystem."""
    src_by_value: dict = defaultdict(list)
    for val, file, line, kind, name in src_decls:
        src_by_value[(val, type(val))].append((file, line, kind, name))

    hits = []
    for val, file, line, _ in tools_lits:
        if val in _NOISE_VALUES:
            continue
        key = (val, type(val))
        if key in src_by_value:
            for src_file, src_line, kind, name in src_by_value[key]:
                hits.append((val, src_file, src_line, kind, name, file, line))

    seen = set()
    deduped = []
    for h in hits:
        dedup_key = (h[0], h[1], h[2], h[5], h[6])
        if dedup_key not in seen:
            seen.add(dedup_key)
            deduped.append(h)
    return deduped


def find_collisions(repo_root: Path) -> list[tuple]:
    """Convenience wrapper: collect both sides under `repo_root` and return the
    deduped collision list. Shared by `main` (the CLI report) and the STORY-197
    standing guard (`backend/tests/test_zr3_duplicate_declarations.py`)."""
    src_decls = collect_src_declarations(repo_root / "backend" / "src")
    tools_lits = collect_tools_literals(repo_root / "tools")
    return _dedupe_hits(src_decls, tools_lits)


def main() -> None:
    repo_root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
    src_root = repo_root / "backend" / "src"
    tools_root = repo_root / "tools"

    src_decls = collect_src_declarations(src_root)
    tools_lits = collect_tools_literals(tools_root)

    print(
        f"backend/src/ declarations collected: {len(src_decls)} "
        f"({sum(1 for d in src_decls if d[3] == 'shape-i')} shape-i, "
        f"{sum(1 for d in src_decls if d[3] == 'shape-ii')} shape-ii)"
    )
    print(f"tools/ literal occurrences collected: {len(tools_lits)}")
    print()

    deduped = _dedupe_hits(src_decls, tools_lits)

    print(
        f"Colliding pairs (backend/src declared value == tools/ literal), "
        f"noise excluded: {len(deduped)}"
    )
    print()
    for val, src_file, src_line, kind, name, tools_file, tools_line in sorted(
        deduped, key=lambda h: (h[5], h[6])
    ):
        print(
            f"  value={val!r} ({type(val).__name__})  "
            f"SRC: {src_file}:{src_line} [{kind} {name}]  "
            f"TOOLS: {tools_file}:{tools_line}"
        )


if __name__ == "__main__":
    main()
