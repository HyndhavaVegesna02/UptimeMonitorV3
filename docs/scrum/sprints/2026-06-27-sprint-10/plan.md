# Sprint 10 — Plan (implemented externally by the PO / Gemini)

**Goal:** Close out Zone 4 — the pipeline's final stage, `decide` (STORY-024): compare anti-flap's
proposed status to the component's current published status and reconcile open proposals (§10 + §12).
Plus three 1-pt cosmetic cleanups carried from recent retros/reviews.

**Branch:** `sprint-10` · **Start tag:** `sprint-10-start` · **Started:** 2026-06-27
**Capacity:** 6 · **Committed:** 6 (STORY-024 = 3, STORY-029 = 1, STORY-027 = 1, STORY-030 = 1)
**Order:** STORY-024 first (headline, highest blast radius, full review pipeline), then STORY-029
(core-domain adjacent — momentum), STORY-027 (test tidy), STORY-030 (tooling). The 1-pt chores are
independent of decide and of each other; their order is by priority only.

## How this sprint runs (workflow — working-agreements.md 2026-06-26)
The PO implements these stories externally (Antigravity / Gemini), committing onto `sprint-10`. Build
to the AC + the TDD steps below — this plan is the contract (there is no implementer-subagent brief).
Then the PO tells the orchestrator "do your review", and the orchestrator diffs `sprint-10-start..HEAD`,
runs the full DoD gate itself + (for the 3-pt story) spec + quality reviewers (Opus) + the wiki blast
radius + review/retro/merge.

**A story is Done only when ALL FOUR DoD commands exit 0** (and, for STORY-024 at 3 pts, both reviews
pass):
- `.venv/Scripts/python.exe -m pytest` → 0
- `.venv/Scripts/lint-imports.exe` → 0 (`3 kept, 0 broken`)
- `.venv/Scripts/python.exe scripts/check_fk_direction.py` → 0  (DB-gated)
- `.venv/Scripts/alembic.exe upgrade head` → 0  (DB-gated; **NO new migration this sprint**)

