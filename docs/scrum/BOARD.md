# Backlog board

**Snapshot at sprint-69, commit `df786be`, generated 2026-08-12.** Regenerated ONCE per sprint at close, so it is expected to lag `.scrum/backlog.yaml` mid-sprint — `backlog.yaml` is always the source of truth. Rebuild with `python .claude/skills/yourteam/scripts/yt_board.py`.

**138/185 stories closed.** 47 open: 9 estimated (15 pts) + **38 unestimated**.

> ⚠ Total work remaining is NOT computable: 38 of 47 open stories carry no estimate, so any points figure below covers only the estimated ones. Refinement closes this gap; no arrangement of the file can.

## Open work

| Epic | Progress | Stories | Est. pts | Unestimated |
| --- | --- | --- | --- | --- |
| **Redesign backend-gap follow-ups (deferred out of sprint 38)** <br>`dashboard-gap-followups` | `######....` | 3/5 | 9/9 | 2 |
| **API restructure "now" phase (2026-07-10 proposal)** <br>`api-restructure` | `#########.` | 7/8 | 19/19 | 1 |
| **AWS migration epic (PO decisions 2026-07-14; supersedes STORY-017)** <br>`aws-migration` | `#########.` | 14/15 | 44/44 | 1 |
| **Sprint 62 — fleet readiness foundation** <br>`sprint-62-fleet` | `#########.` | 6/7 | 20/22 | — |
| **Deferred / future work, filed at sprint-62 planning** <br>`deferred-future` | `..........` | 0/6 | 0/0 | 6 |
| **Frontend rebuild programme (3rd attempt line)** <br>`frontend-rebuild` | `..........` | 0/13 | 0/0 | 13 |
| **Deferred by explicit PO decision (recorded, not forgotten)** <br>`deferred-by-po` | `####......` | 7/18 | 9/11 | 9 |
| **Split out / created at sprint-65 refinement (2026-07-30)** <br>`sprint-65-splits` | `#########.` | 18/21 | 46/47 | 2 |
| **Process: the ratchet brake (filed 2026-08-01, PO-directed)** <br>`process-ratchet-brake` | `##........` | 2/11 | 6/16 | 4 |

### Open stories by epic

**Redesign backend-gap follow-ups (deferred out of sprint 38)**

- `draft` [STORY-063](docs/scrum/stories/STORY-063-proposal-enrichment.md) — Proposal enrichment — severity / reason / source / triggering-signals on ProposalDTO (Approvals cards) · feature · **unestimated**
- `draft` [STORY-067](docs/scrum/stories/STORY-067-component-grouping-uptime-buckets.md) — Component grouping + per-component uptime-bucket API (Dashboard groups + richer sparklines) · feature · **unestimated**

**API restructure "now" phase (2026-07-10 proposal)**

- `draft` [STORY-081](docs/scrum/stories/STORY-081-publication-incident-id.md) — Publication incident-id capture (Statuspage response → Publications timeline) · feature · **unestimated**

**AWS migration epic (PO decisions 2026-07-14; supersedes STORY-017)**

- `draft` [STORY-090](docs/scrum/stories/STORY-090-cicd-github-actions.md) — CI/CD stage 2 — GitHub Actions pipelines + OIDC deploy role · chore · **unestimated**

**Sprint 62 — fleet readiness foundation**

- `ready` [STORY-147](docs/scrum/stories/STORY-147-component-group-description.md) — Component group + description — config to ComponentDTO · feature · 2 pts

**Deferred / future work, filed at sprint-62 planning**

- `draft` STORY-150 _(no story file yet)_ — Anti-flap Phase 2 — breadth sets a severity ceiling, duration climbs to it (D1/D2) · feature · **unestimated**
- `draft` STORY-151 _(no story file yet)_ — Per-component decision rollup — one writer of a component's status (worst-of) · defect · **unestimated**
- `draft` STORY-152 _(no story file yet)_ — Completeness uses expected locations, not observed ones · defect · **unestimated**
- `draft` STORY-153 _(no story file yet)_ — Rejected proposal reopens on the next cycle — needs a suppression window (F1) · defect · **unestimated**
- `draft` STORY-154 _(no story file yet)_ — Map the real Dynatrace HTTP failure codes (blocked on trial renewal) · chore · **unestimated**
- `draft` STORY-155 _(no story file yet)_ — Remove sample_mode (superseded by the demo engine) · chore · **unestimated**

