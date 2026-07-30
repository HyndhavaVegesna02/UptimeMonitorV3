"""Assumed (UNVERIFIED) vendor status codes for the demo engine (STORY-148 AC8, STORY-177).

**Nothing here is a vendor contract.** A real Dynatrace failure code has never
been observed — the trial expired 2026-07-28 before one could be captured — so
every non-healthy `(code, message)` pair this demo engine can build is an
ASSUMPTION. They are collected here, in ONE named place, so nobody mistakes a
demo failure row for something the vendor has confirmed.

**What changed at STORY-177.** This file used to say *"Do NOT use these to add
a failure mapping to `backend/src/`"* and that the pair *"carries no special
acceptance anywhere in `backend/src/`"*. Both statements are now FALSE and have
been removed: STORY-177 deliberately landed `PROVISIONAL_STATUS_MAPPING` in
`adapters/inbound/dynatrace/health_mapping.py`, because the live verification
the old fail-loud-only design deferred to **cannot happen** while the trial is
expired. That was a first-class, reviewed decision — not a side effect of a
demo fixture.

**The dependency direction is fixed** (CLAUDE.md §4): `tools/` may import
`src.*`, never the reverse. So the codes live in `health_mapping.py` and are
DERIVED here, never redeclared. That is what keeps STORY-177 AC2's
single-constant rule true, and what makes STORY-154 (mapping the real codes
once a tenant exists) a one-place change rather than a hunt.

"The failure path is tested" — anywhere this repo makes that claim — means
"tested against an ASSUMED code", never against anything Dynatrace has
confirmed. See `tools/demo_engine/README.md`.
"""

from __future__ import annotations

from src.adapters.inbound.dynatrace.health_mapping import PROVISIONAL_STATUS_MAPPING
from src.core.domain import Health


def _pair_for(health: Health) -> tuple[str, str]:
    """Return the single provisional `(code, message)` pair mapping to `health`.

    Deliberately strict: raises unless the mapping holds EXACTLY one pair for
    `health`. A silent `next()` pick would hide the case where STORY-154 later
    adds a second, real code for the same `Health` — at which point "the
    assumed DOWN pair" stops being a single well-defined thing and this module
    must be revisited rather than quietly choosing one.
    """
    pairs = [
        pair for pair, mapped in PROVISIONAL_STATUS_MAPPING.items() if mapped is health
    ]
    if len(pairs) != 1:
        raise RuntimeError(
            f"expected exactly one provisional pair for {health.name}, found "
            f"{pairs!r} -- PROVISIONAL_STATUS_MAPPING changed shape; revisit "
            "this module (likely STORY-154 landing the real vendor codes)."
        )
    return pairs[0]


ASSUMED_DOWN_CODE, ASSUMED_DOWN_MESSAGE = _pair_for(Health.DOWN)
ASSUMED_DEGRADED_CODE, ASSUMED_DEGRADED_MESSAGE = _pair_for(Health.DEGRADED)

#: A pair deliberately **NOT** in `PROVISIONAL_STATUS_MAPPING`, used by the
#: poison-row scenario (STORY-191 AC5) to prove STORY-190's quarantine on a real
#: run: `map_synthetic_status` must RAISE on it, the row must be quarantined,
#: and the rest of the batch must still ingest.
#:
#: Its entire value is being UNMAPPED — a property of another module, which
#: someone could silently destroy by adding "999" to the provisional mapping.
#: The poison scenario would then quietly stop being poison and STORY-191 AC5
#: would keep passing while testing nothing. That invariant is therefore PINNED
#: BY A TEST, not merely asserted in this comment:
#: `test_assumed_failure_codes.py::test_poison_pair_is_not_in_the_provisional_mapping`.
UNMAPPED_POISON_CODE = "999"
UNMAPPED_POISON_MESSAGE = "UNMAPPED_POISON"
