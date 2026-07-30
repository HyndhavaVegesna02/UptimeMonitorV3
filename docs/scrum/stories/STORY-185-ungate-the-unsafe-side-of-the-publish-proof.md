---
id: STORY-185
title: Un-gate the unsafe side of the publish-safety proof from Docker
type: chore
points: 1
status: ready
refined: 2026-07-30   # PO-approved `ready` at the sprint-64 refinement ("approve all five"); the
                      # frontmatter was never updated to match, which the sprint-65 plan-verifier
                      # caught as a Definition-of-Ready failure. Recorded here, not re-approved.
---

## Context

STORY-176's publish guard is proven by a **pair** of tests in
`backend/tests/test_demo_fleet_config.py`:

| Side | Test | Asserts |
|---|---|---|
| Safe | `test_create_app_with_demo_config_dir_yields_empty_mapping_and_logging_delegate` | `CONFIG_DIR=config/demo` → `statuspage_mapping() == {}` and a `LoggingPublisher` delegate, **with real-looking credentials set** |
| Unsafe | `test_create_app_with_live_config_dir_and_real_looking_creds_selects_real_publisher_type` (`:179-181`) | `CONFIG_DIR=config/apps` → non-empty mapping and a real `StatuspagePublisher` **type** (no network call) |

The pair is the point. A guard test whose check cannot come back "unsafe" is not evidence — that is
working agreement A1, and sprint 63's retro sharpens it (proposed A3): when a two-sided proof reports
the same outcome on both sides, that is **inverted** evidence, not weak evidence.

STORY-176's fix round un-gated the **safe** side from Docker: it takes no `dynamo_local` fixture and
sets `DYNAMO_ENDPOINT_URL` to a literal unreachable endpoint (`http://127.0.0.1:1`), which works
because `composition/dynamo.py:10-22`'s `make_dynamo_resource` is a bare lazy `boto3.resource(...)`
that performs no I/O at construction. Verified: it passes with `DYNAMO_ENDPOINT_URL` **unset** in
0.88 s — and that runtime is itself the proof that nothing dialled out.

The **unsafe** side was left on `dynamo_local`. So on a machine without Docker and without
`DYNAMO_ENDPOINT_URL`, the safe half runs and the unsafe half **skips**, and the suite reports green
for a proof that has quietly become one-sided. Nothing in the output says so.

**This did not affect sprint 63's evidence.** The orchestrator's out-of-test reality-gate harness
proved the unsafe side with no Docker at all — a throwaway config declaring
`statuspage_component_id: FAKE-VENDOR-COMPONENT-ID` yielded a non-empty mapping and the chain
`StatusWritebackPublisher → BestEffortPublisher → RecordingPublisher → StatuspagePublisher`, recorded
on the sprint-63 board under `story_gates/STORY-176 reality_gate.discrimination_proof`. But that
harness lives in a scratchpad, not in the suite, so the repo's own permanent proof is the test pair.

## Description

Apply the same unreachable-endpoint treatment to the unsafe-side test so the pair stays a pair
without Docker. If it genuinely needs a real table for some reason the safe side does not, that
asymmetry is the finding — say so in the story rather than working around it.

Tests only. No file under `backend/src/` changes; the demo config is not touched.

## Acceptance Criteria

- [ ] **AC1 (the unsafe side runs without Docker)** — `test_create_app_with_live_config_dir_...`
      passes with `DYNAMO_ENDPOINT_URL` unset and no Docker-backed fixture, exactly as the safe side
      now does. Evidence: the test run recorded with the variable unset, showing **passed**, not
      **skipped**.
- [ ] **AC2 (still no network call, still type-only)** — The test continues to assert the publisher's
      TYPE and makes no Statuspage call. The real `config/apps` component id
      (`config/apps/httpcheck.yaml:8`) is read but never PATCHed. Nothing in this story may start a
      loop or a server.
- [ ] **AC3 (the pair is visibly a pair)** — Both tests state in a comment or docstring that they are
      two sides of one proof and that neither is meaningful alone, so a future reader cannot delete
      or gate one without noticing.
- [ ] **AC4 (no silent skip anywhere in the pair)** — Neither test is decorated with, or transitively
      depends on, a fixture that can skip. A run with Docker stopped is the evidence.
- [ ] **AC5** — The DoD gate commands the diff can affect exit 0; the test count is unchanged (this
      story edits tests, it does not add behaviour).

## Open Questions

None.

## History

- 2026-07-30: filed from the STORY-176 fix-round quality re-review (PO-authorised after sprint-63
  acceptance). The reviewer confirmed the residual and judged the wiki's honest disclosure of it "the
  right call — follow-up, not a defect in the round". Estimated 1 point.