DB-gated commands need a throwaway Postgres: `.venv/Scripts/python.exe scripts/dev_db.py up` (prints
two `export DATABASE_URL...` lines; `down` to tear down). Requires Docker Desktop running. (STORY-030
in THIS sprint makes `up` self-heal a leftover container; until it lands, if `up` errors "port 55432
address already in use", run `docker rm -f uptime_pg_pytest` then retry.)

**Standing working agreements (all apply):** boundary = build failure (`lint-imports` 3 kept); pure
core / mockable edges (in-memory fakes for unit tests — `decide` is pure core, NO DB needed for its
tests); **empty-input behavior tested**; **range/boundary tested** (non-aligned cases); **frozen
value/result types MUST enforce cross-field coherence invariants with a `model_validator(mode="after")`
+ a test**; **when the plan specifies a port/repository method, the edge/error behavior is explicit**
(below); **a port's fake and its real adapter must agree on edge-case behavior**; **every wiki Fact's
cited file must be in the article's `code_refs`**; scoped staging (never `git add -A`); commit per green
TDD step; CLAUDE.md only if a command/stack changes (none expected this sprint).

**Baseline at lock:** all gates green on main @ `299925b` — `pytest` 264 passed (with DB), `lint-imports`
3 kept / 0 broken.

---

## STORY-024 — Core pipeline stage 4: decide (3 pts)

Spec: dossier **§10 stage 4** ("Compare proposed status to the component's current published status.
Same → nothing. Worse → a degradation proposal (the human-approval gate). Better → a recovery
(auto-publishes). This stage also reconciles open proposals") + **§12 the reconciliation rule**.
Story file: `docs/scrum/stories/STORY-024-core-pipeline-antiflap-decide.md` (read it — the open
"current published status read" seam is RESOLVED below).

**Design decisions made at refinement (build to these):**
1. **`decide` is a core SERVICE with injected ports**, mirroring `IngestService`
   (`backend/src/core/services/ingest_service.py`). Put it in a new module
   `backend/src/core/services/decide.py`. It imports ONLY `src.core.*` (domain + ports) — no SQL, no
   vendor types, no I/O. `lint-imports` stays green (it's core).
2. **The "current published status" is `components.status`** — the single current-status column
   (`publications` is the append-only audit log, NOT the read source). `decide` does **not** get a new
   read port this sprint: `current_status: ComponentStatus` is passed in as an **injected parameter**
   (precedent: `collapse`'s `under_maintenance`, `anti_flap`'s `thresholds`). The composition layer /
   first end-to-end thread (STORY-016) will read `components.status` and supply it. This keeps the
   story to the two ports it names.
3. `decide` **consumes** `ProposalRepository` (`get_open` / `create_open` / `resolve`) for the §12
   reconciliation and `StatusPublisherPort` (`publish`) for the recovery auto-publish — both injected
   via the constructor. Reuse the existing `FakeProposalRepository` and `RecordingStatusPublisher` in
   `backend/tests/fakes.py` for the unit tests (no DB).
4. **Updating `components.status` and writing a `publications` row are OUT OF SCOPE** (no port for them
   here) — that persistence is the end-to-end wiring of STORY-016. `decide`'s publish responsibility is
   exactly: call `StatusPublisherPort.publish(StatusChange(...))`.

**Read first:** `backend/src/core/services/ingest_service.py` (the injected-ports core-service style),
`backend/src/core/services/pipeline.py` (stages 1–3; `AntiFlapOutcome` is decide's upstream),
`backend/src/core/domain/status.py` (`ComponentStatus`, `StatusChange`),
`backend/src/core/domain/proposal.py` (`StatusProposal`, `ProposalState`),
`backend/src/core/ports/proposal_repository.py` + `status_publisher.py` (the two ports),
`backend/tests/fakes.py` (`FakeProposalRepository`, `RecordingStatusPublisher`).

### Severity & the two comparisons
Severity rank: `operational(0) < degraded(1) < partial_outage(2) < major_outage(3)`. A status is a
"degradation" relative to another when its rank is strictly higher. Add a small helper in
`core/domain/status.py` (e.g. a `STATUS_SEVERITY: dict[ComponentStatus, int]` plus a tiny
`is_worse(a, b)` / `severity_rank(s)` — your call, keep it minimal and exported). It is a pure mapping
over a closed enum, so no coherence validator is needed; but it MUST be exhaustive over all four
members (a test asserts every `ComponentStatus` has a rank).

`decide(*, component_id, proposed_status, current_status, now, reason=None)` runs (commit-first —
repo writes happen BEFORE the publish, so a publish failure never loses the decision):

```
open = proposal_repo.get_open(component_id)
proposed_is_degradation = rank[proposed_status] > rank[current_status]

# decide what (if anything) to publish — §10 "better → recovery auto-publishes":
publish_change = StatusChange(component_id, proposed_status) if rank[proposed_status] < rank[current_status] else None

# §12 reconciliation of the single open proposal (commit-first DB writes):
if proposed_is_degradation:
    if open is None:
        proposal_repo.create_open(StatusProposal(component_id, from_status=current_status,
                                                 to_status=proposed_status, state=OPEN, proposed_at=now))
    elif open.to_status != proposed_status:
        proposal_repo.resolve(open.id, to_state=SUPERSEDED, reason=reason, resolved_at=now)
        proposal_repo.create_open(StatusProposal(... to_status=proposed_status, state=OPEN, proposed_at=now))
    else:                       # open.to_status == proposed_status → §12 "Same → leave it"
        pass
else:                          # proposed is operational-or-equal vs published → no human gate
    if open is not None:
        proposal_repo.resolve(open.id, to_state=OBSOLETED, reason=reason, resolved_at=now)  # §12 "Recovered → obsoleted, nothing published"

# best-effort publish AFTER the commit:
if publish_change is not None:
    publisher.publish(publish_change)
```

**Why two comparisons:** §10 compares proposed vs the **current published** status to decide the
publish (only a recovery that improves the *published* status auto-publishes). §12 compares the freshly
computed status vs the **open proposal** to keep exactly one open proposal that reflects the current
worst — and a pending degradation that recovers is *obsoleted with nothing published* (the customer
was never shown the outage; §12 line 965). The two never conflict: a published degradation has no open
proposal (it was approved → terminal), so the "obsolete the pending" and "publish a recovery" branches
are mutually exclusive in practice.

**Return value:** `decide` returns a `DecideAction(str, Enum)` describing the primary outcome —
`NOOP`, `PROPOSED`, `SUPERSEDED`, `OBSOLETED`, `PUBLISHED_RECOVERY` — so the pull loop (STORY-016) can
log it and tests assert on the return rather than poking fake internals. Single-field enum → no
coherence validator needed. (Tests still also assert the side-effects via the fakes.)

**Edge/error behavior (explicit, per the working agreement):**
- `proposed_status == current_status` and no open proposal → `NOOP`, nothing published, no repo write.
- `create_open` returning `None` (the partial-unique safety net fired — a concurrent open exists):
  treat as a benign no-op (do not crash); a `get_open`-then-`create_open` race is the documented
  `ON CONFLICT DO NOTHING` path (§12). Note it; the single-threaded pull loop won't hit it.
- `resolve` raises if the proposal is not open (per the port contract / fake) — decide only ever calls
  `resolve` on the `open` it just fetched, so this should not fire; do not pre-empt it with a guard.
- A `publisher.publish` failure propagates AFTER the repo writes are committed (no rollback — this IS
  the "commit-then-best-effort" guarantee; the composition's `publish_best_effort` from STORY-013 is
  what swallows it in the real wiring). A test asserts the repo write happened before the publish raise.

### TDD steps (commit after every green step)
- [ ] 1. Domain severity helper in `core/domain/status.py` (`STATUS_SEVERITY` + minimal
        `severity_rank`/`is_worse`), exported from `core/domain/__init__.py`. Failing test: every
        `ComponentStatus` has a rank; ordering operational<degraded<partial_outage<major_outage.
        Implement. `lint-imports` green. Commit.
- [ ] 2. `DecideAction(str, Enum)` (NOOP/PROPOSED/SUPERSEDED/OBSOLETED/PUBLISHED_RECOVERY) in
        `core/services/decide.py`. Failing test importing it. Commit. (small; can fold into step 3)
- [ ] 3. `DecideService(*, proposal_repo, publisher)` skeleton + the **same → NOOP** case. Failing test:
        proposed==current, no open proposal → returns `NOOP`, `RecordingStatusPublisher.published`
        empty, `FakeProposalRepository.proposals` empty. Implement minimal. Commit. (AC1)
- [ ] 4. **Worse, no open proposal** → `create_open` a degradation, NO publish, returns `PROPOSED`.
        Failing test (e.g. operational→major_outage): one open proposal persisted with
        from=operational/to=major_outage/OPEN, nothing published. Implement. Commit. (AC1)
- [ ] 5. **Worse, open proposal exists** → supersede-and-create when `to_status` differs; **leave**
        when equal. Failing tests: (a) open=degraded, proposed=major → old resolved SUPERSEDED + new
        open major, returns `SUPERSEDED`, one open proposal (invariant); (b) open=major, proposed=major
        → unchanged, returns `NOOP`/leave, still exactly one open. Implement. Commit. (AC2)
- [ ] 6. **Better / recovery.** (a) published=major_outage, proposed=operational, no open → publish
        `StatusChange(component_id, operational)`, returns `PUBLISHED_RECOVERY`. (b) published=operational,
        an open=major pending, proposed=operational → resolve(OBSOLETED), **nothing published**, returns
        `OBSOLETED` (§12 "recovered → obsoleted, nothing published"). Failing tests for both. Implement.
        Commit. (AC1/AC2)
- [ ] 7. **Commit-first / publish failure.** Failing test: a publisher whose `publish` raises, on a
        recovery that also resolves an open proposal — assert the repo write is committed (the proposal
        is resolved in the fake) BEFORE the exception propagates. Implement ordering. Commit. (AC2/§12)
- [ ] 8. Self-review: `decide.py` imports only `src.core.*`; ports injected; tests use the existing
        fakes (no DB). `lint-imports` green. Commit.
- [ ] 9. DoD gate (all four exit 0). Forward blast radius: update
        `docs/scrum/wiki/core-pipeline-and-availability.md` (decide joins collapse/streak/anti_flap —
        add Facts + extend `code_refs` to include `core/services/decide.py`; bump `verified_sha`) and
        `docs/scrum/wiki/canonical-types-and-ports.md` (the severity helper + `StatusChange` use —
        ensure `status.py` is a code_ref; bump `verified_sha`). Every new Fact's cited file MUST be in
        that article's `code_refs`. Commit.

---

## STORY-029 — Audit frozen value/result types for unenforced coherence invariants (1 pt)

Story file: `docs/scrum/stories/STORY-029-value-type-coherence-audit.md` (AC verbatim there).
Bounded audit of EVERY frozen Pydantic value/result type under `backend/src/core/` (domain + services)
for a cross-field coherence invariant that is documented-but-unenforced. Already-enforced (do not
touch, use as the pattern): `Verdict` (maintenance↔health), `AntiFlapOutcome` (status↔warning),
`SkewResult` (skewed↔lagging_signals), `StatusProposal` (resolved_at↔terminal-state). NOTE: STORY-024
in THIS sprint adds a severity helper + `DecideAction` enum — include them in the audit (the enum has
no cross-field invariant; confirm and record that).

### TDD steps
- [ ] 1. Enumerate every frozen type under `backend/src/core/` (grep `model_config = ConfigDict(frozen=True)`
        / `BaseModel`). For each, record in the story file: fields, whether a cross-field invariant
        exists, and whether it's enforced. Commit (story-file edit only).
- [ ] 2. For any type with an UNENFORCED invariant: add a `model_validator(mode="after")` that raises a
        clear `ValueError` on the incoherent shape + a test covering BOTH the rejected and the valid
        shapes (mirror `Verdict`/`AntiFlapOutcome`). If NONE found, record "no further gaps" with the
        audited list — that is a valid outcome (AC2). Commit per type fixed (or one doc commit if none).
- [ ] 3. DoD gate (all four exit 0). Blast radius: if a validator was added to a domain type, re-verify
        the relevant wiki article (`canonical-types-and-ports.md` / `core-pipeline-and-availability.md`)
        and bump `verified_sha`; if audit-only (no code change), no wiki impact. Commit.

---

## STORY-027 — Hoist the lazy AvailabilityCalculator import in test_availability.py (1 pt)

Story file: `docs/scrum/stories/STORY-027-test-availability-import-cleanup.md`. Test-only, near-trivial:
in `backend/tests/test_availability.py`, move the in-function lazy `AvailabilityCalculator` import to
module top alongside `AvailabilityResult` / `rollup_group`; remove the lazy import. Nothing under
`src/` is touched.

### TDD steps
- [ ] 1. Hoist the import to module top; delete the in-function import. Run `pytest` (availability tests
        pass unchanged) + `lint-imports` (green). Commit.
- [ ] 2. DoD gate (all four exit 0). No `src/` change → no wiki blast radius. Commit (if not already).

---

## STORY-030 — Make dev_db.py up idempotent against a leftover container (1 pt)

Story file: `docs/scrum/stories/STORY-030-dev-db-up-idempotent.md`. Tooling fix in `scripts/dev_db.py`:
`up` must `docker rm -f <name>` its OWN target container (ignoring "no such container") BEFORE
`docker run`, so a leftover/stuck same-named container no longer blocks startup. Only force-remove the
helper's own container name — a real port conflict from a DIFFERENT process still surfaces a clear
error (AC3).

### TDD steps
- [ ] 1. Add the pre-clean step in `up` (force-remove own named container, tolerate absence) before
        `docker run`. If `dev_db.py` has unit-testable helpers, add a test for the pre-clean; otherwise
        verify manually (start; leave a stuck container; `up` succeeds; `down` cleans) and record the
        manual check in the story file (AC4). Commit.
- [ ] 2. Confirm idempotency: `up` when a healthy container already runs → recreates cleanly, ends with
        a migrated DB + the two printed URLs (AC2); `down` still removes cleanly (AC3). Commit if changed.
- [ ] 3. DoD gate (all four exit 0 — this story's change is exercised by the DB-gated commands using
        `dev_db.py`). Blast radius: `dev-setup-and-dod.md` describes `dev_db.py` — re-verify its Facts
        and bump `verified_sha` if the documented behavior changed. Commit.

---

## Reviews (orchestrator, after the PO says "do your review")
- STORY-024 (3 pts → full pipeline): spec reviewer (Opus) vs the AC verbatim, then code-quality
  reviewer (Opus), then the mechanical DoD gate re-run by the orchestrator.
- STORY-029 / 027 / 030 (1 pt each → gate only): mechanical DoD gate (no LLM reviewers).
- Fix-loop findings (CRITICAL/MAJOR) route back to the PO/Gemini to fix and re-trigger the review by
  default; the orchestrator fixes a trivial finding inline only if the PO asks.
