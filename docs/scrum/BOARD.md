# Backlog board

**Snapshot at sprint-70, commit `d2a42f4`, generated 2026-08-13.** Regenerated ONCE per sprint at close, so it is expected to lag `.scrum/backlog.yaml` mid-sprint — `backlog.yaml` is always the source of truth. Rebuild with `python .claude/skills/yourteam/scripts/yt_board.py`.

**166/187 stories closed.** 21 open: 6 estimated (9 pts) + **15 unestimated**.

> ⚠ Total work remaining is NOT computable: 15 of 21 open stories carry no estimate, so any points figure below covers only the estimated ones. Refinement closes this gap; no arrangement of the file can.

## Open work

| Epic | Progress | Stories | Est. pts | Unestimated |
| --- | --- | --- | --- | --- |
| **AWS migration epic (PO decisions 2026-07-14; supersedes STORY-017)** <br>`aws-migration` | `#########.` | 15/16 | 44/46 | — |
| **Sprint 62 — fleet readiness foundation** <br>`sprint-62-fleet` | `#########.` | 6/7 | 20/22 | — |
| **Deferred / future work, filed at sprint-62 planning** <br>`deferred-future` | `..........` | 0/6 | 0/0 | 6 |
| **Deferred by explicit PO decision (recorded, not forgotten)** <br>`deferred-by-po` | `######....` | 11/18 | 9/11 | 5 |
| **Split out / created at sprint-65 refinement (2026-07-30)** <br>`sprint-65-splits` | `#########.` | 18/21 | 46/47 | 2 |
| **Process: the ratchet brake (filed 2026-08-01, PO-directed)** <br>`process-ratchet-brake` | `########..` | 9/12 | 17/19 | 2 |

### Open stories by epic

**AWS migration epic (PO decisions 2026-07-14; supersedes STORY-017)**

- `ready` [STORY-222](docs/scrum/stories/STORY-222-record-stack-decommission.md) — Record the AWS stack decommission — CLAUDE.md and the two deployment wiki articles describe infrastructure that no longer exists · chore · 2 pts

**Sprint 62 — fleet readiness foundation**

- `ready` [STORY-147](docs/scrum/stories/STORY-147-component-group-description.md) — Component group + description — config to ComponentDTO · feature · 2 pts

**Deferred / future work, filed at sprint-62 planning**

- `blocked` STORY-150 _(no story file yet)_ — Anti-flap Phase 2 — breadth sets a severity ceiling, duration climbs to it (D1/D2) · feature · **unestimated**
- `draft` STORY-151 _(no story file yet)_ — Per-component decision rollup — one writer of a component's status (worst-of) · defect · **unestimated**
- `draft` STORY-152 _(no story file yet)_ — Completeness uses expected locations, not observed ones · defect · **unestimated**
- `draft` STORY-153 _(no story file yet)_ — Rejected proposal reopens on the next cycle — needs a suppression window (F1) · defect · **unestimated**
- `blocked` STORY-154 _(no story file yet)_ — Map the real Dynatrace HTTP failure codes (blocked on trial renewal) · chore · **unestimated**
- `draft` STORY-155 _(no story file yet)_ — Remove sample_mode (superseded by the demo engine) · chore · **unestimated**

**Deferred by explicit PO decision (recorded, not forgotten)**

- `blocked` STORY-172 _(no story file yet)_ — Per-location streak persistence — separate a regional outage from a flaky probe (F2) · feature · **unestimated**
- `draft` [STORY-173](docs/scrum/stories/STORY-173-dynamo-container-leak.md) — Killed pytest run leaks its DynamoDB Local container and stalls the next run · defect · **unestimated**
- `draft` STORY-174 _(no story file yet)_ — Expose probe-location labels through the API (B7 consumption side) · feature · **unestimated**
- `blocked` STORY-175 _(no story file yet)_ — Fleet expansion — author the real multi-component topology · chore · **unestimated**
- `draft` [STORY-179](docs/scrum/stories/STORY-179-dynamo-local-port-and-readiness.md) — dynamo_local picks an ephemeral port Docker maps but Windows won't route; readiness probe can't detect it · defect · **unestimated**
- `ready` [STORY-186](docs/scrum/stories/STORY-186-demo-engine-doc-and-test-hygiene.md) — Demo-engine doc and test hygiene batch (wiki prose, parametrised rejection tests, minors) · chore · 1 pts
- `ready` [STORY-189](docs/scrum/stories/STORY-189-sprint64-doc-gaps.md) — Close the two doc/wiki gaps sprint 64 found but deliberately left · chore · 1 pts

**Split out / created at sprint-65 refinement (2026-07-30)**

- `draft` [STORY-192](docs/scrum/stories/STORY-192-wiki-mojibake-repair.md) — Mojibake in docs/scrum/wiki/ — 218 corrupted sequences across 5 articles, and the encoding guard passes them clean · defect · **unestimated**
- `draft` STORY-193 _(no story file yet)_ — Proposal formation is not reliably assertable in a loop run — the orchestrate window outruns past-anchored rows · defect · **unestimated**
- `ready` [STORY-201](docs/scrum/stories/STORY-201-clickpath-require-field-hygiene.md) — Clickpath normalizer hygiene — use require_field for execution.outcome · chore · 1 pts

**Process: the ratchet brake (filed 2026-08-01, PO-directed)**

- `draft` [STORY-213](docs/scrum/stories/STORY-213-pagination-test-isolation.md) — test_dynamo_component_repository_list_components_paginates fails intermittently — the message reads as a pagination defect · defect · 2 pts
- `draft` [STORY-221](docs/scrum/stories/STORY-221-frontend-gate-flake-maintenance-page.md) — The frontend gate can false-red under parallel file execution -- MaintenancePage inline-422 assertions · defect · **unestimated**
- `draft` [STORY-223](docs/scrum/stories/STORY-223-wiki-citation-resolution.md) — Wiki Fact citations that do not resolve from the repo root — 146 across 11 articles, silently skipped by the Facts lint · defect · **unestimated**

## Complete

19 epics with no open stories. Listed, not detailed — this is the three quarters of the backlog that no longer needs reading.

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
- **Redesign backend-gap follow-ups (deferred out of sprint 38)** — 5 stories, 9 pts
- **Sprint-38 redesign follow-ups (found at review)** — 6 stories, 18 pts
- **Chores (from retros)** — 17 stories, 23 pts
- **API restructure "now" phase (2026-07-10 proposal)** — 8 stories, 19 pts
- **Frontend rebuild programme (3rd attempt line)** — 13 stories, 0 pts

