# Backlog board

**Snapshot at sprint-72, commit `a47c469`, generated 2026-08-15.** Regenerated ONCE per sprint at close, so it is expected to lag `.scrum/backlog.yaml` mid-sprint — `backlog.yaml` is always the source of truth. Rebuild with `python .claude/skills/yourteam/scripts/yt_board.py`.

**177/191 stories closed.** 14 open: 3 estimated (13 pts) + **11 unestimated**.

> ⚠ Total work remaining is NOT computable: 11 of 14 open stories carry no estimate, so any points figure below covers only the estimated ones. Refinement closes this gap; no arrangement of the file can.

## Open work

| Epic | Progress | Stories | Est. pts | Unestimated |
| --- | --- | --- | --- | --- |
| **Sprint 62 — fleet readiness foundation** <br>`sprint-62-fleet` | `#########.` | 6/7 | 20/23 | — |
| **Deferred / future work, filed at sprint-62 planning** <br>`deferred-future` | `#.........` | 1/8 | 0/10 | 5 |
| **Deferred by explicit PO decision (recorded, not forgotten)** <br>`deferred-by-po` | `########..` | 15/18 | 16/16 | 3 |
| **Split out / created at sprint-65 refinement (2026-07-30)** <br>`sprint-65-splits` | `#########.` | 19/21 | 47/47 | 2 |
| **Process: the ratchet brake (filed 2026-08-01, PO-directed)** <br>`process-ratchet-brake` | `#########.` | 13/14 | 25/25 | 1 |

### Open stories by epic

**Sprint 62 — fleet readiness foundation**

- `ready` [STORY-147](docs/scrum/stories/STORY-147-component-group-description.md) — Component group + description — config to ComponentDTO · feature · 3 pts

**Deferred / future work, filed at sprint-62 planning**

- `blocked` STORY-150 _(no story file yet)_ — Anti-flap Phase 2 — breadth sets a severity ceiling, duration climbs to it (D1/D2) · feature · **unestimated**
- `draft` STORY-151 _(no story file yet)_ — Per-component decision rollup — one writer of a component's status (worst-of) · defect · **unestimated**
- `draft` STORY-152 _(no story file yet)_ — Completeness uses expected locations, not observed ones · defect · **unestimated**
- `draft` STORY-153 _(no story file yet)_ — Rejected proposal reopens on the next cycle — needs a suppression window (F1) · defect · **unestimated**
- `blocked` STORY-154 _(no story file yet)_ — Map the real Dynatrace HTTP failure codes (blocked on trial renewal) · chore · **unestimated**
- `ready` [STORY-155a](docs/scrum/stories/STORY-155a-remove-sample-mode-frontend.md) — Remove sample_mode from the frontend — the consumer goes first · chore · 3 pts
- `ready` [STORY-155b](docs/scrum/stories/STORY-155b-remove-sample-mode-backend.md) — Remove sample_mode from the backend, and tombstone its article · chore · 7 pts

**Deferred by explicit PO decision (recorded, not forgotten)**

- `blocked` STORY-172 _(no story file yet)_ — Per-location streak persistence — separate a regional outage from a flaky probe (F2) · feature · **unestimated**
- `draft` STORY-174 _(no story file yet)_ — Expose probe-location labels through the API (B7 consumption side) · feature · **unestimated**
- `blocked` STORY-175 _(no story file yet)_ — Fleet expansion — author the real multi-component topology · chore · **unestimated**

**Split out / created at sprint-65 refinement (2026-07-30)**

- `draft` [STORY-192](docs/scrum/stories/STORY-192-wiki-mojibake-repair.md) — Mojibake in docs/scrum/wiki/ — 218 corrupted sequences across 5 articles, and the encoding guard passes them clean · defect · **unestimated**
- `draft` STORY-193 _(no story file yet)_ — Proposal formation is not reliably assertable in a loop run — the orchestrate window outruns past-anchored rows · defect · **unestimated**

**Process: the ratchet brake (filed 2026-08-01, PO-directed)**

- `draft` [STORY-223](docs/scrum/stories/STORY-223-wiki-citation-resolution.md) — Wiki Fact citations that do not resolve from the repo root — 146 across 11 articles, silently skipped by the Facts lint · defect · **unestimated**

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

