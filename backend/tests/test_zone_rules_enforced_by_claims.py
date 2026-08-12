"""STORY-216 standing guard: every `ENFORCED-BY` claim in
`docs/scrum/wiki/zone-rules.md`'s Adjudication table names a guard that
actually exists.

Why this exists (sprint 67's loudest finding, MAJOR-1): the Adjudication
table once marked `ZR-6` `ENFORCED-BY` a named test, and the claim was
false -- reverting the entire ZR-6 fix left the suite identically green,
because the named test pinned a different property. The legend twelve lines
above that row already forbade exactly that ("shown RED -- never merely 'is
green'") and went unread. This guard mechanises the part of the legend a
human can silently skip: it resolves every reference a row claims and fails,
naming the row, if the reference does not exist.

Grammar limit, stated honestly (quality review FIX 1.4): "every reference"
above means every reference this parser's grammar can SEE -- a code span
whose leading `ENFORCED-BY` marker sits INSIDE the backtick span, per the
house convention (`` `ENFORCED-BY path` ``). A marker written OUTSIDE its
span is more natural markdown than the convention it violates, and this
parser does not widen its grammar to accept it; instead
`_assert_reference_count_matches_markers` (the per-row floor) fails LOUDLY,
naming the row, the moment a cell's `ENFORCED-BY` count and its parsed
reference count disagree -- so that shape is caught, not silently
misresolved, even though it is never a shape this parser accepts as valid.

Cites: docs/scrum/wiki/zone-rules.md, "## Adjudication" section (STORY-197
AC6, this guard STORY-216).
"""

from __future__ import annotations

import ast
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_ZONE_RULES_PATH = _REPO_ROOT / "docs" / "scrum" / "wiki" / "zone-rules.md"
_PYPROJECT_PATH = _REPO_ROOT / "pyproject.toml"

_ADJUDICATION_HEADING = re.compile(r"^## Adjudication\b")
#: The rule ids the Adjudication table is expected to carry, one row each.
#: If a NEW rule (e.g. ZR-9) is legitimately added to zone-rules.md, extend
#: this set in the SAME commit as the row addition -- it is not itself the
#: floor being enforced, only the expected shape that floor checks against.
_EXPECTED_RULE_IDS = {f"ZR-{n}" for n in range(1, 9)}
_VERDICT_MARKERS = ("ENFORCED-BY", "GUARDABLE-DEFERRED", "UNGUARDABLE")
_CODE_SPAN = re.compile(r"`([^`]+)`")


@dataclass(frozen=True)
class AdjudicationRow:
    """One data row of the Adjudication table."""

    rule_id: str
    verdict_cell: str
    detail_cell: str
    references: tuple[str, ...]


def _split_row(row: str) -> list[str]:
    """Split a markdown table row into its cell texts (stripped), dropping
    the leading/trailing empty strings either side of the outer pipes.

    A naive split is exact only if no cell contains a literal `|` character.
    That was true of the real table at STORY-216 authoring time (confirmed by
    a one-off pipe-count spot check), but a spot check proves nothing about
    the NEXT edit -- `_assert_uniform_cell_count` below is the STANDING
    invariant that actually guards this on every run (quality review FIX
    1.2), by comparing every row's cell count against the header's.
    """
    assert row.startswith("|") and row.rstrip().endswith("|"), (
        f"Not a pipe-delimited table row: {row!r}"
    )
    parts = row.split("|")
    return [cell.strip() for cell in parts[1:-1]]