**Frontend rebuild programme (3rd attempt line)**

- `draft` STORY-156 _(no story file yet)_ — Design system — Tailwind v4 theme from the reference, light + dark, contrast gate · feature · **unestimated**
- `draft` STORY-157 _(no story file yet)_ — App shell — dark inset sidebar, topbar, routing, responsive at 390 · feature · **unestimated**
- `draft` STORY-158 _(no story file yet)_ — Dashboard page — hero, KPIs, component cards on real fleet-scale data · feature · **unestimated**
- `draft` STORY-159 _(no story file yet)_ — Fleet summary endpoint (B1) — worst-of status, bucket counts, fleet availability · feature · **unestimated**
- `draft` STORY-160 _(no story file yet)_ — Availability page — two-grain table, range tabs, completeness column · feature · **unestimated**
- `draft` STORY-161 _(no story file yet)_ — Bucketed availability series (B3) — N per-bucket verdicts over a window · feature · **unestimated**
- `draft` STORY-162 _(no story file yet)_ — Check History page — fleet-wide feed, filters, pagination, OUR result vocabulary · feature · **unestimated**
- `draft` STORY-163 _(no story file yet)_ — Fleet history endpoint (B2) — optional signal_key, filters, offset, total count · feature · **unestimated**
- `draft` STORY-164 _(no story file yet)_ — Approvals page — master/detail, reasoning + evidence, approve/reject · feature · **unestimated**
- `draft` STORY-165 _(no story file yet)_ — Populate StatusProposal.reason at open time (B8) · feature · **unestimated**
- `draft` STORY-166 _(no story file yet)_ — Maintenance page — status tabs, window cards, schedule form · feature · **unestimated**
- `draft` STORY-167 _(no story file yet)_ — Publications page — timeline of publish attempts · feature · **unestimated**
- `draft` STORY-168 _(no story file yet)_ — Batch component availability (B6) — kill the dashboard/availability N+1 · chore · **unestimated**

**Deferred by explicit PO decision (recorded, not forgotten)**

- `draft` STORY-169 _(no story file yet)_ — Publication headline + body — authored incident notes (B9) · feature · **unestimated**
- `draft` STORY-170 _(no story file yet)_ — Multi-component maintenance windows + publications (B10) · feature · **unestimated**
- `draft` STORY-171 _(no story file yet)_ — Real auth — replace the fixed `dashboard-operator` actor constant · feature · **unestimated**
- `draft` STORY-172 _(no story file yet)_ — Per-location streak persistence — separate a regional outage from a flaky probe (F2) · feature · **unestimated**
- `draft` STORY-173 _(no story file yet)_ — Killed pytest run leaks its DynamoDB Local container and stalls the next run · defect · **unestimated**
- `draft` STORY-174 _(no story file yet)_ — Expose probe-location labels through the API (B7 consumption side) · feature · **unestimated**
- `draft` STORY-175 _(no story file yet)_ — Fleet expansion — author the real multi-component topology · chore · **unestimated**
- `draft` STORY-178 _(no story file yet)_ — yt_gate.py exits 0 when --only matches nothing (false green on the DoD floor) · defect · **unestimated**
- `draft` STORY-179 _(no story file yet)_ — dynamo_local picks an ephemeral port Docker maps but Windows won't route; readiness probe can't detect it · defect · **unestimated**
- `ready` [STORY-186](docs/scrum/stories/STORY-186-demo-engine-doc-and-test-hygiene.md) — Demo-engine doc and test hygiene batch (wiki prose, parametrised rejection tests, minors) · chore · 1 pts
- `ready` [STORY-189](docs/scrum/stories/STORY-189-sprint64-doc-gaps.md) — Close the two doc/wiki gaps sprint 64 found but deliberately left · chore · 1 pts

