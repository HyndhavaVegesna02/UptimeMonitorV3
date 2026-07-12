# Sprint 44 Plan — YourTeam v2 PILOT

**Goal:** Check History shows the real HTTP status code and check type from live Dynatrace data
(STORY-064), and the wiki's Facts-coverage gap class is closed (STORY-079) — executed end-to-end
on the YourTeam v2 machinery as its pilot.

- **Date:** 2026-07-12 · **Mode:** `in-process` · **Stories:** 064 (3p) + 079 (2p) = 5p
- **Pilot notes:** branch `sprint-44` cuts from `yourteam-v2` (v2 is not on main yet — accepting
  this sprint at review also lands YourTeam v2 on main). Lock authorized by the PO's
  2026-07-12 "run the pilot" directive with the recommended scope.
- **Order:** 064 first (code, risk, blast radius), then 079 (prose tail — lints the wiki in its
  post-064 final state).
- **Retro input (recorded at planning):** baseline gate caught two reds — unformatted v2 scripts
  (fixed) and `lint-imports.exe` blocked by a new Windows Application Control policy → standing
  DoD command moved to the module path (`python -c "from importlinter.cli import
  lint_imports_command; lint_imports_command()"`), CLAUDE.md synced (commit 0889259).

## Preconditions (verified)

- Full nine-command gate green: seven at 212f21f, the two repaired commands at 0889259
  (only skill-file formatting + the DoD invocation changed between the runs; no product code).
- Working tree clean (untracked PO artifacts only); throwaway DB up + migrated on :55432.
- Mode declared; plan verified by yt-plan-verifier before lock (verdict recorded below).

## Verified API contracts (STORY-064)

- **Wire (live Grail probe, 2026-07-12, monitor `HTTP_CHECK-38B092E93932C002`, 20/20 rows):**
  the canonical `http_monitor_execution` row carries `result.statistics.response_status_code`
  as a STRING-typed number (`"200"`). Normalization parses to `int`; missing or unparsable →
  `None`, never a crash. `event.type` distribution is exactly
  {`http_monitor_execution`, `http_step_execution`} 1:1; we ingest only the former (STORY-016c).