def _assert_uniform_cell_count(table_lines: list[str]) -> None:
    """Standing invariant (quality review FIX 1.2): every table line must
    split into the same number of cells as the header. A literal `|`
    character inside any cell -- an unescaped pipe an author forgot to
    escape, most plausibly in Detail-column prose -- breaks this without
    touching any backtick span or `ENFORCED-BY` marker, and would otherwise
    silently misalign every downstream cell index (a "Rule" read could
    become Verdict text, or vice versa) rather than failing loudly.
    """
    header_cell_count = len(_split_row(table_lines[0]))
    for line in table_lines:
        cell_count = len(_split_row(line))
        assert cell_count == header_cell_count, (
            f"Adjudication table row has {cell_count} cells but the header "
            f"has {header_cell_count} -- a literal '|' inside a cell (e.g. "
            f"an unescaped pipe in Detail-column prose) broke column "
            f"alignment. Row: {line!r}"
        )


def _extract_table_lines(markdown_text: str) -> list[str]:
    """Return the raw lines (header, separator, every data row) of the single
    markdown table directly under the `## Adjudication` heading.

    Scope is mechanical, not hand-picked: the legend paragraph sits ABOVE the
    heading (out of scope by construction), and `## History` is a later `##`
    heading with prose breaking the contiguous `|`-prefixed run long before
    it is reached -- so scanning "the first contiguous run of `|`-prefixed
    lines after the heading" naturally excludes both.
    """
    lines = markdown_text.splitlines()
    heading_idx = next(
        (i for i, line in enumerate(lines) if _ADJUDICATION_HEADING.match(line)),
        None,
    )
    assert heading_idx is not None, (
        "No '## Adjudication' heading found in zone-rules.md -- the table "
        "this guard depends on may have moved or been renamed. This guard "
        "cannot validate a table it cannot locate."
    )
    table_start = next(
        (i for i in range(heading_idx + 1, len(lines)) if lines[i].startswith("|")),
        None,
    )
    assert table_start is not None, (
        "No markdown table found after the '## Adjudication' heading."
    )
    table_lines = []
    for line in lines[table_start:]:
        if not line.startswith("|"):
            break
        table_lines.append(line)
    return table_lines


def _strip_leading_marker(span: str) -> str | None:
    """If `span` begins with one of the known verdict markers, return the
    remainder after the marker (possibly empty). Return `None` if `span`
    carries no recognised marker prefix at all (a bare reference)."""
    for marker in _VERDICT_MARKERS:
        if span == marker:
            return ""
        if span.startswith(marker + " "):
            return span[len(marker) + 1 :].strip()
    return None


def _references_in_verdict_cell(verdict_cell: str) -> list[str]:
    """Extract every guard reference from a Verdict-column cell (AC1, reading
    C -- the grammar pinned at plan verification). See this module's
    docstring for the full rule set.

    `ENFORCED-BY` marks the CELL, not each backtick span: a cell is only
    scanned for references at all once at least one span in it begins with
    the literal `ENFORCED-BY ` marker (marker INSIDE the span, per the house
    convention). Once gated, every span in the cell is a candidate:
      - a span equal to EXACTLY one of the known markers, with nothing else,
        is a second verdict (ZR-5's own `UNGUARDABLE`), not a reference --
        skipped.
      - a span beginning with a marker + a space has the marker stripped;
        the remainder is a reference.
      - a span with no marker prefix at all is a bare reference, joined by
        " + " to a prior one (ZR-8's finding-2 continuation spans).
    """
    spans = _CODE_SPAN.findall(verdict_cell)
    gated = any(
        span == "ENFORCED-BY" or span.startswith("ENFORCED-BY ") for span in spans
    )
    if not gated:
        return []
    references = []
    for span in spans:
        stripped = _strip_leading_marker(span)
        if stripped is None:
            references.append(span.strip())
        elif stripped:
            references.append(stripped)
        # else: a lone marker with nothing after it -- a second verdict, not
        # a reference. Skipped.
    return references


