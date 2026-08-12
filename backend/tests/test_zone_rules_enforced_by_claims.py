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

_ADJUDICATION_HEADING = re.compile(r"^## Adjudication\b")


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
    assert len(table_lines) == 4  # header + separator + 2 data rows
    joined = "\n".join(table_lines)
    assert "test_history_prose.py" not in joined


def test_split_row_drops_outer_pipes_and_strips_cells() -> None:
    assert _split_row("| ZR-1 | `ENFORCED-BY x` | some detail |") == [
        "ZR-1",
        "`ENFORCED-BY x`",
        "some detail",
    ]
