"""The sample-mode repository port (dossier §6/§17, STORY-048 D2).

TEMPORARY feature (PO directive, 2026-07-03) — see
`docs/scrum/wiki/sample-mode.md` for the REMOVAL inventory. This whole
module is deleted, along with its adapter/fake, when sample-mode is removed;
no other port/core module imports it.

`SampleModeRepository` persists ONE global boolean: whether the live loop is
currently forcing every incoming observation to `Health.DOWN` (the sample
switch, dossier §8's ingest edge). No new domain type — the payload is a
bare bool and there is no not-found case to express.
"""

from abc import ABC, abstractmethod


class SampleModeRepository(ABC):
    """Port interface for the persisted, process-crossing sample-mode flag."""

    @abstractmethod
    def is_enabled(self) -> bool:
        """Return the current flag state.

        Returns `False` when the flag has never been set — the PO's
        default-OFF (2026-07-03) lives HERE, not in a seed. Never raises.
        """
        raise NotImplementedError

    @abstractmethod
    def set_enabled(self, enabled: bool) -> None:
        """Set the flag state (idempotent upsert of the single row).

        Setting the current value again succeeds silently — there is no
        conflict/precondition to violate on a single-row upsert.
        """
        raise NotImplementedError
