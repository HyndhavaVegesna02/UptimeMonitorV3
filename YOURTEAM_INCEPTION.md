# YourTeam Inception Seed — Uptime Monitor V3

> **For the YourTeam skill running in Claude Code.** This repo has no `.scrum/` yet, so you will offer Inception. Read this file *first* — it replaces the cold inception interview. The vision, users, stack, constraints, Definition of Done, and a horizontally-sliced backlog are already settled (see the companion architecture dossier `uptime-monitor-v3-design.html`). Your job at inception is to turn the backlog drafts below into refined stories for PO approval, propose the DoD and working agreements verbatim from here, and then run Sprint 0. Do **not** re-derive any of this conversationally — it is the output of an extended design process and is locked.
>
> **The dossier is the architectural source of truth.** Every story below references it. When briefing implementer/reviewer subagents, the relevant dossier section is the spec.

---

## 1. Vision

A **provider-agnostic uptime monitoring and status-page platform**. It ingests synthetic-monitoring results from an observability vendor (Dynatrace), runs them through a constant business core that turns raw signals into customer-facing status, and publishes approved status changes to a public status page (Statuspage). This is a **showcase environment, not production** — judged on demonstrating the architecture, not on production hardening.

**The organizing principle (governs every decision):** separation by replaceability. The monitored application is replaceable. The observability vendor is replaceable. The mapping configuration is replaceable. The business core — how signals become verdicts become status — is constant, sealed behind a canonical boundary. Litmus test: *delete the Dynatrace adapter, write a Datadog adapter implementing the same ports, change one wiring line — the core does not change by a single character.*

## 2. Users

- **Operators** (internal) — watch health, approve/reject proposed degradations, manage maintenance windows, audit ingestion. They use the internal dashboard.
- **Customers** (external) — see only the final, approved, published status on the public Statuspage. They never see proposals or the approval workflow.

## 3. Stack & Tooling Inventory

**Backend:** Python, FastAPI, run on Railway (single persistent container — the pull loop is a long-lived process, so the backend cannot be serverless).
**Database:** Neon serverless Postgres. Two connection strings — **pooled** (PgBouncer) for app runtime, **direct** (non-pooled) for Alembic migrations (DDL misbehaves through transaction pooling).
**Migrations:** Alembic, run as a **separate Railway release step** before the app container serves — never `create_all`, never on-boot.
**Frontend:** React + TypeScript on Vercel. Deploys independently of the backend.
**Observability source:** Dynatrace (Grail / DQL for synthetic monitor results). Polled via a pull loop.
**Publish target:** Statuspage SaaS (real, customer-facing).
**Monitored demo app:** Sock Shop on a *separate* Railway service, with a toggle-able failure shim in front of one monitored route for live demos.
**Architecture enforcement:** `import-linter` (dependency-direction contracts) + a custom schema FK-direction check. These are CI gates and they ARE the Definition of Done floor.
**Testing:** pytest (backend, with canonical fixtures for the pure core). Frontend test runner chosen in Sprint 0.

**Tooling gaps to surface at planning:** frontend E2E (Playwright?) is not yet specced — raise when the frontend zone is planned. No live Dynatrace/Statuspage credentials are needed until the adapter zones; earlier zones use mocks/fakes against the canonical ports.

## 4. Hard Constraints (from the design — non-negotiable)

1. **The canonical boundary is sacred.** The core (`backend/src/core/`) never imports a vendor type, never imports an adapter. Vendor identifiers live only in provenance fields. Enforced by import-linter, not convention.
2. **Derive, don't store, verdicts.** Availability and status are computed from raw observations on read; verdicts are never persisted (avoids cache-drift). One exception path is *designed* but not built: a short-TTL cache may be added later **only if** measurement shows 30-day multi-location reads are slow.
3. **Availability is honest; status is stable.** The raw availability ratio is never smoothed. Anti-flap governs only displayed status, never the percentage. Two computations off the same observations, kept apart.
4. **Idempotent ingestion.** Unique `source_event_id`, watermark advances on accepted observations only, commit-before-advance. Single backend instance is the intent; idempotency is the safety net if a deploy overlap briefly runs two.
5. **Human-approved degradations.** A degradation becomes a *proposal*; a human approves it before it reaches the public page. Recoveries auto-publish. Proposals have supersession + auto-obsoletion so a stale approval never publishes a finished outage.
6. **Schema spine is one-directional.** A stable spine (topology → signals → decision → publication, components = hub); feature tables FK *into* the spine, the spine never FKs into features. Enforced by a CI FK-direction check.
7. **Auth is deliberately deferred** as a known pre-production gap. When added it is edge-only (controllers), zero core impact. Do not build it unless it becomes a story; do not let its absence block other work.

## 5. Slicing Decision: HORIZONTAL (by architectural zone)

**The PO has chosen horizontal slicing** — each zone built to completion before moving outward, rather than thin end-to-end threads. Build order follows the dependency direction inward-to-outward:

