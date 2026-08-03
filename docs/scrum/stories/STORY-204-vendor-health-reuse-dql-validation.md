---
id: STORY-204
title: Reuse the adapter's DQL builder validation inside composition/vendor_health.py (GAP-2)
type: chore
points: 2
status: ready
filed: 2026-07-31
refined: 2026-08-03
sprint: 68
---

## Context

`ZR-8` Finding 2, first reported as `GAP-2` in
`docs/scrum/sprints/2026-07-31-sprint-66/audit-api-composition-tools.md` §4.

`backend/src/composition/vendor_health.py:40-53` (`build_vendor_health_query`) interpolates a
`native_id` into a DQL string literal **without** the breaking-character validation the real builder
performs. `backend/src/adapters/inbound/dynatrace/query.py` declares `_DQL_BREAKING_CHARS`
(`"`, `\`, `\n`, `\r`) at `:37-39` and raises `InvalidNativeIdError` by name at `:79-82`. So the same
trusted-but-possibly-misconfigured value raises loudly on the ingest path and **silently builds a
malformed query** on the startup probe path — and the probe runs FIRST, at loop startup
(`vendor_health.py::check_vendor_id_health`).

Verified at HEAD 2026-08-03: both citations resolve; `_DQL_BREAKING_CHARS` is declared once, in
`query.py`, and `vendor_health.py` neither imports nor re-declares it.

No live-observed vendor error has ever exercised this path (CLAUDE.md's "two things to know"), which
is why this is a chore, not a defect.

## The design decision, made at refinement (not left to the implementer)

The audit deliberately did not prescribe a fix. Two shapes were available:

- **(a) Export a validator** from `query.py` that both builders call, leaving DQL string-building in
  composition.
- **(b) Move the query builder into the adapter** — `build_vendor_health_dql` lives in
  `adapters/inbound/dynatrace/query.py`; `vendor_health.py` calls it. — **CHOSEN.**

Reasoning: `ZR-8`'s statement is *"vendor query-construction logic lives in exactly ONE adapter;
another zone calls that adapter rather than re-implementing it."* Option (a) fixes the validation
symptom while leaving composition building DQL — which is the violation `ZR-8` actually names. (b)
also makes re-declaring `_DQL_BREAKING_CHARS` structurally impossible rather than merely
discouraged. The bounded-window constant `_HEALTH_CHECK_WINDOW = "2h"` moves with the builder it
belongs to.

**Ordering consequence, recorded because it bites another story this sprint:**
`tools/demo_engine/store.py:17-19` cites `composition/vendor_health.py:37` by `file:line` in its own
docstring, and STORY-203 AC4 adjudicates that exact citation. This story relocates the line.
**STORY-204 runs BEFORE STORY-203** so 203 adjudicates against a line that exists.

## Acceptance Criteria

- [ ] **AC1 — the two paths agree.** For each of the four `_DQL_BREAKING_CHARS`, a `native_id`
      containing it raises `InvalidNativeIdError` from the vendor-health probe path, identically to
      the ingest path. One parametrised test over all four — not one character sampled.
- [ ] **AC2 — RED first (sprint constraint C2).** That test is written and **shown failing** against
      pre-fix HEAD (the probe returns a malformed string instead of raising). Record the failing
      output, not a description of it.
- [ ] **AC3 — one declaration (a REGRESSION CHECK, not evidence).** After the change,
      `grep -rn "_DQL_BREAKING_CHARS" backend/` returns hits from exactly one module.
      *Flagged vacuous at plan verification: this already passes at HEAD — `query.py:38` and `:79`
      are the only hits, as this story's own Context says. It guards against the fix introducing a
      second declaration; it is not proof the story did anything.* `build_dql_query`'s behaviour,
      error type and error message are unchanged — proven by its **ingest** tests passing without
      modification. **Say plainly which OTHER tests must change:** `test_server.py:27`,
      `test_vendor_health_query.py:23-26` and `test_vendor_health.py:21` import
      `build_vendor_health_query`/`_HEALTH_CHECK_WINDOW` from `src.composition.vendor_health` and
      **will** need updating. Leaving a re-export shim in `vendor_health.py` so those imports keep
      working is **not** an acceptable way to satisfy AC4 — the symbol moves, callers follow.
- [ ] **AC4 — the builder moved, not just the validator.** `composition/vendor_health.py` contains no
      DQL string construction: no `fetch `, `| filter `, or `| summarize ` literal. Assert it in a
      test; do not eyeball it.
- [ ] **AC5 — the boundary still holds (a REGRESSION CHECK, not evidence).** The import-boundary DoD
      command exits 0. *Flagged vacuous at plan verification: composition already imports
      `src.adapters.inbound.dynatrace.query` (`vendor_health.py:28`, `pull_loop.py:46`) and the
      command is green at baseline.* Run it anyway; do not reason about it.
- [ ] **AC6 — EVERY citation that moved is repointed, from a re-derived set — not just `store.py`.**
      Grep for references to the relocated symbols and fix all of them in the SAME commit. The set
      found at plan verification, to be re-derived not copied: `tools/demo_engine/store.py:18`;
      `tools/demo_engine/query_grammar.py:10-11` and `:7` (the latter cites `query.py:85-97`, itself
      already imprecise — the clause block is `:87-101`, and this story inserts code above it);
      `backend/tests/demo_engine/test_vendor_health_query.py:3,8`;
      `tools/demo_loop_gate/fleet_coverage.py:8,24`;
      `tools/demo_loop_gate/backfill_reality_gate.py:9,11`;
      `backend/tests/demo_loop_gate/test_backfill_discrimination.py:4,6`;
      `test_fleet_coverage.py:8`; `docs/scrum/wiki/demo-engine.md:103,118`.
      A stale `file:line` written by the commit that invalidated it is exactly the defect class
      behind ten of sprint 67's eleven blocking findings.
- [ ] **AC6b — do not break the ZR-3 guard from inside this story.** `_ADJUDICATED` holds
      `("tools/demo_engine/store.py", 22)`. This story rewrites `store.py`'s `:18-21` comment block —
      its justification ("borrowed from composition") stops being true — and a one-line change moves
      `VENDOR_HEALTH_WINDOW` off `:22`, taking `test_zr3_adjudications_are_still_current` RED inside
      a story that otherwise never touches ZR-3. Re-key that entry if `store.py`'s line count
      changes, preserving its reason text.
- [ ] **AC7b — the catalogue moves in the SAME commit (constraint C3).** *Added at plan
      verification: this story had no `zone-rules.md` AC at all, while the plan claimed every story
      here carried one.* This commit falsifies four places, and `zone-rules.md` carries both edited
      files in its `code_refs`, so the sweep marks it stale the moment this lands:
      `zone-rules.md:667-677` (ZR-8 Finding 2's body — `vendor_health.py:40-53`, `:96-133`,
      `query.py:52-102`, `query.py:41-49,79-82`); `:695-696` (the Coverage verdict's "a parallel
      assertion that `composition/vendor_health.py` calls … `query.py`'s validation");
      `:735` (the ZR-8 row, "Two live violations"); and `:746` ("ZR-8's two violations remain live").
      Update all four and clear the wiki sweep before the DoD gate. Do not stamp `verified_sha` on
      prose that was not re-read.
- [ ] **AC7 — the demo engine still answers the probe.** `tools/demo_engine` parses the
      vendor-health DQL grammar (`demo_engine/query_grammar.py::VendorHealthQuery`). Prove the
      relocated builder's output still parses — the wire contract is the reason `store.py` holds its
      own window constant at all, and breaking it silently would disable the loop's startup probe.

## Not in scope

Escaping or sanitizing `native_id` (STORY-021 decided: reject loudly, never escape — trusted vendor
config, not user input). Changing the `"2h"` window value. `ZR-8`'s `seed_dynamo` finding
(STORY-205). The `store.py` VALUE duplication itself (STORY-203 AC4).