- **check_type:** no dedicated Grail field. Source is the ALREADY-PERSISTED
  `Provenance.native_kind` — the constant `http_normalizer.py::NATIVE_KIND = "http"` stamped by
  the normalizer (the `event.type` → normalizer routing lives in the adapter's dispatch table);
  stored in `observations.source` JSONB and reconstructed by both repository implementations.
  DTO carries `check_type: str` = `native_kind` verbatim (`"http"`); the frontend renders it
  uppercased. No new capture.
- **Scale/units:** `response_status_code` is a unitless int passthrough after str→int (no
  fraction/percent trap); `latency_ms` precedent (ns→ms ÷1e6) is untouched.
- **Current producer shape:** `api/v1/history/models.py::ObservationDTO` =
  `{signal_key, observed_at, health, location, latency_ms?}`;
  `service.py::HistoryService.get_history` maps domain→DTO directly (source/raw_ref omitted
  today). Domain: `core/domain/signal.py::SignalObservation` — 8 fields (signal_key,
  observed_at, health, source_event_id, source, location, latency_ms, raw_ref), no status code.
  DB: `observations` table (shape established by spine migration 3a8254bcfe59; the new revision
  chains off the CURRENT head `ecda752c8865`) — no code/type columns.
- **Fixture provenance — WIRE-TYPE WARNING (plan-verifier finding, round 1):** the checked-in
  fixtures (`grail_synthetic_events.json`, `grail_dual_event_types.json`) store
  `response_status_code` as JSON **int** `200`, which does NOT match the string-typed real wire
  (`"200"`, probe 2026-07-12) — an int row passes `int(x)` without ever driving the str→int
  parse. Step 2 therefore adds STRING-typed rows derived from the probe sample, and the
  present-case test MUST use the string shape. Frontend MSW — derived from a real
  `/api/v1/history` wire response captured during implementation (not invented).

## STORY-064 — Observation HTTP status code + check type (3p, full pipeline)

Edge behavior (explicit): wire field absent → `None`; non-numeric string → `None` (no crash, no
log-spam — canonicalization stays total); DTO serializes `None` → JSON `null`; frontend `null` →
"—". `check_type` always present (provenance is mandatory).

Steps (TDD; commit after every green step):
- [ ] 1. Domain: failing test — `SignalObservation` gains frozen `response_status_code: int | None = None`
        (no cross-field invariant → no validator; mirror existing optional-field style, e.g.
        `latency_ms`). Minimal code, green, commit.
- [ ] 2. Normalizer: failing tests on probe-derived fixture rows — present STRING `"200"` → int
        `200` (the real wire shape; an int-typed fixture row does not satisfy this case);
        absent → `None`; non-numeric → `None`. Add the string-typed rows from the 2026-07-12
        probe sample to the fixtures. Implement extraction in the shared assembly path
        (`_assembly.py::assemble_observation` + `http_normalizer.py`), green, commit.
        (Note, bounded scope: the existing fixtures' int-typed `response_status_code` values may
        be aligned to the string wire shape while adding rows; if any existing test then fails,
        that reveals a real int assumption — fix within this step. Broader fixture-typing audit
        of other numeric fields is a candidate follow-up story, not this one.)
- [ ] 3. Migration: new Alembic revision — nullable `Integer` column
        `observations.response_status_code`; upgrade green on fresh DB (migrated_db fixture);
        downgrade drops cleanly. Commit.
- [ ] 4. Persistence parity: the SAME contract test against `PostgresObservationRepository` AND
        the in-memory fake — round-trip incl. `None`. Implement both mappings, green, commit.
- [ ] 5. API: failing endpoint test — `/api/v1/history` rows carry `response_status_code`
        (int|null) + `check_type` (from persisted `source.native_kind`); extend `ObservationDTO`
        + `HistoryService` mapping; all existing history validation tests stay green. Commit.
- [ ] 6. Frontend: mirror DTO in `api/types.ts`; add Type + Code columns to the Check History
        grid; MSW fixtures from the real wire sample; tests cover populated + null ("—").
        Commit.
- [ ] 7. Gates + wiki blast radius: run `yt_wiki.py sweep`, update/re-verify every flagged
        article (commit per article); full `yt_gate.py` green; evidence recorded.
- [ ] 8. Reality gate (AC5): local stack live (DB + uvicorn :8000 + live loop + vite :5173);
        compare one rendered Check History row's Type + Code against the raw
        `/api/v1/history` wire values for the same record. Record the comparison.

## STORY-079 — Wiki Facts-coverage cleanup (2p, full pipeline for the pilot)

- [ ] 1. Enumerate: `yt_wiki.py facts` findings at post-064 HEAD (~20 expected + any new).
- [ ] 2. Per finding, per article: extend `code_refs` with the cited DEFINING file, or re-home
        the Fact to the covering article (claims text frozen — citations/refs only). Commit per
        article with a History line.
- [ ] 3. Re-verify touched articles (bump `verified_sha` to HEAD); `yt_wiki.py` (all three
        checks) exits 0. Full gate green (proves prose-only). Commit.

## Conventions

In-process mode: the yt-implementer agent loads `.scrum/checklists/implementer.md` (binding);
reviewers load theirs. Applicable highlights for 064: migration on DIRECT URL; fake/adapter
parity; tz-aware validation untouched; five-file shape (history feature already has its test);
no module-scope env side effects; fixtures from real samples.

## Plan verification

- Round 1 (yt-plan-verifier, Opus): **GAPS** — (1) checked-in Grail fixtures store
  `response_status_code` as JSON int `200` vs the string-typed real wire, so the str→int parse
  would ship green-but-untested (the S32 false-green class, caught pre-lock); (2) two accuracy
  errors in the "Verified API contracts" section (9→8 fields; NATIVE_KIND wording).
- Amendments applied (WIRE-TYPE WARNING + string-typed fixture requirement in step 2; contract
  section corrected; migration-chaining note).
- Round 2: **LOCK_READY** — all 11 checks pass, zero gaps. Locked under the PO's 2026-07-12
  "run the pilot" directive.
