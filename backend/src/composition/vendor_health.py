"""Live vendor-id drift health check (dossier §8, STORY-070, composition zone).

The Sprint 38 review found a configured Dynatrace monitor `native_id` had been
silently recreated in Dynatrace (a new id issued for the same demo monitor);
the pull loop kept polling the STALE id every cycle -- the query was well
formed and Dynatrace answered HTTP 200 -- but the id matched no rows, so the
loop ingested nothing for 30 days without ever raising or logging an error: a
"trusted-and-wrong" no-data pipeline (fixed by hotfix ``79bfbb3``; see the
2026-07-08 sprint-38 retro working agreement).

``check_vendor_id_health`` closes that gap: at live-loop startup, it runs one
bounded DQL count query per configured signal through the SAME injected
``Executor`` seam ``run_cycle``/``fetch_observations`` use (dossier §8), and
logs a PROMINENT WARNING naming any monitor id that returned zero executions
in the window. This is a **loud WARNING, not fail-fast** (decided sprint-41
planning, PO 2026-07-08): a dead/misconfigured monitor id must surface
immediately, but must never block the live loop from starting, and a probe
error for one signal must never stop the others from being checked. Tests
inject a fake executor -- no live Dynatrace call is ever made here (working
agreement: pure core, mockable edges). This module stays vendor-adjacent
composition/adapter-facing code, never imported by ``core/``.

The DQL this module probes with is built by
``adapters/inbound/dynatrace/query.py::build_vendor_health_dql`` (STORY-204,
ZR-8 finding 2). Before that story this module re-implemented that builder
itself, interpolating ``native_id`` with none of the adapter's breaking-
character validation -- a misconfigured ``native_id`` raised loudly on the
ingest path but silently built a malformed query here, on the probe that
runs FIRST at loop startup. This module now calls the adapter's builder
instead of re-deriving it, so both paths reject the same way.
"""

from __future__ import annotations

import logging

from src.adapters.inbound.dynatrace.query import (
    _HEALTH_CHECK_WINDOW,
    Executor,
    build_vendor_health_dql,
)
from src.composition.config import Config

logger = logging.getLogger(__name__)


def _extract_count(rows: list[dict]) -> int:
    """Extract the `summarize count()` value from the executor's row list.

    Returns 0 when the row list is empty (Grail's `summarize` still emits one
    row for a matched-nothing query, but a fake/real executor may reasonably
    return `[]` instead) OR when the single row's count field is 0 or
    unparseable -- both mean "no live executions in the window" (STORY-070
    AC1). Grail's `summarize count()` names the result column `count()`
    (a literal Grail column name); `count` is also accepted for executors
    that pre-friendly-name the field.
    """
    if not rows:
        return 0
    row = rows[0]
    for key in ("count()", "count"):
        if key in row:
            try:
                return int(row[key])
            except (TypeError, ValueError):
                return 0
    return 0


def check_vendor_id_health(*, config: Config, executor: Executor) -> None:
    """Probe every configured monitor `native_id` for live drift (STORY-070).

    For EACH signal across every loaded app config, runs
    `adapters/inbound/dynatrace/query.py::build_vendor_health_dql` through the
    injected `Executor` seam. A 0-row/0-count result logs a PROMINENT WARNING
    naming the monitor id and signal key -- the drift this story exists to
    catch. A healthy id logs nothing (kept quiet; the loud signal is reserved
    for the failure case, AC1).

    NOT fail-fast for the EXECUTOR: a probe that raises (HTTP failure,
    malformed response, vendor timeout) is caught and logged as its own
    WARNING, but never re-raised -- one dead/unreachable monitor id must not
    block every other signal's probe, and must never prevent the live loop
    itself from starting (decided sprint-41 planning). Call this once, early,
    at live-loop startup (`composition/run.py::main`), before
    `build_live_loop`/`run_periodic` ever run.

    IS fail-fast for a misconfigured `native_id`: `build_vendor_health_dql`
    raises `InvalidNativeIdError` for a DQL-breaking character BEFORE the
    executor is ever called, and that raise is deliberately outside the
    try/except below, so it propagates out of this function identically to
    the ingest path's `build_dql_query` (STORY-204 AC1) -- a misconfigured id
    is a config error, not a transient probe failure.
    """
    for app in config.apps:
        for signal in app.signals:
            query = build_vendor_health_dql(native_id=signal.native_id)
            try:
                rows = executor(query)
            except Exception as exc:
                logger.warning(
                    "Vendor-id health probe FAILED for signal_key=%r "
                    "native_id=%r: %s. Unable to determine whether this "
                    "monitor id is live -- investigate manually.",
                    signal.signal_key,
                    signal.native_id,
                    exc,
                )
                continue

            count = _extract_count(rows)
            if count == 0:
                logger.warning(
                    "VENDOR-ID DRIFT SUSPECTED: configured monitor "
                    "native_id=%r (signal_key=%r) returned 0 executions in "
                    "the last %s. This monitor id may have been recreated "
                    "or deleted in Dynatrace -- ingestion for this signal is "
                    "silently stalled. See dossier §8 / Sprint 38 retro / "
                    "hotfix 79bfbb3.",
                    signal.native_id,
                    signal.signal_key,
                    _HEALTH_CHECK_WINDOW,
                )
            else:
                logger.info(
                    "Vendor-id health OK for signal_key=%r native_id=%r "
                    "(%d executions in last %s).",
                    signal.signal_key,
                    signal.native_id,
                    count,
                    _HEALTH_CHECK_WINDOW,
                )