```
Sprint 0  → scaffold + CI contracts + harness   (the gates exist before any logic)
Zone 1    → canonical types + ports             (the boundary, pure, fully unit-tested)
Zone 2    → Neon schema + migrations + repos     (persistence behind repository ports)
Zone 3    → ingest adapter (Dynatrace → canonical)
Zone 4    → core pipeline (collapse→streak→anti-flap→decide) + availability calculator
Zone 5    → proposal lifecycle + publish adapter (Statuspage)
Zone 6    → API layer (five-file convention)
Zone 7    → frontend (six tabs, redesigned)
Integration → the deliberate "first end-to-end thread" story
```

**Consequence the PO has accepted and you must honor:** early reviews demo *proven layers* (passing tests, green contracts), not visible end-to-end behavior. The first showable thread is a *deliberate integration story*, not an accident. Therefore **every horizontal story's acceptance criteria must be mechanically checkable in isolation** — unit tests against canonical fixtures, contracts passing — so "done" is exit-code-provable without a visual demo. The architecture supports this: the core is pure and unit-testable, ports are mockable, zones test in isolation by design.

## 6. Proposed Definition of Done (for PO approval at inception)

See the companion `definition-of-done.md`. Its core is the architecture's own CI gates: **import-linter contracts pass, schema FK-direction check passes, pytest green, migrations apply cleanly on a fresh DB.** These are not generic — they are the mechanical enforcement of constraints 1 and 6 above. The boundary that the whole design rests on is *checked on every story*, from Sprint 0 onward — which is exactly what makes horizontal slicing safe here.

## 7. Proposed Working Agreements (for PO approval at inception)

- **The dossier is the spec.** Every subagent brief cites the relevant dossier section. Implementers build to the dossier + the story AC, never to chat history.
- **Boundary violations are build failures, not review comments.** If import-linter or the FK-direction check goes red, the story is not Done — no human override.
- **Pure core, mockable edges.** Core logic stories are tested with in-memory canonical fixtures; no story in zones 1–4 may require live Dynatrace/Statuspage/Neon to pass its tests (use fakes/mocks against the ports; real adapters are their own zones).
- **Measure before optimizing the read path.** The derive-on-read strategy ships as-is. No caching story is created until a measurement story demonstrates a real 30-day read problem.
- **Defer auth cleanly.** Auth's absence never blocks a story. CORS is restricted to the Vercel origin from the deployment story onward.

## 8. Backlog Drafts (refine into stories for PO approval)

> Estimates are rough placeholders for refinement — confirm/split at refinement. Any **8 must be split** before entering a sprint. `priority` follows the horizontal build order. Each maps to dossier sections.

### Sprint 0 — Setup
- **STORY-001** (chore, ~3) — *Repo scaffold + four-zone structure.* Create `backend/src/{core,adapters,composition,api}/` per dossier §4. Init git, detect default branch. pytest harness. CLAUDE.md (YourTeam pointer + stack + commands + tooling inventory). *AC: `pytest` runs (zero tests OK, exit 0); the four zones exist; CLAUDE.md present.*
- **STORY-002** (chore, ~3) — *CI contracts = the DoD floor.* Configure import-linter with the three contracts from dossier §4 (core-independence, core-internal-layering domain←ports←services, adapter-independence) and the schema FK-direction check from §9. *AC: `lint-imports` exits 0 on the empty skeleton; the FK-direction check script exists and exits 0; both wired into the DoD.*
- **STORY-003** (chore, ~2) — *Alembic + Neon two-connection setup.* Alembic initialized; migration command uses the DIRECT connection; app config reads the POOLED connection. An empty baseline migration applies cleanly to a fresh DB. *AC: `alembic upgrade head` exits 0 on a fresh database; app reads pooled URL, migration step reads direct URL.*