def _assert_reference_count_matches_markers(row: AdjudicationRow) -> None:
    """Per-row non-vacuity floor (quality review FIX 1.1): if `row`'s raw
    `verdict_cell` contains the literal marker `ENFORCED-BY` at all, its
    parsed `references` must be non-empty AND at least as many as the
    number of `ENFORCED-BY` occurrences in the cell.

    The global floor (`assert all_references` in the real-file test) only
    catches a TOTAL collapse to zero across the whole table -- a single row
    whose references silently drop to zero (or whose ZR-8-style multi-
    reference cell silently drops from 4 to 1) stays invisible to it, and
    because the shown-RED check filters on `row.references` too, that row
    escapes BOTH checks at once and the guard stays green throughout. The
    single most likely cause is the verdict marker written OUTSIDE its
    backtick span -- this parser's grammar requires it INSIDE the span (the
    house convention, `` `ENFORCED-BY path` ``) -- which is MORE natural
    markdown than the convention it violates, so nothing else guards against
    an author reasonably getting this wrong.
    """
    marker_count = row.verdict_cell.count("ENFORCED-BY")
    if marker_count == 0:
        return
    assert row.references and len(row.references) >= marker_count, (
        f"{row.rule_id}: Verdict cell contains {marker_count} 'ENFORCED-BY' "
        f"marker(s) but only {len(row.references)} reference(s) parsed out "
        f"of it ({row.references!r}). Likely cause: the marker sits OUTSIDE "
        f"its backtick code span -- this parser's grammar requires "
        f"`` `ENFORCED-BY path` `` with the marker INSIDE the span. Fix the "
        f"row's markdown to that convention; do not weaken this check."
    )


def parse_adjudication_table(markdown_text: str) -> list[AdjudicationRow]:
    """Parse the Adjudication table into one `AdjudicationRow` per data row,
    in file order, applying AC1's reference grammar to each Verdict cell.
    """
    table_lines = _extract_table_lines(markdown_text)
    assert len(table_lines) >= 3, (
        "Adjudication table has no data rows (only a header/separator row, "
        "or nothing at all) -- the heading or table structure has drifted."
    )
    _assert_uniform_cell_count(table_lines)
    header_cells = [c.lower() for c in _split_row(table_lines[0])]
    assert "rule" in header_cells and "verdict" in header_cells, (
        f"Adjudication table header is missing an expected 'Rule'/'Verdict' "
        f"column: {header_cells!r}"
    )
    rule_idx = header_cells.index("rule")
    verdict_idx = header_cells.index("verdict")
    detail_idx = header_cells.index("detail") if "detail" in header_cells else None

    rows = []
    for line in table_lines[2:]:
        cells = _split_row(line)
        rule_id = cells[rule_idx]
        verdict_cell = cells[verdict_idx]
        detail_cell = cells[detail_idx] if detail_idx is not None else ""
        references = tuple(_references_in_verdict_cell(verdict_cell))
        row = AdjudicationRow(rule_id, verdict_cell, detail_cell, references)
        _assert_reference_count_matches_markers(row)
        rows.append(row)
    return rows


# ---------------------------------------------------------------------------
# Reference resolution (AC1's two reference kinds, AC2's AST test-name check).
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ResolvedReference:
    """The outcome of resolving one guard reference."""

    reference: str
    exists: bool
    detail: str


def _function_exists(path: Path, test_name: str) -> bool:
    """AST-parse `path` and return True iff it defines a function (`def` or
    `async def`, at any nesting level) named `test_name`.

    AC2 residue, stated here and in the calling assertion's failure message:
    this checks DEFINITION only. A test that exists but is skipped, xfailed,
    or deselected still counts as present -- this guard has no opinion on
    whether a named test currently RUNS, only on whether it still EXISTS. No
    `pytest --collect-only` subprocess is run (a pytest run inside a pytest
    run is slow and recursion-prone; settled at refinement).
    """
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == test_name
        for node in ast.walk(tree)
    )


def _is_path_like(token: str) -> bool:
    """A reference is treated as a filesystem path if it contains a `/` or
    ends in `.py`; otherwise it is treated as an import-linter contract name
    (ZR-1's row: `inbound-adapters-dont-persist` has neither)."""
    return "/" in token or token.endswith(".py")


