# Sprint 45 Review — Redesign backend-gap follow-ups (Maintenance + Publications)

**Date:** 2026-07-13 · **Branch:** `sprint-45` · **Mode:** in-process · **Committed:** 6 pts · **Accepted:** 6 pts
**Gate HEAD:** `f53819e` (GREEN) · **Merged to:** `main` (local; not pushed — PO to push)

**Goal:** The Maintenance tab gains a real Title field and a per-window delete (STORY-065), and the
Publications timeline shows the real publish author (STORY-066, author-only) — closing two Sprint 38
redesign data gaps against real API data.

## Execution note
Implementation was delegated to a PO-driven external agent (handoff.md), handed back complete at
`48fba51`. The orchestrator (session `cc-sprint45-close-20260713-2231`) ran the DoD gate, reviews,
and reality gate. First review returned quality FIX_REQUIRED on 065 (styling) + a minor on 066 (MSW
actor); the external agent applied both fixes (`cbe628b`, `356fb8a`); the orchestrator re-reviewed,
re-gated GREEN, and ran both reality gates before this review.

## STORY-065 — Maintenance title + DELETE (3 pts) — ACCEPTED

| AC | Result | Evidence |
| -- | ------ | -------- |
| AC1 title model + schema | ✅ | migration `b52c8865a2c1` (nullable `title` off `a2c1d89efcea`); `alembic upgrade head` exit 0; FK-direction 0 violations |
| AC2 title persistence parity | ✅ | fake+Postgres contract tests (pytest 570 green); live: POST→201 body carries `title`, GET row carries `title` |
| AC3 DELETE endpoint (204/404) | ✅ | live: `DELETE /maintenance/1`→204, GET→[]; `DELETE /999999`→404 `MaintenanceWindowNotFoundError`. Codebase's first DELETE verb |
| AC4 frontend title renders | ✅ | 363 component tests incl. "title renders on the created row" (plan-verifier hardening) |
| AC5 frontend inline-confirm delete + 404 state | ✅ | component tests cover delete-success + delete-404; no `window.confirm`/modal |
| Gates + wiki blast radius | ✅ | 9-command gate GREEN; `yt_wiki.py` sweep CLEAN (frontend-zone.md re-verified) |

- **Spec review:** PASS (AC→test trace complete). **Quality:** FIX_REQUIRED → **APPROVE**.
  - Fix (`cbe628b`): 9 static inline styles + orphan BEM hooks in `MaintenancePage.tsx` moved to
    `MaintenancePage.css` under design tokens. Orchestrator re-review at `f53819e`: 0 inline styles,
    all 13 `maintenance-window*` class hooks have backing CSS (exact className↔selector match), all
    8 referenced tokens exist in `styles/`.
- **Reality gate:** PASS (live wire cycle vs real ASGI backend / throwaway Postgres).

## STORY-066 — Publication author, author-only (3 pts) — ACCEPTED

| AC | Result | Evidence |
| -- | ------ | -------- |
| AC1/AC2 derive-on-read author (parity) | ✅ | correlated scalar subquery (not LEFT JOIN); fake+Postgres contract tests incl. two-approved-events defensive case; live: seeded approved proposal (actor `dashboard-operator`) → wire `author="dashboard-operator"` == DB `approval_events.actor` |
| AC1 null case | ✅ | live: proposal-less publication → `author=null` (graceful) |
| AC3 no migration | ✅ | story diff adds none under `migrations/`; FK-direction 0 |
| AC4 frontend render + null degrade | ✅ | 363 component tests; MSW fixtures use canonical `dashboard-operator` (minor fix `cbe628b`) |
| Gates + wiki | ✅ | GREEN; sweep CLEAN |

- **Spec review:** PASS. **Quality:** APPROVE (1 minor — MSW actor not the canonical seam — fixed in `cbe628b`).
- **Reality gate:** PASS (live wire author derivation + null).

## DoD gate — GREEN @ `f53819e`
pytest 570 · import-linter 8/8 kept · FK 0 violations · alembic clean · ruff check + format clean ·
frontend 363 tests + build + lint. One first-run `dev_db` container-contention flake (1/570) proven
benign per the 2026-07-06 agreement (empty diff since cut + 2/2 isolation); clean rerun 570/570.
Detail in `sprint-current.yaml::gate_notes`.

## PO verdict
**Accept both** (2026-07-13). STORY-065 + STORY-066 → `main`. Velocity 6/6.

## Carried to retro
1. STORY-080 — `dev_db` CLI hardcoded-port contention (open defect; the recurring gate flake source).
2. Bake `PYTHONUTF8=1` into `yt_gate.py`'s subprocess env (script rung; still open).
3. YourTeam git-guard hook template should use `$CLAUDE_PROJECT_DIR` (fixed here at `f53819e`).
4. `origin/HEAD` points at stale `debug/ingest-stall-sample-mode` (293 behind `main`) — housekeeping.