### Zone 1 — Canonical types + ports (dossier §5, §6)
- **STORY-004** (feature, ~3) — *Canonical `SignalObservation` type.* Health enum (up/down/degraded, closed), `observed_at` UTC, `source_event_id`, source provenance {system, native_id, native_kind}, location, optional latency_ms/raw_ref. Frozen, validated. *AC: type constructs/validates per §5; vendor id appears only in provenance; round-trip tests with canonical fixtures.*
- **STORY-005** (feature, ~3) — *The ports.* `SignalIngestPort`, `StatusPublisherPort`, repository ports, `ClockPort` — interfaces in `core/ports/`, signatures in canonical vocabulary only (a reader who's never heard of Dynatrace understands them). *AC: ports defined; import-linter confirms core imports no adapter/vendor; a fake implementation of each compiles against the interface.*

### Zone 2 — Schema + migrations + repositories (dossier §9)
- **STORY-006** (feature, ~5) — *Spine schema migration.* The three table groups (topology / signals / workflow) per §9 with timestamptz, JSONB, UNIQUE(source_event_id), composite index (signal_key, observed_at), partial unique index (one active proposal per component). *AC: migration applies to fresh DB exit 0; FK-direction check passes; indexes present.*
- **STORY-007** (feature, ~3) — *Repository adapters behind the ports.* Neon-backed implementations of the repository ports from STORY-005. *AC: repos implement the port interfaces; integration tests against a test DB; no SQL leaks above the repository layer.*

### Zone 3 — Ingest adapter (dossier §7, §8)
- **STORY-008** (feature, ~5) — *Dynatrace adapter + DQL normalization.* Query synthetic results via DQL, normalize to `SignalObservation`. Vendor specifics fully contained here. *AC: given recorded DQL responses (fixtures), produces correct canonical observations; lives entirely in adapters; core untouched.*
- **STORY-009** (feature, ~5) — *Pull loop with watermarks + validation gate.* Per-signal watermark, overlap window, validate→quarantine (rejected_observations), dedupe on source_event_id, advance watermark on accepted-only, commit-first. *AC per §8: invalid observations land in rejected_observations; watermark advances only on accepted; duplicate source_event_id is a no-op; crash mid-loop loses nothing (test by interrupting).*

### Zone 4 — Core pipeline + availability (dossier §10, §11)
- **STORY-010** (feature, ~5) — *Four-stage pipeline.* collapse → streak → anti-flap → decide, all pure, provider-blind, per-app config thresholds. *AC: each stage unit-tested with canonical fixtures per §10; maintenance excluded from streak; severity-ordered direction; produces proposals/auto-publish/nothing correctly.*
- **STORY-011** (feature, ~5) — *Availability calculator.* Two-grain math: availability over collapsed verdicts, completeness over raw observations with location-aware denominator (intervals × distinct_locations); min-of-children group rollup; skew flag surfaced; derive-on-read, no stored verdicts. *AC per §11: both metrics correct on fixtures; 3-location signal never exceeds 100% completeness; group = min of children; entry points shaped for a drop-in cache (but no cache built).*

### Zone 5 — Proposal lifecycle + publish (dossier §12)
- **STORY-012** (feature, ~5) — *Proposal lifecycle.* Supersession + auto-obsoletion, terminal states (superseded, obsoleted), one-active-proposal-per-component enforced by the partial unique index, collision = ON CONFLICT + debug log. *AC per §12: a worse proposal supersedes a pending lesser one; a recovering pending degradation is obsoleted not published; concurrent insert is safe.*
- **STORY-013** (feature, ~3) — *Statuspage publish adapter + commit-first boundary.* Real Statuspage publish behind `StatusPublisherPort`; commit DB first, best-effort publish in try/except with SLA-retry safety net. *AC: approved change publishes; a publish failure does not roll back the committed decision; mock publisher used in tests.*

### Zone 6 — API (dossier §13)
- **STORY-014** (feature, ~5) — *Five-file feature modules.* `api/v1/<feature>/` = __init__/controller/models/validation/service per §13; edge service thin (validate→core via composition→shape HTTP), no horizontal feature imports, canonical types stay in core. Endpoints for the six tabs' data + the decision endpoint. *AC: each feature follows the five-file shape; import-linter confirms no cross-feature imports; edge holds no business logic.*

### Zone 7 — Frontend (dossier §17, two-surface model)
- **STORY-015** (feature, ~5) — *Dashboard shell + six tabs (redesigned).* React/TS SPA, six tabs (Dashboard, Availability, Approvals, Check History, Maintenance, Publications) — same information architecture as V2, fresh visual design. Consumes the API from STORY-014. *AC: six tabs render against the API; approve/reject works on the Approvals tab; CORS restricted to the Vercel origin.* *(May split into shell + per-tab stories at refinement — likely an 8.)*

### Integration + Deployment
- **STORY-016** (feature, ~5) — *First end-to-end thread.* The deliberate integration story: one Dynatrace monitor → pull loop → canonical observation → pipeline → proposal → approval → Statuspage, running live. This is the first *demoable* thread. *AC: a forced failure via the shim produces a proposal that, once approved, publishes to Statuspage — observed end to end.*
- **STORY-017** (chore, ~3) — *Deployment topology.* Backend on Railway (single instance, migrations as release step), frontend on Vercel, Sock Shop on Railway service #2 + failure shim, secrets in Railway env, tuned demo cadence. *AC per §17: a push deploys via the migrate-release-then-serve flow; a failed migration halts the deploy; the demo thread runs on deployed infra.*

> **Deferred (do NOT create as stories until the PO asks):** auth (constraint 7), the read-path cache (working agreement: measure first), and all Tier-3 contracts from dossier §16 (ProblemSignal→incident, status-vs-problem reconciliation, Dynatrace maintenance ingestion, intra-core call-graph linting, completeness option-C, per-app notification routing, guaranteed-delivery outbox, pull-loop liveness). They are isolated by design and entangle nothing.

---

## 9. Handoff Notes

- This seed pairs with **`uptime-monitor-v3-design.html`** (the architecture dossier, 18 sections) and **`definition-of-done.md`** (the stack DoD). Keep all three in the repo; the dossier is the spec every story points back to.
- At inception, present the backlog above + the DoD + the working agreements for PO approval, then run Sprint 0 (STORY-001..003). Sprint 0 ends, as always, with a normal review: a running skeleton with the CI contracts green on an empty build.
- The first sprint with velocity history should commit to measured capacity; with none yet, deliberately under-commit (the skill's rule).
- If anything here conflicts with an existing CLAUDE.md/AGENTS.md in the repo, run the skill's mandatory conflict scan — PO content wins, append never modify.
