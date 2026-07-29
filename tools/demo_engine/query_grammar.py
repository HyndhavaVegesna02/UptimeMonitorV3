"""Parses the two DQL query strings the production code actually emits
(STORY-148 AC3-AC5).

Mirrors exactly two shapes:

- the ingest grammar, `build_dql_query`
  (`adapters/inbound/dynatrace/query.py:85-97`) — always scoped to a monitor
  id and `event.type`, plus an optional `timestamp >= toTimestamp(...)` lower
  bound when a watermark exists;
- the vendor-health grammar, `build_vendor_health_query`
  (`composition/vendor_health.py:40-53`) — a `summarize count()` existence
  probe scoped to a monitor id, with a `from:now()-2h` window.

This module recognizes exactly these two shapes and raises on anything else,
so a future third grammar the engine doesn't understand surfaces loudly
instead of silently returning nothing (mirroring the fail-loud style of the
production code it stands in for).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

from src.adapters.inbound.dynatrace._assembly import parse_ns_timestamp

_MONITOR_ID_RE = re.compile(r'dt\.synthetic\.monitor\.id\s*==\s*"([^"]*)"')
_EVENT_TYPE_RE = re.compile(r'event\.type\s*==\s*"([^"]*)"')
_WATERMARK_RE = re.compile(r'timestamp\s*>=\s*toTimestamp\("([^"]*)"\)')
_SUMMARIZE_COUNT_RE = re.compile(r"summarize\s+count\(\)")


class UnrecognizedDqlQueryError(ValueError):
    """Raised when a query string matches neither grammar this engine answers."""


@dataclass(frozen=True)
class IngestQuery:
    """A parsed ingest-grammar query (`build_dql_query`)."""

    monitor_id: str
    event_type: str
    since: datetime | None


@dataclass(frozen=True)
class VendorHealthQuery:
    """A parsed vendor-health-grammar query (`build_vendor_health_query`)."""

    monitor_id: str


def parse_watermark_bound(value: str) -> datetime:
    """Parse a `toTimestamp("...")` bound at 0-, 6- or 9-digit fractional
    precision (STORY-148 AC4).

    Reuses the REAL production timestamp parser
    (`_assembly.py::parse_ns_timestamp`) rather than reimplementing it, so
    the watermark bound and every row's own `timestamp` are parsed by the
    exact same logic and can be compared as `datetime` objects — never as
    strings (a 6-digit bound sorts lexicographically BEFORE a 9-digit row at
    the same instant, which is the STORY-051 stall reproduced inside this
    engine if this parsing is skipped).
    """
    return parse_ns_timestamp(value)


def parse_query(query: str) -> IngestQuery | VendorHealthQuery:
    """Parse one DQL query string into the grammar it matches.

    Raises `UnrecognizedDqlQueryError` if it matches neither of the two
    grammars the production code emits.
    """
    if _SUMMARIZE_COUNT_RE.search(query):
        monitor_match = _MONITOR_ID_RE.search(query)
        if monitor_match is None:
            raise UnrecognizedDqlQueryError(
                f"vendor-health query missing monitor id filter: {query!r}"
            )
        return VendorHealthQuery(monitor_id=monitor_match.group(1))

    monitor_match = _MONITOR_ID_RE.search(query)
    event_match = _EVENT_TYPE_RE.search(query)
    if monitor_match is None or event_match is None:
        raise UnrecognizedDqlQueryError(
            f"query matches neither the ingest nor the vendor-health grammar: {query!r}"
        )

    watermark_match = _WATERMARK_RE.search(query)
    since = (
        parse_watermark_bound(watermark_match.group(1))
        if watermark_match is not None
        else None
    )
    return IngestQuery(
        monitor_id=monitor_match.group(1),
        event_type=event_match.group(1),
        since=since,
    )
