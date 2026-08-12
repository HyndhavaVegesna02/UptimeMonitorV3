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

Cites: docs/scrum/wiki/zone-rules.md, "## Adjudication" section (STORY-197
AC6, this guard STORY-216).

Built incrementally, table-scoping first: the extraction of the single
Adjudication table's raw lines, proven against a synthetic fixture that
deliberately includes ENFORCED-BY-bearing prose OUTSIDE the table (the
legend above the heading, and a later "## History" section) to prove scope
is mechanical, not accidental.
"""

from __future__ import annotations

import ast
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path

_ADJUDICATION_HEADING = re.compile(r"^## Adjudication\b")
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

    Every row in the Adjudication table carries exactly one delimiter pipe
    per cell boundary -- no cell contains a literal `|` character (confirmed
    by a direct pipe-count-per-line spot check at STORY-216 authoring time),
    so a naive split is exact here, not an approximation.
    """
    assert row.startswith("|") and row.rstrip().endswith("|"), (
        f"Not a pipe-delimited table row: {row!r}"
    )
    parts = row.split("|")
    return [cell.strip() for cell in parts[1:-1]]


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


def parse_adjudication_table(markdown_text: str) -> list[AdjudicationRow]:
    """Parse the Adjudication table into one `AdjudicationRow` per data row,
    in file order, applying AC1's reference grammar to each Verdict cell.
    """
    table_lines = _extract_table_lines(markdown_text)
    assert len(table_lines) >= 3, (
        "Adjudication table has no data rows (only a header/separator row, "
        "or nothing at all) -- the heading or table structure has drifted."
    )
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
        rows.append(AdjudicationRow(rule_id, verdict_cell, detail_cell, references))
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
