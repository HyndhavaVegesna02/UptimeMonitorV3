"""Shared pagination diagnostic helper (STORY-213).

`test_dynamo_component_repository_list_components_paginates` (one of
STORY-199's five AC2 proofs) failed once in eleven full-suite runs with:

    assert {'comp-page-0', 'comp-page-1'} == {10 ids}

-- i.e. `list_components` returned page 1 and stopped. That message is
indistinguishable from a REAL regression of the pagination loop STORY-199
had just fixed, at the exact call site the failure hit. The fix here is not
to the pagination loop (mutation-verified correct, STORY-197's ZR-7 guard
independently confirms all six compliant call sites) but to the MESSAGE: a
reader hitting this failure should be able to tell, from the assertion
output alone, whether they are looking at an early-stop flake (a
`LastEvaluatedKey` was still present when the loop exited -- more pages were
claimed available but the loop stopped anyway) or a real regression (no
`LastEvaluatedKey` ever appears, or the loop logic itself is wrong).

`PaginationSpy` wraps a boto3 `Table`'s `query`/`scan` method and records
every raw response so `.diagnostic()`/`.summary()` can render that answer
without re-instrumenting the failure by hand. It is deliberately dumb: it
does not interpret the responses beyond counting pages and checking for
`LastEvaluatedKey` on the last one recorded -- the interpretation belongs to
the reader of the assertion message, not to this helper.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any


class PaginationSpy:
    """Records every response from one table method call (default `query`)
    for later diagnostic rendering. Restores the original method on
    `__exit__`, including when the wrapped call raises."""

    def __init__(self, table: Any, method_name: str = "query") -> None:
        self._table = table
        self._method_name = method_name
        self._original = getattr(table, method_name)
        self.responses: list[dict] = []

    def __enter__(self) -> "PaginationSpy":
        original = self._original
        responses = self.responses

        def _spied(*args: Any, **kwargs: Any) -> Any:
            response = original(*args, **kwargs)
            responses.append(response)
            return response

        setattr(self._table, self._method_name, _spied)
        return self

    def __exit__(self, *exc_info: Any) -> None:
        setattr(self._table, self._method_name, self._original)

    @property
    def page_count(self) -> int:
        """How many `query`/`scan` calls were recorded."""
        return len(self.responses)

    @property
    def last_evaluated_key_present(self) -> bool | None:
        """Whether the LAST recorded response carried a `LastEvaluatedKey`
        -- i.e. whether the loop stopped while DynamoDB still claimed more
        pages were available. `None` if no call was recorded at all (the
        loop never ran, e.g. an empty table)."""
        if not self.responses:
            return None
        return bool(self.responses[-1].get("LastEvaluatedKey"))

    def summary(self) -> str:
        """Page count + LastEvaluatedKey presence only -- for call sites
        (e.g. a boolean short-circuit like `is_under_maintenance`) that have
        no "ids returned" to report."""
        return (
            f"{self.page_count} page(s) read; LastEvaluatedKey present when "
            f"loop exited={self.last_evaluated_key_present}"
        )

    def diagnostic(self, expected: Iterable[str], actual: Iterable[str]) -> str:
        """Render observed page count, actual ids, the missing/extra sets
        against `expected`, and whether a LastEvaluatedKey was present when
        the loop exited. An early-stop flake shows up as LEK-present=True
        with a non-empty `missing`; a real regression more plausibly shows
        LEK-present=False from the first page, or a `missing` set that
        doesn't shrink between runs."""
        expected_set = set(expected)
        actual_set = set(actual)
        missing = sorted(expected_set - actual_set)
        extra = sorted(actual_set - expected_set)
        return (
            f"pagination diagnostic: {self.summary()}; "
            f"ids returned={sorted(actual_set)}; missing={missing}; extra={extra}"
        )
