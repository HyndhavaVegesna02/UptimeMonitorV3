---
id: STORY-202
title: env_matrix.py must import ALL SEVEN child env-var NAMES from settings.py, not re-declare them
type: defect
points: 1
status: draft
filed: 2026-07-31
---

> **DRAFT — needs a refinement pass before it may enter a sprint** (Definition of Ready: approved AC
> + estimate + no open questions). The estimate below is the audit's or the orchestrator's first cut,
> not a refined one.

## Context

Filed during sprint 66, the boundary/code-discipline audit. **Authoritative detail:**
`docs/scrum/sprints/2026-07-31-sprint-66/audit-api-composition-tools.md` §6 (STORY-196 audit) — it carries the three testable AC verbatim.

This file exists so the story is visible in `docs/scrum/stories/` alongside every other story —
it was originally landed as a `.scrum/backlog.yaml` entry only, which made it findable at planning
but invisible here.

## The finding, as recorded when it was filed

```
written -- the report section is the source (audit-api-composition-tools.md
section 6), and it carries three testable AC ready to lift.
*** THIS ONE IS CREDENTIAL-SAFETY-RELEVANT, which is why a 1-pointer is filed
separately from the MINOR batch. *** tools/demo_loop_gate/env_matrix.py:75 and
:77 hardcode the literal env-var KEY NAMES "STATUSPAGE_PAGE_ID" /
"STATUSPAGE_API_KEY", duplicating STATUSPAGE_PAGE_ID_VAR /
STATUSPAGE_API_KEY_VAR at backend/src/composition/settings.py:49-50.
CONSEQUENCE OF A RENAME ON THE settings.py SIDE: the harness's fake-credential
injection into the credentialed API subprocess silently stops matching, and
composition/asgi.py's own load_dotenv() fills the gap with the REAL repo-root
.env Statuspage credentials instead. `decide` publishes recoveries with NO
human gate and sprint 65 proved that fires, so this is the guard behind the
guard. NOTE the real publish guard remains config-only (config/demo declares
no statuspage_component_id); fake credentials are defence in depth -- but this
defect degrades that defence silently, which is the worst way to lose it.
AC2 is the good one: pin the test's expectation to the IMPORTED symbols, so a
future rename moves the test's expectation with it instead of passing a
now-wrong key.
*** SCOPE WIDENED 2026-07-31 at the STORY-196 fix round, and the severity
ORDER CHANGED. *** The original entry covered only the 2 Statuspage credential
names. The quality review pointed out that the SAME rename-drift mechanism
applies to the five sitting five lines above them -- env_matrix.py:64-68
CONFIG_DIR, AWS_REGION, DYNAMO_ENDPOINT_URL, DYNAMO_OBSERVATIONS_TABLE,
DYNAMO_CONTROL_TABLE. They escaped the ZR-3 sweep only because settings.py:32-38
reads those names as FUNCTION-BODY literals rather than module constants -- a
formatting accident on the src side, NOT a difference in risk.
CONFIG_DIR IS NOW GRADED THE MOST SEVERE OF THE SEVEN, above the credential
pair: the fake credentials are only defence in depth, whereas CONFIG_DIR is
what selects config/demo and therefore what makes statuspage_mapping() empty --
it IS the publish guard. Story is now 7 names, not 2.
```

## Acceptance Criteria

- [ ] To be lifted from the source above and approved at refinement. The source already states
      testable AC for this story; refinement's job is to confirm they are still accurate against the
      code, not to invent new ones.

## Open Questions

Refinement must confirm the estimate (1 point) and check
every `file:line` citation still resolves — this sprint repeatedly found citations that had drifted.
