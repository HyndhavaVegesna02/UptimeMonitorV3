"""The sample-mode ingest decorator (dossier §6/§8, STORY-048 D4/D5).

TEMPORARY feature (PO directive, 2026-07-03) — see
`docs/scrum/wiki/sample-mode.md` for the REMOVAL inventory. This whole
module (and its ONE seam line in `composition/run.py`) is deleted, along
with the port/adapter/fake/API feature, when sample-mode is removed.

`SampleModeIngest` is a composition-layer decorator over `SignalIngestPort`
(dossier §6's inbound front door) — the on-demand outage simulator that lets
the PO exercise the real degrade->approve->publish->recover loop against a
healthy real monitor. It never touches `core/services/`: the override wraps
the real `IngestService`, so the core stays pure (hexagonal constraint,
STORY-048 Context).

The flag is read ONCE per `ingest_observations` call — no caching, no TTL,
no background refresh — because each `run_periodic` cycle calls ingest
exactly once (`composition/pull_loop.py::run_periodic`), so this IS the
per-cycle read the story's AC4 requires: a flip between cycles changes the
next cycle's recording with no loop restart.
"""

from __future__ import annotations

from collections.abc import Sequence

from src.core.domain import Health, IngestResult, SignalObservation
from src.core.ports import SignalIngestPort
from src.core.ports.sample_mode_repository import SampleModeRepository

SIMULATED_RAW_REF = "sample-mode:forced-down"
"""The AC5 marker: a `raw_ref` sentinel, deliberately reusing the EXISTING
`SignalObservation.raw_ref` field rather than adding a new domain field/column
(D5) — `raw_ref` is already persisted and round-tripped by
`ObservationRepository`, is `None` on every genuine live HTTP row today, the
core never reads it, and the history API never exposes it, so a simulated row
is mechanically distinguishable (`raw_ref = SIMULATED_RAW_REF`) while nothing
else in the system changes. This keeps the whole feature removable with zero
schema/domain change."""


class SampleModeIngest(SignalIngestPort):
    """Composition-layer decorator: forces every observation to DOWN while
    the persisted sample-mode flag is ON; passes the batch through unchanged
    while it is OFF (dossier §6, §8, STORY-048 D4).
    """

    def __init__(
        self, *, delegate: SignalIngestPort, sample_mode_repo: SampleModeRepository
    ) -> None:
        self._delegate = delegate
        self._sample_mode_repo = sample_mode_repo

    def ingest_observations(self, batch: Sequence[SignalObservation]) -> IngestResult:
        """Read the flag ONCE, then delegate — unchanged if OFF, forced-DOWN
        copies if ON.

        A sample-mode repo read failure PROPAGATES (never swallowed): the
        cycle already depends on the same database, consistent with the
        loop's existing cycle-failure handling.
        """
        enabled = self._sample_mode_repo.is_enabled()

        if not enabled:
            return self._delegate.ingest_observations(batch)

        forced = [
            observation.model_copy(
                update={"health": Health.DOWN, "raw_ref": SIMULATED_RAW_REF}
            )
            for observation in batch
        ]
        return self._delegate.ingest_observations(forced)
