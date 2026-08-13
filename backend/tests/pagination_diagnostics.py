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
output alone, whether they are looking at an early-stop flake or a real
regression.

Both shapes are CONFIRMED (not merely plausible) by STORY-213's own AC1/AC2
evidence, and they are OPPOSITE signatures: the hypothesised DynamoDB Local
flake (a genuinely absent `LastEvaluatedKey` handed to an unmodified,
correct loop) reads `LastEvaluatedKey present when loop exited=False` --
the server said "no more" and the loop correctly believed it. Mutating away
the loop itself (STORY-199's own regression, still honoring `Limit`)
instead reads `... =True` -- the server correctly says more rows exist and
the (broken) code never asks for them. `False` points upstream, at
DynamoDB Local under-reporting; `True` points at this repository's own loop.

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

    def diagnostic(self, expected: Iterable[Any], actual: Iterable[Any]) -> str:
        """Render observed page count, actual ids, the missing/extra sets
        against `expected`, and whether a LastEvaluatedKey was present when
        the loop exited -- the two shapes below are CONFIRMED, not merely
        plausible (STORY-213 AC1/AC2 evidence): forcing DynamoDB Local's
        hypothesised flake (a genuinely absent LastEvaluatedKey handed to an
        UNMODIFIED, correct loop) reads `1 page(s) read; ... present when
        loop exited=False` with a non-empty `missing`
        (test_dynamo_component_repository_list_components_paginates_diagnostic_message_on_forced_truncation);
        mutating away the loop itself (STORY-199's own regression, still
        honoring `Limit`) instead reads `... present when loop exited=True`
        with the SAME non-empty `missing` -- the server correctly says more
        rows exist and the (broken) code ignores it. A `missing` set with
        LEK=False points upstream (DynamoDB Local under-reported); LEK=True
        points at this repository's own loop."""
        expected_set = set(expected)
        actual_set = set(actual)
        missing = sorted(expected_set - actual_set)
        extra = sorted(actual_set - expected_set)
        return (
            f"pagination diagnostic: {self.summary()}; "
            f"ids returned={sorted(actual_set)}; missing={missing}; extra={extra}"
        )