def _import_linter_contract_names(pyproject_path: Path) -> set[str]:
    """Every `name` declared under `[[tool.importlinter.contracts]]` in
    `pyproject_path` -- the set a non-path reference resolves against."""
    with open(pyproject_path, "rb") as f:
        config = tomllib.load(f)
    contracts = config.get("tool", {}).get("importlinter", {}).get("contracts", [])
    return {c["name"] for c in contracts if "name" in c}


def resolve_reference(
    reference: str, repo_root: Path, contract_names: set[str]
) -> ResolvedReference:
    """Resolve one guard reference (AC1's two kinds):
    - `path::test_name` -- the path must exist AND AST-parsing it must find
      a `FunctionDef`/`AsyncFunctionDef` named `test_name` (AC2).
    - a bare path (no `::`, but `/`-bearing or `.py`-suffixed) -- the path
      must exist.
    - anything else -- resolved as an import-linter contract name against
      `contract_names` (ZR-1's row).
    """
    if "::" in reference:
        file_part, test_name = reference.split("::", 1)
        path = repo_root / file_part
        if not path.is_file():
            return ResolvedReference(
                reference, False, f"path does not exist: {file_part}"
            )
        if not _function_exists(path, test_name):
            return ResolvedReference(
                reference,
                False,
                f"path exists but defines no test function named "
                f"'{test_name}': {file_part}",
            )
        return ResolvedReference(reference, True, "")

    if _is_path_like(reference):
        path = repo_root / reference
        if not path.is_file():
            return ResolvedReference(
                reference, False, f"path does not exist: {reference}"
            )
        return ResolvedReference(reference, True, "")

    if reference not in contract_names:
        return ResolvedReference(
            reference,
            False,
            f"no import-linter contract named '{reference}' in pyproject.toml",
        )
    return ResolvedReference(reference, True, "")


# ---------------------------------------------------------------------------
# Meta-tests: prove the parser itself, against synthetic fixtures, before it
# is trusted against the real file (same discipline as
# test_zr7_pagination_guard.py's "prove it fires against a throwaway file").
# ---------------------------------------------------------------------------

_FIXTURE_TABLE = """\
# Some doc

Some legend paragraph mentioning ENFORCED-BY as prose, out of scope.

## Adjudication

| Rule | Verdict | Detail |
| --- | --- | --- |
| ZR-1 | `ENFORCED-BY some-contract-name` | Detail prose ENFORCED-BY test_foo.py is prose, out of scope |
| ZR-2 | `ENFORCED-BY backend/tests/test_x.py::test_y` | Shown RED by mutation. |
| ZR-3 | `ENFORCED-BY backend/tests/test_bare.py` | Shown RED. |
| ZR-4 | `ENFORCED-BY backend/tests/test_a.py::test_b` (STORY-1) + `backend/tests/test_c.py::test_d` | Shown RED twice. |
| ZR-5 | `ENFORCED-BY backend/tests/test_e.py::test_f` (code-level half only); the operational half stays `UNGUARDABLE` | Shown RED once. |
| ZR-6 | `FIXED -- NO STANDING GUARD` | No guard, and no ENFORCED-BY claim here. |
| ZR-7 | `GUARDABLE-DEFERRED` | Deferred, no reference yet. |
| ZR-8 | `ENFORCED-BY backend/tests/test_g.py::test_h` | Shown RED. |

## History

A bare ENFORCED-BY backend/tests/test_history_prose.py mention that is prose, out of scope, and
line-wrapped away from any table structure.
"""


def test_extract_table_lines_scopes_to_the_adjudication_table_only() -> None:
    """The legend paragraph (above the heading) and `## History` (a later
    heading) must not leak into the extracted table lines, even though both
    contain the literal substring `ENFORCED-BY`. (Detail-column prose INSIDE
    the table, e.g. ZR-1's fixture row, is legitimately part of a table line
    at this extraction stage -- its exclusion from reference-resolution is a
    later, column-based concern, tested separately.)"""
    table_lines = _extract_table_lines(_FIXTURE_TABLE)
    assert table_lines[0] == "| Rule | Verdict | Detail |"
    assert len(table_lines) == 10  # header + separator + 8 data rows
    joined = "\n".join(table_lines)
    assert "test_history_prose.py" not in joined