**Split out / created at sprint-65 refinement (2026-07-30)**

- `draft` STORY-192 _(no story file yet)_ — The same encoding corruption exists in docs/scrum/wiki/ — 246 mojibake sequences across 6 files · defect · **unestimated**
- `draft` STORY-193 _(no story file yet)_ — Proposal formation is not reliably assertable in a loop run — the orchestrate window outruns past-anchored rows · defect · **unestimated**
- `ready` [STORY-201](docs/scrum/stories/STORY-201-clickpath-require-field-hygiene.md) — Clickpath normalizer hygiene — use require_field for execution.outcome · chore · 1 pts

**Process: the ratchet brake (filed 2026-08-01, PO-directed)**

- `draft` [STORY-211](docs/scrum/stories/STORY-211-plan-on-context-and-token-budget.md) — Plan sprints on context and token budget instead of story points · chore · **unestimated**
- `draft` [STORY-212](docs/scrum/stories/STORY-212-evidence-check-script-rung.md) — Land the evidence-artifact rule at the SCRIPT rung (mutation + provenance helper) · chore · **unestimated**
- `draft` [STORY-213](docs/scrum/stories/STORY-213-pagination-test-isolation.md) — test_dynamo_component_repository_list_components_paginates fails intermittently — the message reads as a pagination defect · defect · 2 pts
- `draft` STORY-214 _(no story file yet)_ — Extract the LastEvaluatedKey pagination loop into a shared helper — and rework the ZR-7 guard that would forbid it · chore · **unestimated**
- `draft` [STORY-217](docs/scrum/stories/STORY-217-topology-write-port.md) — Composition still writes to DynamoDB directly — decide whether topology seeding needs a real write port · chore · 1 pts
- `draft` [STORY-218](docs/scrum/stories/STORY-218-settings-defaults-declared-twice.md) — Settings declares every default TWICE — and the ZR-3 sweep is structurally blind to it · chore · 2 pts
- `draft` [STORY-219](docs/scrum/stories/STORY-219-enforce-citation-resolution.md) — Wire tools/citation_sweep.py into the gate — the capability exists and is unenforced · chore · 3 pts
- `draft` [STORY-220](docs/scrum/stories/STORY-220-zr1-forbidden-list-completeness-test.md) — ZR-1's forbidden-module list is maintained by a prose note -- make its completeness a test · chore · 2 pts
- `draft` [STORY-221](docs/scrum/stories/STORY-221-frontend-gate-flake-maintenance-page.md) — The frontend gate can false-red under parallel file execution -- MaintenancePage inline-422 assertions · defect · **unestimated**

## Complete

16 epics with no open stories. Listed, not detailed — this is the three quarters of the backlog that no longer needs reading.

- **Sprint 0 — Setup** — 3 stories, 8 pts
- **Zone 1 — Canonical types + ports** — 2 stories, 6 pts
- **Zone 2 — Schema + migrations + repositories** — 2 stories, 8 pts
- **Zone 3 — Ingest adapter** — 2 stories, 10 pts
- **Zone 4 — Core pipeline + availability** — 5 stories, 17 pts
- **Zone 5 — Proposal lifecycle + publish** — 2 stories, 6 pts
- **Zone 6 — API** — 5 stories, 23 pts
- **Zone 7 — Frontend** — 1 stories, 5 pts
- **Zone 7 — Frontend split (STORY-015 → shell + six per-tab stories)** — 10 stories, 31 pts
- **2026-07-02 full-codebase audit output** — 4 stories, 13 pts
- **Sample switch (PO idea, 2026-07-03 post-sprint-30 demo)** — 5 stories, 13 pts
- **Config / Topology / Orchestration (backend; pre-frontend)** — 3 stories, 15 pts
- **Integration + Deployment (live-credential / account gated)** — 6 stories, 21 pts
- **Operator Dashboard redesign (Sprint 38; PO-approved 2026-07-07)** — 8 stories, 31 pts
- **Sprint-38 redesign follow-ups (found at review)** — 6 stories, 18 pts
- **Chores (from retros)** — 17 stories, 23 pts

