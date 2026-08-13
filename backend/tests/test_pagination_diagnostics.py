"""Unit tests for the shared pagination-diagnostic spy (STORY-213 AC1/AC4).

Pure Python -- no DynamoDB required. `PaginationSpy` wraps a table-like
object's `query`/`scan` method and records every raw response so a
pagination test's assertion message can report the observed page count, the
ids actually returned, and whether a `LastEvaluatedKey` was still present
when the loop exited -- instead of a bare set-equality mismatch, which reads
identically for a real regression and a one-off flake (the STORY-213
defect: `test_dynamo_component_repository_list_components_paginates` failed
once in eleven full-suite runs with a message indistinguishable from
"pagination is broken").
"""

from __future__ import annotations

from tests.pagination_diagnostics import PaginationSpy


class _FakeTable:
    """A table stand-in whose `query` returns a scripted sequence of
    DynamoDB-shaped responses, one per call."""

    def __init__(self, responses: list[dict]) -> None:
        self._responses = list(responses)
        self.call_count = 0

    def query(self, **kwargs):
        response = self._responses[self.call_count]
        self.call_count += 1
        return response


def test_pagination_spy_records_every_response_and_restores_the_method():
    table = _FakeTable(
        [
            {"Items": [{"id": "a"}], "LastEvaluatedKey": {"pk": "x"}},
            {"Items": [{"id": "b"}]},
            {"Items": [{"id": "c"}]},
        ]
    )
    with PaginationSpy(table) as spy:
        table.query()
        table.query()

    assert spy.page_count == 2
    assert spy.last_evaluated_key_present is False

    # restored on __exit__: a further call is NOT recorded by the spy.
    table.query()
    assert spy.page_count == 2


def test_pagination_spy_last_evaluated_key_present_true_when_last_page_carries_one():
    table = _FakeTable([{"Items": [], "LastEvaluatedKey": {"pk": "still-more"}}])
    with PaginationSpy(table) as spy:
        table.query()
    assert spy.last_evaluated_key_present is True


def test_pagination_spy_last_evaluated_key_present_none_when_nothing_recorded():
    table = _FakeTable([])
    with PaginationSpy(table) as spy:
        pass
    assert spy.page_count == 0
    assert spy.last_evaluated_key_present is None


def test_pagination_spy_diagnostic_reports_page_count_ids_missing_extra_and_lek():
    table = _FakeTable([{"Items": [{"id": "a"}, {"id": "b"}]}])
    with PaginationSpy(table) as spy:
        table.query()

    message = spy.diagnostic(expected={"a", "b", "c"}, actual={"a", "b"})

    assert "1 page(s)" in message
    assert "'a'" in message and "'b'" in message
    assert "missing=['c']" in message
    assert "extra=[]" in message
    assert "LastEvaluatedKey present when loop exited=False" in message


def test_pagination_spy_summary_reports_page_count_and_lek_without_ids():
    table = _FakeTable([{"Items": [{"id": "a"}], "LastEvaluatedKey": {"pk": "x"}}])
    with PaginationSpy(table) as spy:
        table.query()

    summary = spy.summary()

    assert "1 page(s)" in summary
    assert "LastEvaluatedKey present when loop exited=True" in summary
