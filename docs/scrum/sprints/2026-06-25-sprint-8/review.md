# Sprint 8 — Review

**Goal:** Zone 4's pure-logic surface closes — anti-flap (stage 3) and the per-component skew flag,
both pure and injectable, no config-loading or proposal-persistence dependency.

**Branch:** `sprint-8` (commits `a601a4b..2035237`) · **Committed:** 6 pts · **Done:** 6 pts
**Capacity:** 6 (velocity 8/6/6/6/5/6/6/6, last-3 mean).

---

## STORY-028 — Core pipeline stage 3: anti-flap (3 pts) — ✅ DONE

**Pipeline:** implementer (Sonnet) → spec **PASS** (Opus) → quality (Opus): 1 MAJOR → **fix loop 1**
(fresh Sonnet) → re-review **APPROVE** (Opus) → DoD gate green.

Built (pure core, `core/services/pipeline.py`): `anti_flap(streak, thresholds) -> AntiFlapOutcome`
— a failing streak maps by length to `major_outage`/`partial_outage`/`degraded` (severity-ordered,
`>=`), a single failure → an internal warning (never published), a sustained `degraded` →
`degraded`, a passing streak `>= recovery` → `operational`, below all → nothing. Thresholds
(`AntiFlapThresholds`) are INJECTED — config loading deferred.

### AC checklist (spec reviewer verified each MET)
- AC1 failing ladder by length vs injected thresholds, boundary-tested ✅ · AC2 internal-warning
  distinct + degraded/recovery/nothing ✅ · AC3 thresholds injected, pure ✅ · AC4 boundary + degenerate
  (at/just-below each threshold, length 0/1, negative) ✅

**Fix loop:** quality caught that `AntiFlapOutcome` could be constructed incoherently
(`proposed_status` set *and* `internal_warning=True`) — the same latent-incoherence pattern STORY-025
enforced on `Verdict`. Fix loop 1 added a `model_validator(mode="after")` + tests; re-review APPROVE.

---

## STORY-026 — Per-component skew flag (3 pts) — ✅ DONE

**Pipeline:** implementer (Sonnet) → spec **PASS** (Opus) → quality (Opus): 1 MAJOR → **fix loop 1**
(fresh Sonnet) → re-review **APPROVE** (Opus) → DoD gate green.

Built (pure core, new `core/services/skew.py`): `skew(feeders) -> SkewResult` — a feeder lagging the
freshest peer watermark by MORE than its own `interval` is flagged (strict `>`, so exactly-at-interval
is not skewed); names the lagging signals. Peers/watermarks/intervals INJECTED; result is its own type
(diverges from completeness). None-watermark feeder → maximally-lagging if peers exist; single feeder /
empty / all-None → no skew, no crash.

### AC checklist (spec reviewer verified each MET)
- AC1 lag > own interval vs MAX peer watermark ✅ · AC2 separate result, diverges from completeness ✅
- AC3 injected peers, pure ✅ · AC4 at-vs-just-over boundary, empty/single/None-watermark degenerate ✅

**Fix loop:** quality caught the *same* coherence gap on `SkewResult` (`skewed` must equal
`bool(lagging_signals)`) — the third value-object-coherence MAJOR in a row (Verdict, AntiFlapOutcome,
SkewResult). Fix loop 1 added the validator + tests + fixed a stale wiki `verified_sha`; re-review APPROVE.

---

## DoD evidence (orchestrator-verified; consolidated DB gate at the final tree)
| Command | Result |
|---|---|
| `pytest` | 241 passed (191 baseline + 28 anti-flap + 22 skew) |
| `lint-imports` | 3 kept, 0 broken |
| `check_fk_direction.py` | 10 FKs, 0 violations |
| `alembic upgrade head` | no-op (pure-core sprint) |

(One environmental hiccup: a leftover `uptime_pg_pytest` docker container held port 55432 and was
removed before the DB-gated runs — no impact on results.)

## Demo
- anti-flap: `pytest backend/tests/test_anti_flap.py` (severity ladder + boundaries + coherence).
- skew: `pytest backend/tests/test_skew.py` (at-vs-just-over + degenerate + coherence).
- All pure-core, in-memory fixtures — no live services.

## Wiki
Compile pass done (blocks review): no stale articles; the Zone 4 article gained anti-flap + skew
Facts (with `skew.py`/`test_skew.py` added to `code_refs` per the sprint-7 agreement); drifted
`file:line` citations across the article were re-aligned to the current code. Links lint clean.

## Carried into Sprint 9
- STORY-024 (decide, stage 4, 3, draft) — depends on the proposal lifecycle (STORY-012).
- STORY-012 (proposal lifecycle, 5, draft) — Zone 5; the natural unblock for decide.
- STORY-027 (lazy-import cleanup, 1, ready).

## PO verdict
- [ ] STORY-028 — accept / reject
- [ ] STORY-026 — accept / reject