def test_split_row_drops_outer_pipes_and_strips_cells() -> None:
    assert _split_row("| ZR-1 | `ENFORCED-BY x` | some detail |") == [
        "ZR-1",
        "`ENFORCED-BY x`",
        "some detail",
    ]


def test_parse_adjudication_table_finds_all_eight_rule_ids() -> None:
    rows = parse_adjudication_table(_FIXTURE_TABLE)
    assert {row.rule_id for row in rows} == _EXPECTED_RULE_IDS


def test_references_reading_c_grammar_on_every_shape() -> None:
    """Reading C (AC1's pinned grammar), exercised against one synthetic
    instance of each of the six real shapes."""
    rows = {row.rule_id: row for row in parse_adjudication_table(_FIXTURE_TABLE)}

    # ZR-1 shape: single ENFORCED-BY span, non-path token (contract name).
    assert rows["ZR-1"].references == ("some-contract-name",)

    # ZR-2 shape: single ENFORCED-BY span, path::test_name.
    assert rows["ZR-2"].references == ("backend/tests/test_x.py::test_y",)

    # ZR-3 shape: single ENFORCED-BY span, bare path (no ::test_name).
    assert rows["ZR-3"].references == ("backend/tests/test_bare.py",)

    # ZR-4 shape: ENFORCED-BY span + " + "-joined bare continuation span.
    assert rows["ZR-4"].references == (
        "backend/tests/test_a.py::test_b",
        "backend/tests/test_c.py::test_d",
    )

    # ZR-5 shape: ENFORCED-BY span + a second, lone UNGUARDABLE verdict span
    # (not a reference) + a parenthetical OUTSIDE the span (must not leak in).
    assert rows["ZR-5"].references == ("backend/tests/test_e.py::test_f",)

    # ZR-6 shape: no ENFORCED-BY anywhere in the cell -- zero references.
    assert rows["ZR-6"].references == ()

    # ZR-7 shape here: GUARDABLE-DEFERRED only, no ENFORCED-BY -- zero refs.
    assert rows["ZR-7"].references == ()

    # ZR-8 shape (single-finding form here): one ENFORCED-BY span.
    assert rows["ZR-8"].references == ("backend/tests/test_g.py::test_h",)


def test_references_pins_zr8s_real_four_reference_two_finding_shape() -> None:
    """Quality review FIX 1.3: the main grammar test above only exercises
    ZR-8 in its SINGLE-reference form. ZR-8's REAL cell is two findings, two
    `ENFORCED-BY` spans, and two more bare, ` + `-joined continuation spans
    attached to the second -- four references total. If a future grammar
    change silently narrowed that to 1, 30% of the guard's real-table
    coverage would vanish while staying green; this pins the shape directly,
    independent of `zone-rules.md`'s current wording."""
    cell = (
        "Finding 1: `ENFORCED-BY backend/tests/test_a.py::test_b` (STORY-1, "
        "sprint-1). Finding 2: `ENFORCED-BY backend/tests/test_c.py::test_d` "
        "(AC4) + `backend/tests/test_e.py::test_f` + "
        "`backend/tests/test_g.py::test_h` (STORY-2, sprint-1)"
    )
    assert _references_in_verdict_cell(cell) == [
        "backend/tests/test_a.py::test_b",
        "backend/tests/test_c.py::test_d",
        "backend/tests/test_e.py::test_f",
        "backend/tests/test_g.py::test_h",
    ]


