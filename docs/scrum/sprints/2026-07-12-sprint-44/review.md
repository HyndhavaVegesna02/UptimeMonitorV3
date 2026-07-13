# Sprint 44 Review — YourTeam v2 PILOT

**Goal:** Check History shows the real HTTP status code and check type from live Dynatrace data
(064), the wiki Facts-coverage gap class is closed (079) — executed end-to-end on YourTeam v2.
**Committed 5 pts (064: 3, 079: 2). Both stories Done. Zero blocked.**
**Merge note:** sprint-44 was cut from `yourteam-v2`; accepting this sprint merges BOTH the two
stories AND YourTeam v2 (agents, hooks, scripts, checklists, migrated agreements) to main.

## STORY-064 — Observation HTTP status code + check type (3 pts)

**Built:** `result.statistics.response_status_code` captured at normalization (str→int, the real
string wire shape; absent/non-numeric → None), persisted via new nullable
`observations.response_status_code` column (migration `a2c1d89efcea`), served on `ObservationDTO`
alongside `check_type` (from persisted provenance `native_kind`), rendered as the Check History
grid's new Type and Code columns (null → "—").

**AC evidence:**
- AC1 (capture): string-typed `"200"` fixture rows drive the parse (plan-verifier round-1 catch:
  the old int-typed fixtures would have shipped the parse untested); absent/`"N/A"` → None.
  Existing fixtures realigned to the string wire — all tests stayed green (no hidden int
  assumption).
- AC2 (persist): same-body parity test against Postgres repo AND fake, round-tripping 200 and
  None; column verified `integer, nullable=YES` on a live DB.
- AC3 (serve): endpoint test asserts both fields; existing tz-aware validation untouched.
- AC4 (render): populated ("HTTP", "200") and null ("—") cases tested; MSW fixtures derive from
  the real probe capture.
- AC5 (reality gate): **live render-vs-wire exact match** — wire row
  `{observed_at 2026-07-12T17:08:46.505000Z, location …0060, response_status_code 200,
  check_type "http", latency_ms 531}` rendered as `Type=HTTP · Code=200 · Latency=531 ms`;
  120 live-ingested rows, distributions {200: 120} / {http: 120}.
- Gates: all nine green at `d3dce88` (564 backend, 361 frontend, 8 contracts, 11 FKs).

**Verdicts:** spec PASS (all ACs MET, tests run, deletion-check clean, zero scope additions);
quality APPROVE (zero critical/major; tests given "special hostility" — over-mock, deleted
coverage, invented fixtures, dirty-tree all checked clean; 1 minor recorded on the story file).

**Demo:** the local stack is LIVE — open `http://localhost:5173/check-history` (vite → uvicorn
:8000 → throwaway DB :55432 ← live loop ingesting the real Dynatrace tenant). Compare any row
against `curl http://localhost:8000/api/v1/history?signal_key=http-check`.

## STORY-079 — Wiki Facts-coverage cleanup (2 pts)

**Built:** all 19 Facts-coverage findings across 8 articles resolved (code_refs extensions,
claims frozen), commit-per-article; plus two `status:`-frontmatter comment bugs fixed. Quality
review then forced a fix loop with real teeth: two over-broad hot-file refs (CLAUDE.md,
pyproject.toml — the false-stale-busywork mode) re-scoped with their citations re-homed, and a
Fact clause that had become self-contradictory ("neither file appears in code_refs" — they now
did) deleted, with both reviewers converging on the ruling that ref-bookkeeping clauses are
citation matter, not frozen knowledge.

**AC evidence:** `yt_wiki.py` sweep + facts + links all CLEAN (exit 0) at `1d1500f`; 8 articles
re-verified with resolvable SHAs + History lines; story diff empty over
backend/frontend/scripts/migrations (prose-only, proven); all nine gates green at `1d1500f`.

**Verdicts:** spec PASS (first pass; flagged the self-contradiction as a non-blocking
AC-vs-hygiene conflict); quality APPROVE after the fix loop (3 MAJORs resolved; 2 minors
recorded on the story file).

## Follow-ups filed / carried

- **STORY-080 (defect, draft):** `test_dev_db_cli` hardcodes port 55433 — collided with the
  second reviewer DB this sprint (contention proven per the 2026-07-06 protocol); gate must be
  collision-proof.
- Candidate chores (recorded on story files): CheckHistoryPage null-code test cell-scoping
  (064 minor); two low-churn code_refs scoping notes (079 minors).
- v2 tooling defects found AND fixed in-sprint (orchestrator commits): yt_gate cp1252 output
  capture; yt_gate UTF-8 stdout; yt_wiki comment-blind frontmatter parser (an article was
  silently skipped by the sweep — the exact hole the sweep exists to close).

## Pilot success criteria (from YOURTEAM_REDESIGN_REVIEW.md)

| Criterion | Result |
|---|---|
| Zero prose-rule violations a hook/allowlist should have caught | **MET** — the git-guard hook fired once, correctly, BLOCKING a mis-sequenced lock commit; nothing landed wrong |
| Gate evidence script-written, byte-accurate | **MET** — every gate run emitted its own fragment; two runner bugs surfaced and fixed in-sprint |
| Subagent briefs measurably thinner | **MET** — briefs carried pointers + variables only; roles/model/tools lived in agent definitions; the 550-line agreements payload is gone (95-line file + targeted checklists) |
| ≥1 reality-gate execution recorded | **MET** — 064's live render-vs-wire exact match |
| Wiki tooling pass clean | **MET** — sweep/facts/links all CLEAN at close; 19 coverage gaps closed; parser hole fixed |

Also demonstrated: plan verifier killed an S32-class wrong-fixture assumption BEFORE lock
(round 1 GAPS → round 2 LOCK_READY); crash recovery cost ≤1 article's frontmatter on a
connection-drop (commit cadence + article-by-article commits + edge-case #13 tail completion);
reviews ran concurrently on isolated DBs; the fix loop used a fresh agent per the standing rule.

## Verdict requested from the PO

Per story, accept or reject: **STORY-064**, **STORY-079**. Accepting both merges sprint-44
(including YourTeam v2) to main; velocity records 5. Retro follows the verdicts.
