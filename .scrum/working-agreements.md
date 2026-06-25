# Working Agreements
# Append-only. Each entry: date, the agreement, and the incident that motivated it.
# These bind every session and every subagent brief.
# Team-proposed amendments enter only via retro with PO approval.
# PO-stated rules (coding style, conventions, process preferences) are appended
# IMMEDIATELY whenever the PO states them — the PO never waits for a ceremony.
# PO-stated rules outrank observed codebase patterns wherever they conflict.

## Defaults (active from inception)
- 2026-01-01 — Execution pipeline: stories of 1-2 points use implementer + DoD gate;
  3+ points use implementer + spec reviewer + quality reviewer + DoD gate.
  The DoD gate is never skipped at any size. (Default)
- 2026-01-01 — Effort cap: a story exceeding 3x its estimate in attempts is
  auto-Blocked with a summary of what was tried. (Default)
- 2026-01-01 — An 8-point story must be split during refinement; it may never
  enter a sprint. (Default)
- 2026-01-01 — Tooling (MCP servers, CLIs) may only change at sprint planning or
  retro; mid-sprint the environment is frozen like scope. (Default)
- 2026-01-01 — One active session: honor .scrum/session.lock; a second session
  runs read-only. (Default)

## PO-stated rules (added during work — binding immediately)
- 2026-06-24 — **Subagent model assignment is mandatory.** Implementation/implementer
  subagents MUST be dispatched on the **Sonnet** model (`model: "sonnet"`); reviewer
  subagents (spec-compliance AND code-quality) MUST be dispatched on the **Opus** model
  (`model: "opus"`). This applies to every Agent dispatch in the YourTeam pipeline, every
  story size. Not negotiable, no per-story override. (PO directive, 2026-06-24.)

## PO working agreements (locked at inception, 2026-06-23 — from YOURTEAM_INCEPTION.md §7)
- 2026-06-23 — **The dossier is the spec.** Every subagent brief cites the relevant
  section of `uptime-monitor-v3-design.html`. Implementers build to the dossier + the
  story AC, never to chat history.
- 2026-06-23 — **Boundary violations are build failures, not review comments.** If
  `lint-imports` (import-linter) or the schema FK-direction check goes red, the story
  is NOT Done — no human override, at any story size.
- 2026-06-23 — **Pure core, mockable edges.** No story in zones 1–4 may require live
  Dynatrace / Statuspage / Neon to pass its tests. Core logic is tested with in-memory
  canonical fixtures; ports are mocked/faked. Real adapters are their own zones and use
  recorded fixtures + a throwaway test database.
- 2026-06-23 — **Measure before optimizing the read path.** The derive-on-read strategy
  ships as-is; availability/status are never persisted. No caching story is created until
  a measurement story demonstrates a real 30-day multi-location read problem.
- 2026-06-23 — **Defer auth cleanly.** Auth's absence never blocks a story. From the
  deployment story onward, CORS is restricted to the Vercel origin (+ localhost for dev).

## Amendments
- 2026-06-23 — **Command-sync in the brief.** Any story that adds, removes, or changes a
  DoD / build / test / run command MUST carry an explicit "update CLAUDE.md in the same
  commit" step in the implementer brief and is checked at the DoD gate. (Motivated by
  Sprint 0, STORY-002: it made `lint-imports` + the FK-check real DoD commands, but the brief
  omitted the doc sync, so CLAUDE.md said they "arrive in later stories" until a manual patch.)
- 2026-06-23 — **Single canonical Definition of Done.** `.scrum/definition-of-done.md` is the
  sole source of truth the gate runner reads; the root `definition-of-done.md` is reduced to a
  one-line pointer to it. No second editable copy. (Motivated by Sprint 0, STORY-003: the
  implementer flagged two DoD files as a drift risk.)
- 2026-06-24 — **Clean tree at dispatch; scoped staging.** The orchestrator commits any
  board/state edit (`.scrum/sprint-current.yaml`, board transitions) BEFORE dispatching an
  implementer, so the working tree is clean at dispatch. Implementers stage only the files
  they created/changed for the step — never `git add -A`. (Motivated by Sprint 1, STORY-004:
  the orchestrator's uncommitted board→in-progress edit was swept by the implementer's
  `git add -A` into code commit abeb448, putting a state change inside a story commit.)
- 2026-06-24 — **DB-gated work uses the shared throwaway-DB harness.** Once STORY-019 lands,
  every DB-gated story (migrations, repositories, schema checks) and reviewer/gate run uses
  the shared helper + pytest fixture to obtain a migrated throwaway Postgres — no hand-rolled
  `docker run` + `alembic upgrade head` + URL-export sequence in individual briefs. Until then,
  DB-gated briefs must still carry the explicit migrate-first sequence and the two-URL dialect
  split. (Motivated by Sprint 2: the throwaway-Postgres setup was hand-rolled FIVE separate
  times — across the STORY-006/018 implementers, the spec reviewer, and the orchestrator DoD
  gates — each re-implementing the `DATABASE_URL` plain-libpq vs `DATABASE_URL_DIRECT`
  `+psycopg` dialect split, a standing foot-gun. Every remaining Zone 2–4 story is DB-heavy.)
- 2026-06-25 — **Fix loops use a fresh agent; verify the tree after any agent crash.** For a
  fix loop (or any continuation) where the original agent's transcript is already large, dispatch
  a FRESH subagent with a focused brief stating the current committed state + the specific
  remaining work — do NOT repeatedly resume the large-transcript agent. After ANY agent crash or
  abnormal stop, the orchestrator inspects the working tree before proceeding: preserve coherent
  committed/uncommitted work, discard scraps (last green commit is truth), and clean leaked
  artifacts (e.g. temp test files written into `backend/tests/`). (Motivated by Sprint 3,
  STORY-019: resuming the implementer for its fix loop crashed twice with
  `API Error: Connection closed mid-response` — an artifact of a large transcript producing a
  long response — leaving uncommitted work and a leaked `test_zz_*.py` in the tests dir; a fresh
  tight-brief implementer then finished first try.)
- 2026-06-25 — **Resource-lifecycle stories require teardown-on-failure in the brief.** Any story
  that creates an external resource (Docker container, temp file, network connection, subprocess)
  MUST have its implementer brief explicitly require teardown on EVERY failure path — including a
  failure partway through setup, before any caller finalizer is established — plus a regression
  test proving no resource leaks on that path. (Motivated by Sprint 3, STORY-019: a MAJOR review
  finding — `resolve_db()` could raise after `start_container` created the container but before
  the fixture's `try/finally` registered, leaking a uniquely-named container with nothing to
  reclaim it. The implementer brief had described the lifecycle but not demanded teardown on
  partial-setup failure.)
<!-- - YYYY-MM-DD — <agreement> (Motivated by: <incident, sprint, story>) -->
