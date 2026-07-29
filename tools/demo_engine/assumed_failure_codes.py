"""Assumed (UNVERIFIED) vendor failure codes for the demo engine (STORY-148 AC8).

`map_synthetic_status` (`adapters/inbound/dynatrace/health_mapping.py:54-70`)
maps ONLY `code == "0"` / `message == "HEALTHY"` to `Health.UP` and RAISES on
every other value — deliberately: a real failure code has never been
observed (the Dynatrace trial expired before one could be captured; memory:
`dynatrace-trial-expired`), and that module's own docstring states that
inventing one "would silently mis-map (or mask) the real failure value
during that verification, so it is deliberately NOT done".

Any non-healthy `(code, message)` pair this demo engine can build is
therefore an ASSUMPTION, not a verified fact — collected here, in ONE named
place, so nobody mistakes a demo failure row for a confirmed vendor
contract.

Do NOT use these to add a failure mapping to `backend/src/`; that is a
separate, first-class, reviewed decision (STORY-177), not a side effect of a
demo fixture (STORY-148 AC9's no-`backend/src/`-changes rule is deliberate).

"The failure path is tested" — anywhere this repo makes that claim about the
demo engine — means "tested against an ASSUMED code", never against anything
Dynatrace has confirmed. See `tools/demo_engine/README.md`.
"""

from __future__ import annotations

#: UNVERIFIED pending Dynatrace trial renewal (STORY-154). Chosen only
#: because it reads plausibly next to the one CONFIRMED pair ("0"/"HEALTHY");
#: no live signal has ever produced it, and `map_synthetic_status` raises
#: `UnknownVendorStatusError` on it exactly like it would on anything else
#: unrecognized — this pair carries no special acceptance anywhere in
#: `backend/src/`.
ASSUMED_DOWN_CODE = "1"
ASSUMED_DOWN_MESSAGE = "UNHEALTHY"