def test_function_exists_finds_a_present_function_at_any_nesting_level(
    tmp_path,
) -> None:
    module = tmp_path / "mod.py"
    module.write_text(
        "def test_top_level():\n    pass\n\n\n"
        "class Foo:\n    def test_nested(self):\n        pass\n",
        encoding="utf-8",
    )
    assert _function_exists(module, "test_top_level") is True
    assert _function_exists(module, "test_nested") is True
    assert _function_exists(module, "test_absent") is False


def test_resolve_reference_path_with_test_name(tmp_path) -> None:
    repo_root = tmp_path
    test_file = repo_root / "backend" / "tests" / "test_real.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text("def test_present():\n    pass\n", encoding="utf-8")

    ok = resolve_reference("backend/tests/test_real.py::test_present", repo_root, set())
    assert ok.exists is True

    missing_path = resolve_reference(
        "backend/tests/does_not_exist.py::test_present", repo_root, set()
    )
    assert missing_path.exists is False

    missing_test = resolve_reference(
        "backend/tests/test_real.py::test_absent", repo_root, set()
    )
    assert missing_test.exists is False


def test_resolve_reference_bare_path(tmp_path) -> None:
    repo_root = tmp_path
    test_file = repo_root / "backend" / "tests" / "test_bare_real.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text("x = 1\n", encoding="utf-8")

    ok = resolve_reference("backend/tests/test_bare_real.py", repo_root, set())
    assert ok.exists is True

    missing = resolve_reference(
        "backend/tests/does_not_exist_bare.py", repo_root, set()
    )
    assert missing.exists is False


def test_resolve_reference_contract_name(tmp_path) -> None:
    repo_root = tmp_path
    contract_names = {"some-real-contract"}

    ok = resolve_reference("some-real-contract", repo_root, contract_names)
    assert ok.exists is True

    missing = resolve_reference("no-such-contract", repo_root, contract_names)
    assert missing.exists is False


def test_import_linter_contract_names_reads_pyproject(tmp_path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        "[[tool.importlinter.contracts]]\n"
        'name = "contract-a"\n\n'
        "[[tool.importlinter.contracts]]\n"
        'name = "contract-b"\n',
        encoding="utf-8",
    )
    assert _import_linter_contract_names(pyproject) == {"contract-a", "contract-b"}


def test_per_row_floor_catches_marker_written_outside_the_backtick_span() -> None:
    """Quality review FIX 1.1, edit 1 -- the most natural markdown mistake:
    writing `ENFORCED-BY \\`path\\`` with the marker OUTSIDE the span instead
    of INSIDE it (the house convention this parser's grammar depends on).
    `_references_in_verdict_cell` sees a plain, unmarked span and returns
    zero references while the cell plainly claims a guard -- the per-row
    floor must catch that, naming the row."""
    broken = _FIXTURE_TABLE.replace(
        "| ZR-7 | `GUARDABLE-DEFERRED` | Deferred, no reference yet. |",
        "| ZR-7 | ENFORCED-BY `backend/tests/test_zr7.py` | Shown RED. |",
    )
    try:
        parse_adjudication_table(broken)
    except AssertionError as exc:
        assert "ZR-7" in str(exc)
    else:
        raise AssertionError(
            "parse_adjudication_table did not raise on a marker written "
            "outside its backtick span -- the row's claim silently vanished."
        )


def test_per_row_floor_catches_a_lone_marker_span_with_reference_outside() -> None:
    """Quality review FIX 1.1, edit 2: a lone `` `ENFORCED-BY` `` span
    (correctly recognised as a marker, not a reference) with its reference
    written OUTSIDE any span at all. Zero references parse out, silently."""
    broken = _FIXTURE_TABLE.replace(
        "| ZR-7 | `GUARDABLE-DEFERRED` | Deferred, no reference yet. |",
        "| ZR-7 | `ENFORCED-BY` backend/tests/test_zr7.py | Shown RED. |",
    )
    try:
        parse_adjudication_table(broken)
    except AssertionError as exc:
        assert "ZR-7" in str(exc)
    else:
        raise AssertionError(
            "parse_adjudication_table did not raise on a lone ENFORCED-BY "
            "marker span whose reference sits outside any span."
        )


