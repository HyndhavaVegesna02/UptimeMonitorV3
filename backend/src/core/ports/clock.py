"""The clock port (dossier §6) — injected time.

`now()` is injected rather than read from the wall clock, so the core's
time-dependent logic is controllable and deterministic in tests. The contract is
that it returns a tz-aware UTC instant.
"""

from abc import ABC, abstractmethod
from datetime import datetime


class ClockPort(ABC):
    """Supplies the current instant to the core (dossier §6).

    Implementations MUST return a tz-aware UTC `datetime`. Injecting the clock is
    what makes time controllable in tests (a fixed fake) while production reads
    the real wall clock.
    """

    @abstractmethod
    def now(self) -> datetime:
        """Return the current instant as a tz-aware UTC `datetime`."""
        raise NotImplementedError
