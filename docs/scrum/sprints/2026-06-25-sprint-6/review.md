# Sprint 6 — Review

**Goal:** Zone 4 opens — the first two pure pipeline stages (collapse + streak) land as
provider-blind core logic, and the three carried 1-pt chores clear the small debt.

**Branch:** `sprint-6` (commits `8f061a7..24975e1`) · **Committed:** 6 pts · **Done:** 6 pts
**Capacity:** ~6 (velocity 8/6/6/6/5/6, last-3 mean).

---

## STORY-010 — Core pipeline stages 1–2: collapse + streak (3 pts) — ✅ DONE

**Pipeline:** implementer (Sonnet) → spec review **PASS** (Opus) → quality review (Opus):
1 MAJOR → **fix loop 1** (fresh Sonnet) → re-review **APPROVE** (Opus) → DoD gate green.

Built (pure core, `core/services/pipeline.py` + `core/domain/verdict.py`):
- **`Verdict`** domain type — one cycle's collapsed verdict for one signal (`signal_key`,
  `observed_at`, `health: Health | None`, `under_maintenance`).
- **`collapse`** — per-location observations → one verdict (all-up→up, all-down→down, else
  degraded); maintenance is an injected boolean, excluded from the verdict, short-circuits.
- **`streak`** — consecutive same-health verdicts reading backward over non-maintenance
  verdicts only (transparently skips maintenance gaps).

### AC checklist (spec reviewer verified each MET)
- **AC1** collapse health rule, single + multi location ✅
- **AC2** maintenance excluded from verdict + short-circuit + excluded from streak ✅
- **AC3** streak backward, terminates on health change, skips maintenance ✅
- **AC4** pure + provider-blind, `lint-imports` green, new type in `core/domain/` ✅

**Fix loop:** quality review caught `collapse([])` leaking a `max() iterable argument is empty`
instead of a clear domain error (the symmetric `streak([])` was handled). Fix loop 1 added a
top-of-function guard (`ValueError("collapse requires at least one observation for a cycle")`)
+ a message-matching test; re-review APPROVE.

### Non-blocking minors recorded (notes)
- The `Verdict` `under_maintenance ⇔ health is None` invariant is documented but not enforced
  (a `model_validator` would close it, consistent with `signal.py`).
- `Streak.health` non-optional while `streak()` returns `Streak | None` — judged fine.

---

## STORY-021 — Reject native_id in the DQL query builder (1 pt) — ✅ DONE
`build_dql_query` now raises `InvalidNativeIdError` on a `native_id` containing a DQL-breaking
char (`"`, backslash, newline) instead of silently malforming the query. 2 tests (reject +
no-regression). Light pipeline.

## STORY-022 — Fail loud on a mixed-signal batch (1 pt) — ✅ DONE
`IngestService.ingest_observations` now raises `MixedSignalBatchError` (naming the keys) up
front if a batch spans >1 `signal_key`, before any validation/persist/watermark work — closing
the STORY-009 latent hazard. Single-signal + empty-batch paths unchanged. Light pipeline.

## STORY-023 — Clarify the double stop_event check (1 pt) — ✅ DONE
Comment-only: explains why `run_periodic` re-checks `stop_event` after the cycle (skip the final
sleep on a mid-cycle stop). Done directly by the orchestrator per the sprint-5 amendment (no
testable behaviour; existing pull-loop tests are the guard). Light pipeline.

---

## DoD evidence (orchestrator-verified; consolidated DB gate at the final tree)
| Command | Result |
|---|---|
| `pytest` | 162 passed (133 baseline + 25 pipeline + 1 fix-loop + 2 native_id + 1 mixed-signal) |
| `lint-imports` | 3 kept, 0 broken |
| `check_fk_direction.py` | 10 FKs, 0 violations |
| `alembic upgrade head` | no-op (no migration — pure-core sprint) |

## Demo
- Pipeline: `pytest backend/tests/test_pipeline.py backend/tests/test_streak.py backend/tests/test_verdict.py`.
- Chores: `pytest backend/tests/test_dynatrace_adapter.py backend/tests/test_ingest_service.py backend/tests/test_pull_loop.py`.
- All core logic tested with in-memory canonical fixtures — no live services.

## Wiki
Compile pass done (blocks review): no stale articles; the narrowed `architecture-boundary.md`
correctly did NOT go falsely stale (sprint-5 amendment paid off); learnings folded into
`canonical-types-and-ports.md` (Verdict + pipeline), `dynatrace-adapter.md` (native_id guard),
`ingest-service-and-pull-loop.md` (mixed-signal guard + stop-check comment). Links lint clean.

## Carried into Sprint 7
- STORY-024 (anti-flap + decide, 5, draft) — two open questions (config mechanism, proposal seam).
- STORY-011 (availability calculator, 5, draft) — depends on collapse (now built).

## PO verdict
- [x] STORY-010 — **ACCEPTED** (2026-06-25). 3 pts. Merged to main.
- [x] STORY-021 — **ACCEPTED** (2026-06-25). 1 pt. Merged to main.
- [x] STORY-022 — **ACCEPTED** (2026-06-25). 1 pt. Merged to main.
- [x] STORY-023 — **ACCEPTED** (2026-06-25). 1 pt. Merged to main.
- PO directed a follow-up from the minor: **STORY-025** (enforce the Verdict
  `under_maintenance ⇔ health is None` invariant via a `model_validator`) added to the backlog
  as `ready`. The second minor (`Streak.health` typing) needs no action.