def test_assert_uniform_cell_count_catches_a_stray_pipe_inside_a_cell() -> None:
    """Quality review FIX 1.2: a literal '|' inside a cell (e.g. an
    unescaped pipe an author forgot to escape) breaks column alignment
    without touching any backtick span or ENFORCED-BY marker at all -- a
    standing invariant on cell count catches it. This replaces the
    authoring-time-only pipe-count spot check `_split_row`'s docstring used
    to lean on: a spot check proves nothing about the NEXT edit."""
    broken = _FIXTURE_TABLE.replace(
        "| ZR-7 | `GUARDABLE-DEFERRED` | Deferred, no reference yet. |",
        "| ZR-7 | `GUARDABLE-DEFERRED` | Deferred, with a stray | pipe. |",
    )
    try:
        parse_adjudication_table(broken)
    except AssertionError as exc:
        message = str(exc)
        assert "ZR-7" in message
        assert "cells" in message
    else:
        raise AssertionError(
            "parse_adjudication_table did not raise on a row with a stray "
            "'|' inside a cell -- column alignment silently broke."
        )


def test_non_vacuity_floor_trips_on_a_heading_that_has_moved() -> None:
    """If the '## Adjudication' heading is missing entirely (e.g. renamed,
    or the table moved to a different section), the parser must fail loudly
    -- never silently return zero rows. This is the exact failure mode
    sprint-67's MAJOR-1 was: a guard that checks nothing and reports green."""
    drifted = _FIXTURE_TABLE.replace("## Adjudication", "## Adjudicationnn")
    try:
        parse_adjudication_table(drifted)
    except AssertionError as exc:
        assert "Adjudication" in str(exc)
    else:
        raise AssertionError(
            "parse_adjudication_table did not raise on a missing heading -- "
            "a moved/renamed table would silently parse as zero rows."
        )


# ---------------------------------------------------------------------------
# The real guard: run everything above against the REAL zone-rules.md and
# the REAL pyproject.toml. AC1's non-vacuity floor + AC6 (a failing row is
# fixed, never exempted, under THIS specified grammar).
# ---------------------------------------------------------------------------


