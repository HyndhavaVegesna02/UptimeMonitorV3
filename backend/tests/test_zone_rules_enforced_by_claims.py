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

import re
from dataclasses import dataclass

_ADJUDICATION_HEADING = re.compile(r"^## Adjudication\b")
_EXPECTED_RULE_IDS = {f"ZR-{n}" for n in range(1, 9)}


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


def _references_in_verdict_cell(verdict_cell: str) -> list[str]:
    """Placeholder -- the reference grammar (AC1) is added in the next TDD
    step. For now every cell yields zero references."""
    return []


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
