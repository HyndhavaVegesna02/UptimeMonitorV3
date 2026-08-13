# Backlog board

**Snapshot at sprint-71, commit `c325cd5`, generated 2026-08-14.** Regenerated ONCE per sprint at close, so it is expected to lag `.scrum/backlog.yaml` mid-sprint — `backlog.yaml` is always the source of truth. Rebuild with `python .claude/skills/yourteam/scripts/yt_board.py`.

**171/189 stories closed.** 18 open: 2 estimated (3 pts) + **16 unestimated**.

> ⚠ Total work remaining is NOT computable: 16 of 18 open stories carry no estimate, so any points figure below covers only the estimated ones. Refinement closes this gap; no arrangement of the file can.

## Open work

| Epic | Progress | Stories | Est. pts | Unestimated |
| --- | --- | --- | --- | --- |
| **Sprint 62 — fleet readiness foundation** <br>`sprint-62-fleet` | `#########.` | 6/7 | 20/22 | — |
| **Deferred / future work, filed at sprint-62 planning** <br>`deferred-future` | `..........` | 0/6 | 0/0 | 6 |
| **Deferred by explicit PO decision (recorded, not forgotten)** <br>`deferred-by-po` | `#######...` | 13/18 | 13/14 | 4 |
| **Split out / created at sprint-65 refinement (2026-07-30)** <br>`sprint-65-splits` | `#########.` | 19/21 | 47/47 | 2 |
| **Process: the ratchet brake (filed 2026-08-01, PO-directed)** <br>`process-ratchet-brake` | `#######...` | 10/14 | 19/19 | 4 |

### Open stories by epic

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
- `ready` [STORY-186](docs/scrum/stories/STORY-186-demo-engine-doc-and-test-hygiene.md) — Demo-engine doc and test hygiene batch (wiki prose, parametrised rejection tests, minors) · chore · 1 pts

**Split out / created at sprint-65 refinement (2026-07-30)**

- `draft` [STORY-192](docs/scrum/stories/STORY-192-wiki-mojibake-repair.md) — Mojibake in docs/scrum/wiki/ — 218 corrupted sequences across 5 articles, and the encoding guard passes them clean · defect · **unestimated**
- `draft` STORY-193 _(no story file yet)_ — Proposal formation is not reliably assertable in a loop run — the orchestrate window outruns past-anchored rows · defect · **unestimated**

**Process: the ratchet brake (filed 2026-08-01, PO-directed)**

- `draft` [STORY-221](docs/scrum/stories/STORY-221-frontend-gate-flake-maintenance-page.md) — The frontend gate can false-red under parallel file execution -- MaintenancePage inline-422 assertions · defect · **unestimated**
- `draft` [STORY-223](docs/scrum/stories/STORY-223-wiki-citation-resolution.md) — Wiki Fact citations that do not resolve from the repo root — 146 across 11 articles, silently skipped by the Facts lint · defect · **unestimated**
- `draft` [STORY-224](docs/scrum/stories/STORY-224-skill-tests-outside-the-gate.md) — An entire second test suite exists and the DoD gate does not run it — 7 skill-level modules, including the two guards that have already caught real defects · defect · **unestimated**
- `draft` [STORY-225](docs/scrum/stories/STORY-225-infra-files-outside-wiki-coverage.md) — The deployment/infra files are in no article's code_refs — infra/stack.yaml is gated every run but hooked by no wiki article · defect · **unestimated**

## Complete

20 epics with no open stories. Listed, not detailed — this is the three quarters of the backlog that no longer needs reading.

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
- **AWS migration epic (PO decisions 2026-07-14; supersedes STORY-017)** — 16 stories, 47 pts
- **Frontend rebuild programme (3rd attempt line)** — 13 stories, 0 pts

