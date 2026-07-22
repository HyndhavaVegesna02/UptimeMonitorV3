# Sprint 60 — Review

**Goal:** Complete the operator cockpit begun in sprint 59 — build the five remaining tabs
(Availability, Check History, Approvals, Maintenance, Publications) as fresh, high-craft designs on
the sprint-59 design system + shell, each live on the real `/api/v1` backend. At sprint end all six
nav routes are real; the placeholder pages are gone.

**Mode:** in-process (pivoted from the PO-rejected external delivery — see
`scrap/sprint-60-external-rejected`). Each story: yt-implementer (TDD, commit-per-green-step) →
spec ∥ quality reviewers (3-pointers) → my own DoD gate → live scripted-Chromium reality gate.
STORY-133 (2 pts) ran the impl-only ceremony (no reviewer pair).

**Result: 5 of 5 stories done — 20 / 20 points.** All six nav routes now real; `PlaceholderPage`
deleted. Branch `sprint-60` @ `c3d9d39`, unmerged (awaiting PO acceptance; per the 2026-07-21
directive the new-frontend line stays unmerged on the ui-prototype branch).

---

## Per-story evidence

| Story | Pts | Spec | Quality | DoD (scoped) | Reality gate |
| --- | --- | --- | --- | --- | --- |
| 129 Availability | 5 | PASS | APPROVE | green @2280f67 | PASS (prior session) |
| 130 Check History | 3 | PASS | APPROVE | green @1d447d7 (525) | PASS — **caught + fixed a live defect** |
| 131 Approvals | 5 | PASS | APPROVE | green @bfcca9b (567) | PASS — empty state + live 404/422 probe |
| 132 Maintenance | 5 | PASS | APPROVE | green @b818dc3 (643) | PASS — **full live create→delete cycle** |
| 133 Publications | 2 | — (impl-only) | — (impl-only) | green @ce33f8c (663) | PASS — empty state + ~50-cap note |

### STORY-130 — Check History (`e21a9f0..1d447d7`)
Multi-signal merge with global `observed_at`-desc re-sort, filter toolbar (search / fixed Result
vocab / derived Location / window toggle), dense grid, ~1000 render cap, five states incl. distinct
filtered-empty. Dedicated observation-health mapper (not the vendor-status mapper).
**Reality gate earned its keep:** it caught a blocking defect the reviewers missed — the live wire
contains duplicate `(signal_key, observed_at, location)` triples, so the composite row key collided
→ React "duplicate key" console errors + visibly corrupted filtered rendering (168 rows with stale
locations vs live 164). Fixed (positional-index keys + a regression test reproducing the exact live
error), re-verified clean. *(Quality had dismissed this collision as "not realistic on the wire" —
reality proved it real. Retro item.)*

### STORY-131 — Approvals, first mutating page (`51c8adc..bfcca9b`)
Introduced the client write path (`postJson` + `postDecision`) — verified clean, general, reused by
132. Two-step confirm state machine (one decision at a time), 409/404 handling keyed off numeric
`ApiError.status` with real list-refresh, never throws to console. Live: empty "Queue clear" state
(matches `approvals=[]`) + direct probe of the real write endpoint (`POST /decisions/999999` → 404
`ProposalNotFoundError`; bad action → 422). Success/409 UI paths proven by forced MSW tests (the live
queue is empty and there is no create-proposal API in frontend scope — per the plan's "where a
proposal is available" framing).

### STORY-132 — Maintenance, schedule + delete (`53cb1f4..b818dc3`)
Windows list with client-derived upcoming/active/past badge (half-open rule, boundary-pinned);
uncontrolled schedule form (`datetime-local`→UTC-Z); the order-sensitive 422 field mapping proven at
3 levels ("strictly greater than" → `ends_at` first, not `starts_at`); delete-with-confirm, 204-safe
`deleteRequest`, non-idempotent 404 → non-destructive notice + refresh.
**Full live create→verify→delete cycle** through the UI: created via real POST (201; entered
08:00/10:00 IST → stored `02:30Z`/`04:30Z`, proving the UTC conversion), rendered with the correct
"Upcoming" badge, end-before-start showed the inline `ends_at` error, deleted via UI (204), list
reconciled — **live state left clean**.

### STORY-133 — Publications (`85090ed..ce33f8c`)
Read-only publish-attempt timeline: given-order render (no re-sort), outcome chip distinct from the
health status (never colour alone), `proposal_id`/`author` null→"—", no fabricated `incident_id`,
~50-cap note. Live empty "Nothing published yet" state (matches `publications=[]`); populated
timeline proven by component tests per the plan. **Deleted `PlaceholderPage`** (last mount) — all six
routes now real.

---

## Sprint-close full gate (evidence of record, final HEAD `c3d9d39`)

All 8 commands green. Backend/infra/config are **byte-unchanged since the sprint cut** (empty
`git diff sprint-60-start..HEAD -- backend/ infra/ config/ pyproject.toml`), so the backend results
reflect the untouched sprint-59 baseline.

| # | Command | Result |
| --- | --- | --- |
| 1 | pytest | PASS — 529 passed *(via `python -m pytest`; `pytest.exe` blocked by Device Guard)* |
| 2 | import-linter | PASS — 8 contracts kept *(via `python -c` callable; `.exe` blocked — documented)* |
| 3 | ruff check | PASS |
| 4 | ruff format --check | PASS — 206 files |
| 5 | cfn-lint | PASS — exit 0 *(via `cfnlint.runner:main` callable; `cfn-lint.exe` blocked by Device Guard)* |
| 6 | npm test | PASS — 663 tests / 84 files |
| 7 | npm run build | PASS |
| 8 | npm run lint | PASS |

**Tooling note (retro candidate):** the Windows Device Guard / Application Control policy (which has
blocked the `lint-imports.exe` shim since 2026-07-12) also blocks `pytest.exe` and `cfn-lint.exe`.
All three pass via module/callable invocation. `yt_gate.py` invokes the raw `.exe` shims for pytest
and cfn-lint, so the packaged gate reports RED on this machine despite green code — worth routing to
the module form in the DoD (enforcement-ladder: gate command).

## Wiki
Sprint-end compile pass: `yt_wiki.py sweep` → **CLEAN** (no stale, no broken links, no coverage
gaps). `frontend-zone.md` folded each story's blast-radius incrementally; `verified_sha` @ `2e97408`;
reflects all six routes real + `PlaceholderPage` removal.

## Follow-ups already filed (STORY-134, from review minors)
Flaky delay-based AC5 test hardening; a few px spacing literals; relative-time `tabular-nums`;
`Button` `forwardRef`/`type` passthrough (4 hand-rolled native-button call sites now); `<time>`
encodes only start; shared dense-table primitive (History/Availability/Publications duplicate CSS).

## Verdict requested (PO)
Per-story accept / reject. Recommendation: accept all five (branch stays unmerged on the
ui-prototype line unless you direct a swap).