def test_every_enforced_by_reference_in_adjudication_table_resolves() -> None:
    """STORY-216 AC1/AC2/AC6: every `ENFORCED-BY` reference THIS PARSER CAN
    SEE in the REAL Adjudication table (`docs/scrum/wiki/zone-rules.md`)
    resolves -- a path reference exists on disk, a `path::test_name`
    reference's file ALSO defines a function of that name (AST-checked,
    existence only -- a test that is skipped/xfailed/deselected still counts
    as present here, see `_function_exists`), and a non-path reference names
    a real import-linter contract in `pyproject.toml`.

    Grammar limit (quality review FIX 1.4): "every reference" means every
    reference matching this parser's grammar -- a code span whose leading
    `ENFORCED-BY` marker sits INSIDE the backtick span (the house
    convention). A marker written OUTSIDE its span is not resolved by this
    function at all; it is instead caught, loudly, by the PER-ROW floor
    below (`_assert_reference_count_matches_markers`, run inside
    `parse_adjudication_table`), never silently misresolved.

    AC1's non-vacuity floor: all eight rule ids ZR-1..ZR-8 must be found, and
    at least one ENFORCED-BY reference must resolve, or this guard has gone
    silently vacuous -- the exact failure mode (sprint-67 MAJOR-1) it exists
    to end. That floor is GLOBAL; the per-row floor inside
    `parse_adjudication_table` catches a single row's silent collapse to
    zero (or a partial collapse, e.g. ZR-8's 4 references dropping to 1)
    that the global floor alone would miss.

    AC6: a row failing under THIS specified grammar is fixed, never
    exempted -- there is no exemption list here on principle. But note the
    other half of AC6: "a failing row" means one failing THIS grammar. If a
    row you believe is correct fails here, the grammar may be wrong -- stop
    and say so rather than editing the row to satisfy the parser.
    """
    markdown_text = _ZONE_RULES_PATH.read_text(encoding="utf-8")
    rows = parse_adjudication_table(markdown_text)

    rule_ids = {row.rule_id for row in rows}
    assert rule_ids == _EXPECTED_RULE_IDS, (
        f"Expected all eight rule ids ZR-1..ZR-8, found {sorted(rule_ids)} -- "
        f"the Adjudication table's row set has drifted. (If a NEW rule, e.g. "
        f"ZR-9, was legitimately added to zone-rules.md, extend "
        f"_EXPECTED_RULE_IDS in the SAME commit as the row addition -- this "
        f"assertion is not itself evidence of a defect.)"
    )

    all_references = [
        (row.rule_id, reference) for row in rows for reference in row.references
    ]
    assert all_references, (
        "Non-vacuity floor tripped (AC1): zero ENFORCED-BY references were "
        "found across the whole Adjudication table. Either every rule "
        "genuinely lost its guard (very unlikely) or this parser's table-"
        "location or grammar broke silently -- exactly sprint-67's MAJOR-1, "
        "reproduced inside the guard built to end it. Investigate before "
        "trusting a green run."
    )

    contract_names = _import_linter_contract_names(_PYPROJECT_PATH)
    failures = [
        f"{rule_id}: `{reference}` -- {resolved.detail}"
        for rule_id, reference in all_references
        for resolved in [resolve_reference(reference, _REPO_ROOT, contract_names)]
        if not resolved.exists
    ]

    assert not failures, (
        "Adjudication table row(s) claim ENFORCED-BY a guard that does not "
        "exist (STORY-216, closing sprint-67's MAJOR-1 -- ZR-6's row once "
        "claimed a guard that reverting the fix proved false). Fix the "
        "reference or the code/contract it should point at. Per AC6: never "
        "add an exemption here, and never edit a row just to make this "
        "parser pass -- if you believe the row is genuinely correct and this "
        "check is wrong, stop and say so instead of editing either. NOTE the "
        "limit of a `::test_name` failure specifically (AC2): it means the "
        "named function no longer EXISTS (AST-checked) -- a test that "
        "exists but is skipped, xfailed, or deselected would NOT fail here; "
        "this check has no opinion on whether a test currently runs.\n"
        + "\n".join(failures)
    )


def test_every_enforced_by_row_records_a_shown_red_demonstration() -> None:
    """STORY-216 AC3 -- the honest half. "Has been shown RED" is prose in the
    Detail column; this test can verify a row RECORDS a red demonstration
    (the substring "shown red", case-insensitive), but it CANNOT verify the
    demonstration actually happened. A green run here is never proof the
    mutations were real -- nobody may read it that way.
    """
    markdown_text = _ZONE_RULES_PATH.read_text(encoding="utf-8")
    rows = parse_adjudication_table(markdown_text)
    enforced_rows = [row for row in rows if row.references]
    assert enforced_rows, "Non-vacuity floor: no ENFORCED-BY rows found to check."

    missing = [
        row.rule_id
        for row in enforced_rows
        if "shown red" not in row.detail_cell.lower()
    ]
    assert not missing, (
        "Row(s) claim ENFORCED-BY but their Detail column records no "
        "'shown RED' demonstration (the legend's own requirement -- a guard "
        "is not ENFORCED-BY until it has been shown RED, never merely 'is "
        "green'). Perform the mutation and record it; never satisfy this "
        "check by adding the phrase 'shown RED' with no demonstration "
        "behind it. NOTE the limit of this check: it verifies the row "
        "RECORDS a red demonstration, never that the demonstration actually "
        "happened -- that half is not mechanically verifiable.\n" + "\n".join(missing)
    )
