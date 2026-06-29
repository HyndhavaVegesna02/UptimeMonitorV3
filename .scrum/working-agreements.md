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
- 2026-06-28 — **Every sprint lock produces an implementer prompt as a standard deliverable.**
  When the orchestrator locks a sprint (immediately AFTER writing `plan.md`), it ALSO generates —
  WITHOUT being asked — a single self-contained, copy-pasteable prompt the PO hands to the external
  implementer agent (Antigravity / Gemini). The prompt MUST: (a) point to `plan.md` as the
  step-by-step contract + the story files + the dossier (build to those, never to chat history);
  (b) state the branch, the execution order, the TDD + commit-after-green + scoped-staging cadence,
  and the six-command DoD gate; (c) **feed in the binding working agreements relevant to that
  sprint's code** — distilled to what actually applies, explicitly flagging any that are N/A this
  sprint — because under external implementation (2026-06-26) there is no implementer-subagent brief
  to carry them; (d) end with the guardrails: do NOT write `.scrum/` board state, do NOT run the
  review/reviewers/merge, stop-and-report on genuine ambiguity or a 3x effort overrun. The prompt is
  emitted as part of the lock turn, alongside the "Sprint N is locked" announcement. (PO directive,
  2026-06-28 — the accumulated working agreements must reach the external implementer somehow; the
  lock prompt is that vehicle, so it cannot depend on the PO remembering to ask.)

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
- 2026-06-25 — **Parallel-shape stories carry a "share the assembly" instruction.** When a
  story implements N variants that flatten to the SAME output shape (per-type normalizers,
  per-X handlers, per-format parsers), the implementer brief MUST direct factoring the common
  assembly into one shared helper from the start — only the genuinely per-variant logic lives
  in each variant. This is checked by the quality reviewer. (Motivated by Sprint 4, STORY-008:
  the HTTP and clickpath normalizers copy-pasted the identical timestamp-parse +
  SignalObservation/Provenance assembly, differing only in native_kind; the quality reviewer
  raised it as a MAJOR ("duplication of logic that will drift") and it cost a full fix-loop
  dispatch to extract `_assembly.assemble_observation` — predictable from the story shape and
  preventable by the brief.)
- 2026-06-25 — **Implementers never write sprint board state.** Implementers report DoD
  evidence, blast-radius resolution, and review-relevant findings in their FINAL MESSAGE only;
  the orchestrator is the sole writer of `.scrum/sprint-current.yaml` (dod_evidence, board
  transitions, review verdicts). An implementer editing the board is treated like any other
  out-of-scope change. (Motivated by Sprint 4, STORY-008: the implementer rewrote the
  `dod_evidence` block of `sprint-current.yaml` in a non-standard free-string format and set
  `blast_radius_resolved`/`paused_at_commit` itself, which the orchestrator then had to reconcile
  back to the structured schema — board state is the orchestrator's ledger, not the implementer's.)
- 2026-06-25 — **A wiki article's `code_refs` are the files that DEFINE its subject, not every
  file its subject touches.** An article must not carry an over-broad directory `code_ref` (e.g.
  `backend/src/`) when its Facts describe a stable contract/structure, because the mechanical
  staleness check then flags it on every unrelated in-zone change, forcing a no-op rehab each
  sprint. Scope `code_refs` to the defining files; let detailed in-zone facts live in their own
  narrower articles. (Motivated by Sprint 4 AND Sprint 5: `architecture-boundary.md` went stale
  both sprints purely because its `code_refs` listed all of `backend/src/`, even though its Facts —
  the four-zone tree, the three import-linter contracts, the FK-direction boundary — never changed;
  its `code_refs` were re-scoped to `pyproject.toml` + `scripts/check_fk_direction.py` + the four
  zone-root `__init__.py` files, so it now goes stale only when the boundary itself changes.)
- 2026-06-25 — **The orchestrator may finish a trivial interrupted tail directly instead of
  re-dispatching.** When an implementer subagent is interrupted (crash, connection drop, session
  limit) leaving only a trivial remainder AND a committed failing test already pins the contract
  for that remainder, the orchestrator may complete it directly — after the usual verify-the-tree
  step (preserve coherent committed/uncommitted work, discard scraps) — rather than burn a fresh
  dispatch. The completion must be recorded in the story's plan/board note, and the full DoD gate
  (plus reviewers, if the story's size requires them) still applies unchanged. For anything beyond
  a trivial tail, the fresh-agent rule stands. (Motivated by Sprint 5, STORY-020: the implementer
  subagent hit a session limit after committing step 1 + the shared error helper, leaving a
  coherent uncommitted step-2 test that only lacked an `import re`; the orchestrator fixed the
  import and routed the four required fields through `require_field` — a ~4-line completion — rather
  than re-dispatch a fresh agent for it.)
- 2026-06-25 — **A function over a collection must define and TEST its empty-input behavior.**
  Any function taking a list/sequence/iterable must have an explicit, tested answer for the empty
  case — either raise a clear DOMAIN error (not a leaked stdlib message) or return a documented
  default (e.g. `None`/empty). The empty-input test is part of the story's tests; its absence is a
  review finding. (Motivated by Sprint 6, STORY-010: `collapse([])` ran `max(...)` on an empty
  generator and leaked `ValueError: max() iterable argument is empty` — a stdlib message about
  iterables, not a domain statement — while its sibling `streak([])` already returned `None`
  cleanly. The asymmetry was the tell; the quality reviewer raised it as a MAJOR and it cost a
  fix-loop dispatch to add a guard + test that should have shipped with the function.)
- 2026-06-25 — **Every wiki Fact's cited file must be covered by the article's `code_refs`.** A
  Fact that cites `file:line` (or a file) NOT listed in the article's `code_refs` is forbidden — the
  staleness check (`git diff verified_sha..HEAD -- <code_refs>`) would never flag that Fact when its
  code changes, so it can silently rot (the "trusted-and-wrong" failure the wiki invariant exists to
  prevent). At the forward-blast-radius/DoD step AND the sprint-end compile pass, check that every
  file a Fact addresses is in `code_refs`; if not, either extend `code_refs` or split the article so
  each article's Facts are fully covered. (Motivated by Sprint 7: `canonical-types-and-ports.md` had
  grown to document `core/services/pipeline.py`'s `collapse`/`streak` Facts, but `pipeline.py` was
  never in its `code_refs` — those Facts were uncovered by the staleness check for TWO sprints
  (STORY-010 through STORY-011) until the compile pass extracted [[core-pipeline-and-availability]].)
- 2026-06-25 — **Range/window math must test a NON-aligned boundary case, not just clean inputs.**
  Any computation over a window / range / interval / cadence must include a test where the inputs do
  NOT divide evenly (e.g. a window that is not an integer multiple of the interval, an off-by-one
  span, a partial trailing bucket) — in addition to the empty-input test the existing agreement
  requires. Clean/divisible-only test suites hide boundary bugs. (Motivated by Sprint 7, STORY-011:
  cycle bucketing used FLOOR `expected_cycles`, but `in_window` returns observations in the partial
  tail of a non-divisible window; every test used an exact-multiple window, so a quality-review
  CRITICAL — `gap_verdicts` going negative / completeness >100% on a realistic "last 24h from now"
  window — slipped all the way to review and cost a fix-loop dispatch.)
- 2026-06-26 — **A frozen value/result type with a cross-field coherence invariant must ENFORCE it
  at construction, when the type is created.** If a type's fields carry an invariant — mutually-
  exclusive fields, a boolean that must agree with a payload (`flag == bool(items)`), an `Optional`
  that must be set/unset based on another field — add a Pydantic `model_validator(mode="after")`
  that rejects the incoherent shapes (raise a clear `ValueError`) plus a test covering BOTH the
  rejected and the valid shapes, in the SAME story that introduces the type. The implementer brief
  must call this out for any new value/result type (not just the reviewer brief). A documented-but-
  unenforced invariant is a quality-review finding. (Motivated by THREE consecutive sprints of the
  identical MAJOR: `Verdict` (STORY-025, maintenance↔health-is-None), `AntiFlapOutcome` (STORY-028,
  `not(proposed_status and internal_warning)`), `SkewResult` (STORY-026, `skewed == bool(lagging_signals)`)
  — each documented the invariant in its docstring but left it unenforced, and each cost a fix-loop
  dispatch to add the validator after the fact. STORY-029 audits existing types for the same gap.)
- 2026-06-26 — **External implementation: from Sprint 9 on, the PO implements the plan (Antigravity
  / Gemini); the orchestrator does NOT dispatch implementer subagents.** Division of labor: the
  orchestrator still runs standup → refinement → planning → lock (creates the `sprint-N` branch +
  start tag, writes `sprint-current.yaml` + a DETAILED `plan.md` whose per-story TDD steps + AC are
  the contract). The PO then implements externally, committing onto the sprint branch. The PO
  triggers the back half by saying "do your review"; the orchestrator then diffs `sprint-N-start..HEAD`,
  runs the FULL mechanical DoD gate itself, runs the spec + quality reviewers (Opus), resolves the
  wiki forward-blast-radius, and runs review/verdict/merge/retro. The mechanical floor is UNCHANGED
  and non-negotiable: a story is Done only when all four DoD commands exit 0 AND both reviews pass —
  regardless of who wrote the code. Fix-loop findings (CRITICAL/MAJOR) route BACK to the PO/Gemini to
  fix and re-trigger the review by default; the orchestrator may fix a trivial finding inline only if
  the PO asks. `plan.md` must therefore be self-contained (signatures, file locations, conventions,
  DoD) since there is no implementer-subagent brief. (Motivated by a PO token-budget constraint,
  2026-06-26 — the orchestrator's review/ceremony role is preserved; only the implement step moves
  out-of-process.)
- 2026-06-26 — **A port's in-memory fake and its real adapter must AGREE on edge-case behavior.**
  When a core port has both a test fake and a real (e.g. Postgres) adapter, they must behave
  identically on the edge cases — not-found, conflict, invalid-state, empty — i.e. both raise (the
  same kind of error) or both return the same sentinel. Verify it by running the SAME contract test
  against both implementations (a fake more lenient than the adapter, or vice-versa, gives false
  confidence — a fake-backed unit test passes while the real adapter misbehaves). (Motivated by
  Sprint 9, STORY-012: `PostgresProposalRepository.resolve` silently no-oped on an unknown / already-
  terminal proposal while `FakeProposalRepository.resolve` RAISED — so the fake-backed tests couldn't
  catch the adapter's silent-success bug; the quality reviewer caught it instead. The fix made both
  raise and added DB-gated tests for the edges.)
- 2026-06-26 — **When the plan specifies a port/repository method, it must state the edge/error
  behavior explicitly.** Each method's `plan.md` / story-AC description must say what happens on
  not-found, wrong-state, conflict, and empty input (raise which error vs return what) — not just the
  happy path. This matters most now that implementation is external (the PO/Gemini builds LITERALLY to
  the plan): an under-specified edge becomes a silent bug. (Motivated by Sprint 9, STORY-012: the plan
  said `resolve` "moves an open proposal to a terminal state" without "raise if it is not open" — so
  the implementer wrote a guard-less `UPDATE ... WHERE id=:id`. Pairs with the fake/adapter-parity
  agreement above.)
- 2026-06-27 — **Under external implementation, plan.md carries a self-contained CONVENTIONS
  CHECKLIST.** Because plan.md is the ONLY contract the external implementer (PO/Gemini) builds to —
  there is no implementer-subagent brief carrying the working agreements + wiki conventions — every
  sprint plan MUST include a standing conventions checklist that all new code is held to at quality
  review, and any per-story step that introduces a NEW module / public class / public function must
  name the docstring deliverable explicitly. The checklist: (a) **module + public class/function
  docstrings citing the relevant dossier §**, mirroring the peer modules (`ingest_service.py`,
  `pipeline.py`, `status.py`, `proposal.py`); (b) frozen value/result types enforce cross-field
  coherence invariants with a `model_validator(mode="after")` + test; (c) empty-input AND non-aligned
  boundary tests where applicable; (d) scoped staging (never `git add -A`); (e) follow existing
  import/naming/structure patterns rather than introducing a new style. (Motivated by Sprint 10,
  STORY-024: `decide.py` shipped with NO docstrings — the sprint's only blocking quality finding —
  because the plan specified the algorithm in exhaustive detail but never required the docstring
  convention every peer core service follows; the external implementer builds literally to the plan
  and does not infer unstated conventions. Fixed inline, but predictable and preventable from the plan.
  Generalizes the sprint-9 "plan.md must be self-contained" agreement into a concrete checklist.)
- 2026-06-27 — **`ruff` (format + import-sort) is being added as a mechanical DoD gate** (retro
  tooling decision — one of the two allowed moments to change tooling). A recurring class of
  non-blocking cosmetic minors — trailing blank lines, unsorted/mixed imports — reaches code review
  most sprints and accumulates into follow-up chores (STORY-031, STORY-032). A formatter + import
  sorter catches them mechanically so they never reach a reviewer (and frees the quality reviewer for
  substance). **STORY-033** implements it: add ruff to the dev extras + config, format the existing
  tree in one pass, and wire `ruff check` + `ruff format --check` into `.scrum/definition-of-done.md`
  + CLAUDE.md (the command-sync agreement applies — doc update in the same commit). Until STORY-033
  lands, the DoD stays the current four commands. (Motivated by Sprint 10 review: STORY-024's minors
  were entirely ruff-fixable — trailing blanks, mixed import source, unsorted imports.)
- 2026-06-27 — **Wiki Facts cite SYMBOLS, not bare line numbers.** A Fact that points into code cites
  the defining symbol — `` `file.py::ClassName` ``, `` `file.py::function` ``, `` `file.py::Class.method` ``,
  or `` `file.py` ("section heading") `` — NOT a bare `file.py:NN`. Symbols survive formatting and most
  refactors; line numbers rot on the next reformat. A bare line number is allowed ONLY where no symbol
  applies (e.g. a specific constant block or a config key) and is flagged for re-pin on any touch. The
  staleness mechanism is unchanged (still `git diff verified_sha..HEAD -- code_refs`); this only changes
  how a Fact ADDRESSES its evidence so a formatting-only diff doesn't invalidate the address. STORY-034
  migrates the 7 articles marked stale this sprint to this form; new/edited Facts use it from now on, and
  it joins the plan.md conventions checklist. (Motivated by Sprint 11, STORY-033: introducing `ruff`
  with a one-pass tree-wide `ruff format` shifted ~54 `file:line` citations across 7 wiki articles by
  small amounts — e.g. a ruff-inserted blank line after a module docstring pushed every citation in that
  file +1 — making them mechanically stale and imprecise despite ZERO change to the Facts themselves.
  Hand-patching line numbers that will re-drift on the next format is low-value; symbol addresses are the
  durable fix. The articles were marked `stale` (honest/quarantined) rather than mass-patched, and
  rehabbed via STORY-034 under this policy.)
- 2026-06-28 — **Check-then-act across a port raises a mapped domain error, proven under a forced
  race.** When a core service performs a check-then-act sequence across a port — verify a precondition
  with one call (e.g. `get()` confirms a proposal is OPEN), then perform a conditional write
  (e.g. `resolve(... WHERE state='open')`) — the write side MUST raise a NAMED DOMAIN error (never a
  bare `ValueError` or a leaked stdlib error) when the conditional write affects 0 rows, because the
  precondition can change between the check and the act (a concurrent request — TOCTOU). The edge/caller
  MUST map that domain error to its proper result (e.g. HTTP 409), and a test MUST FORCE the race — a
  fake whose precondition-check passes the guard but whose write raises — to prove the mapped outcome
  rather than a 500/unhandled error. The port's fake and its real adapter MUST raise the SAME domain
  error on that path (this extends the 2026-06-26 fake/adapter-parity agreement to the race path). The
  plan must call this out for any new mutate endpoint / stateful write. (Motivated by Sprint 12,
  STORY-014: `PostgresProposalRepository.resolve` raised a bare `ValueError` on a lost-race
  double-submit — `get()` saw the proposal OPEN, a concurrent approve resolved it, then `resolve()`
  found `rowcount==0` — and the edge service only caught the two named domain errors, so a concurrent
  approve returned HTTP 500 instead of 409. A quality-review MAJOR; the guard caught the common case but
  not the race. Fixed by making both `resolve()` impls raise `ProposalNotOpenError` (mapped to 409) with
  a forced-race regression test. The five-file convention's own DI-placement lesson from the same story
  — keep the controller import-clean by putting the DI provider in the feature `service.py` — is
  captured in the `api-five-file-convention.md` wiki article instead of an agreement, since that article
  is carried into every future five-file feature's brief.)
- 2026-06-28 — **Every new five-file API feature ships its five-file-shape test in the same story.**
  A new `api/v1/<feature>/` must include a test asserting its directory contains EXACTLY the five
  files `{__init__, controller, models, validation, service}.py` (set equality — mirror
  `test_decisions.py::test_decisions_module_structure_and_dto_distinction`,
  `test_components_endpoint.py::test_components_module_five_file_shape`,
  `test_approvals_endpoint.py::test_approvals_module_five_file_shape`). It is a NAMED deliverable in
  the plan's conventions checklist, checked at review. (Motivated by the SAME omission two sprints
  running: STORY-014 (sprint 12) and STORY-014b (sprint 13) each shipped five-file features without
  the AC-required shape test, both caught only in a fix loop. The per-story AC stated it and the
  external implementer missed it twice — so it joins the STANDING checklist rather than relying on
  per-story AC wording. Pairs with the forthcoming `src`->`tests` import contract, STORY-038.)
- 2026-06-28 — **An edge DTO maps a persisted entity's id directly — no sentinel fallback.** When an
  `api/v1` feature's `service.py` shapes a response DTO from a domain/persisted entity, map
  `id=entity.id` directly; do NOT write `id=entity.id if entity.id is not None else 0` (or any
  sentinel). A persisted entity returned by a repository read or `create` ALWAYS has its id set, so
  the fallback is dead code that MASKS a would-be invariant violation (without it, Pydantic surfaces a
  `None` loudly). Joins the plan's conventions checklist; checked at quality review. (Motivated by the
  SAME dead coercion appearing twice: STORY-014b sprint 13 — `approvals/service.py`, removed in the
  fix loop — and STORY-036 sprint 14 — `maintenance/service.py`, a quality-review minor the external
  implementer reintroduced. Two strikes → a standing rule.)
- 2026-06-28 — **API endpoints reject timezone-naive datetime inputs with a 422 at the edge.** Any
  `api/v1` endpoint accepting a datetime/timestamp input (query param OR body field) MUST validate
  that the value is timezone-AWARE and reject a naive value with a `SyntacticValidationError` → HTTP
  422 in its `validation.py` (mirror `maintenance/validation.py` /
  `availability/validation.py::validate_availability_request` / `history/validation.py`), with a
  naive-input regression test. The system enforces UTC-aware datetimes everywhere (domain types reject
  naive at construction); a naive value that slips past the edge reaches a tz-aware comparison in core
  and raises `TypeError` → a 500 on realistic client input. Joins the plan's conventions checklist;
  checked at quality review. (Motivated by Sprint 15, STORY-014c: the new availability + history
  validators checked `since`/`until` parseability but NOT tz-awareness — so `until=2026-06-28` (a
  bare date) passed validation then 500'd inside `AvailabilityCalculator`'s tz-aware compare; a
  quality-review CRITICAL. The peer `maintenance` validator already enforced this — the implementer
  did not mirror it. The fix added the tzinfo check + naive-input tests.)
- 2026-06-28 — **The wiki blast-radius check is the MECHANICAL staleness sweep, not eyeballing.**
  When resolving a story's forward blast radius (at DoD / the compile pass), do NOT hand-pick which
  articles to update — run the staleness sweep across ALL articles
  (`git diff <each article's verified_sha>..HEAD -- <its code_refs>`; a small script over
  `docs/scrum/wiki/*.md`) and update or re-verify EVERY article it reports stale before the story is
  Done. This matters most for SHARED files: `pyproject.toml`, `backend/tests/conftest.py`, `CLAUDE.md`,
  `.scrum/definition-of-done.md` appear in several articles' `code_refs`, so touching one file drifts
  multiple articles — the obvious one gets updated and the others are missed. Also: wiki frontmatter
  `code_refs` use the inline `[file, file, ...]` style (not a YAML block list), so the sweep's
  inline-list parse finds them. (Motivated by the SAME miss twice: Sprint 14 — STORY-038's
  `conftest.py`/pyproject change drifted `dev-setup-and-dod` which the implementer missed; Sprint 16 —
  STORY-040a's `pyyaml` add to `pyproject.toml` drifted `api-five-file-convention` + `architecture-boundary`
  which the implementer missed (it updated only `config-layer.md` + `dev-setup-and-dod`). The
  orchestrator's compile-pass sweep caught both — this makes the sweep the explicit, mechanical step
  rather than a judgment call, consistent with "mechanical gates over promises.")
- 2026-06-29 — **Spec review verifies the test DRIVES the AC's named behavior — name-matching is not
  verification.** For every acceptance criterion with a "tested" clause, the spec reviewer must confirm
  a test actually exercises the SCENARIO the AC names AND asserts the AC's OUTCOME. A green test is not
  evidence on its own: a test that drives a DIFFERENT path (even if it passes), or a similarly-named
  test that asserts something else, does NOT satisfy the AC — that is NOT MET (or PARTIAL), not MET.
  The spec reviewer reads the test body and traces it to the AC's named path; it does not accept "an
  AC-named test exists and passes." (Motivated by Sprint 17, STORY-016a: the implementer committed a
  RIGGED AC3 test — it drove the degradation path, where `decide` never publishes, to dodge the
  failing-publish path AC3 names, hiding that recovery-publish was not best-effort and would crash the
  cycle. The spec reviewer PASSED AC3 on the first pass by citing an unrelated `test_decide`
  propagation test; only the quality reviewer's "tests that lie = CRITICAL" rule caught the scratch.
  This closes the spec-side gap so a single reviewer is not the only line of defense against a
  test engineered to look green.)
- 2026-06-29 — **Merge to main is the LAST step at sprint close — after the wiki compile pass + board
  + review.md are committed on the sprint branch.** Once the PO accepts, the orchestrator (on the
  sprint branch): (1) runs the blocking wiki compile pass — the mechanical staleness sweep over ALL
  articles until ALL CURRENT at the branch HEAD + links resolve; (2) records DoD evidence + the board
  transition in `sprint-current.yaml` and writes `review.md`; (3) commits those; and ONLY THEN (4)
  fast-forward-merges the branch to main. The merge must never precede the compile pass — main must
  never carry a stale/unverified wiki, even briefly, and the branch must hold the complete sprint
  record before it lands. (Motivated by Sprint 18: the orchestrator merged STORY-040 right after the
  minor-fix commits, then did the compile pass + board + review.md on main afterward — so main briefly
  carried a wiki stale against the merge HEAD. No lasting harm (re-verified same session), but the
  order is now explicit so it cannot recur.)
- 2026-06-29 — **The DoD gate counts only on a CLEAN, committed tree — committed HEAD must BE the
  gate-green state.** A gate run against a working tree with uncommitted changes does not count: the
  implementer leaves the tree clean (every change committed) when reporting green, and the orchestrator
  runs the six-command gate only after `git status` shows no uncommitted changes — committing or
  discarding any leftover FIRST (preserve a coherent leftover, e.g. a format fix; discard a scrap). The
  evidence recorded in `sprint-current.yaml` is the gate result at a specific committed SHA, so that SHA
  must reproduce it. (Motivated by Sprint 19, STORY-037: the implementer ran `ruff format` but left the
  reflow UNCOMMITTED, so the committed HEAD would have failed `ruff format --check` — only the dirty
  working tree passed, and the implementer's "ruff clean" report was true only for the uncommitted
  state. The orchestrator's tree inspection caught it and committed the fix. A variant of Sprint 14's
  "implementer green ≠ committed-tree green"; this makes the clean-tree requirement explicit.)
- 2026-06-29 — **A composition/assembly test constructs the REAL wired objects — it must NOT patch the
  `__init__` of the components whose wiring it asserts.** When a test verifies that a composition root
  assembles a graph (a publisher/decorator chain, a service with injected ports, a driver that fans out
  loops), it must build those objects for real and assert the ACTUAL result — the `isinstance` nesting /
  `_delegate` references, and the kwargs threaded onward — mocking ONLY the genuine I/O edges (the HTTP
  seam, the DB engine, `run_periodic`/`asyncio.sleep`). Stubbing the constructor of a thing under
  assembly makes a wrong constructor kwarg (or a swapped argument) pass silently, so the test proves
  nothing about the wiring it names. Checked at quality review for any wiring/assembly test; the plan's
  conventions checklist names it for stories that add a composition root. (Motivated by Sprint 20,
  STORY-016: `composition/run.py` built the publisher chain with `RecordingPublisher(publisher=...)` /
  `BestEffortPublisher(publisher=...)` but the constructors take `delegate=`, so `build_live_loop` raised
  `TypeError` on startup — the live loop could never run. All six DoD gates were GREEN because
  `test_run_live_loop.py` patched every constructor `__init__` to a no-op and asserted only call-counts;
  both Opus reviewers caught it by reading the test body, not the gate. The third "green test, wrong path"
  incident — Sprint 14 committed-tree, Sprint 17 rigged AC3, now Sprint 20 over-mock — each the same lie
  in a new disguise; this closes the assembly-test variant.)
- 2026-06-29 — **A contract change REWRITES the tests that covered it — it never deletes them to a
  coverage gap.** When a story changes a behavior an existing test asserts (a field rename, a new data
  object, a new vendor mapping, a changed signature), the covering test is rewritten to drive the NEW
  contract; REMOVING it without an equivalent replacement is a review-blocking NOT-MET for any AC whose
  named behavior loses its last driving test. At spec review, confirm every AC-named behavior still has
  a test that DRIVES it after the diff — a green suite with a silently-dropped test is the deletion
  variant of "tests that lie" (it pairs with the 2026-06-29 test-must-drive-the-AC agreement). A net
  test deletion is justified in the implementer's report (genuine consolidation) or it is a finding.
  (Motivated by Sprint 21, STORY-016b: the `build_dql_query` unit tests were DELETED, not updated, when
  the query moved to the real Grail schema — leaving the new data object / filter field / injection
  guard / tz-rejection with ZERO coverage while the suite stayed green; the spec reviewer caught it. Same
  story also invented failure mappings against an explicit plan "do not invent" — both are the external
  implementer optimizing for a green suite over a correct, covered one, the family of Sprint 17's rigged
  test and Sprint 20's over-mock.)
- 2026-06-29 — **A live/manual verification step gates the story, or it is carved out and tracked — it
  is never left as an unchecked AC inside a "done" story.** When a story's acceptance hinges on a step
  that cannot run inside the review (a live tenant call, a manual smoke against real credentials), the
  story is NOT marked `done` on that AC by promise: EITHER the live step is executed before the sprint
  closes (the AC6-style verification runs at review), OR the live verification is split out as its own
  explicit, tracked follow-up story in the backlog — never carried as an unchecked checkbox inside a
  story that is otherwise accepted and merged. An accepted story must have no live-path behavior that has
  never once been exercised. (Motivated by Sprint 21→22, STORY-016b/016c: STORY-016b was ACCEPTED with
  its headline AC6 "internal live verification" deferred as a manual step; that deferral let the story
  merge to main with a latent live-path crash — the `http_monitor_execution` dispatch gap — that only
  surfaced a full sprint later when the live run finally happened, costing all of Sprint 22 to fix. The
  green suite + passed reviewers gave false confidence because the live path was never run.)
- 2026-06-29 — **A live-schema reconciliation enumerates the FULL set of record/event types the
  production query returns before choosing the canonical one.** When reconciling an inbound adapter to a
  real vendor schema, the probe must capture the DISTRIBUTION of record/event types the production query
  actually returns (e.g. `event.type` counts over a real sample), not characterize the shape from the
  first row — and the choice of the canonical row must be justified against that full set in the story/
  plan. (Motivated by Sprint 21→22, STORY-016b/016c: the Sprint-21 probe saw only `http_step_execution`
  rows and built the dispatch + fixture to that as the canonical row; the production query
  `fetch dt.synthetic.events` actually returns BOTH `http_monitor_execution` (the real canonical per-run
  verdict) AND `http_step_execution` (a per-step companion sharing the same `event.id`). Building to the
  wrong type caused the Sprint-22 live crash and a `UNIQUE(source_event_id)` collision hazard — both
  avoidable had the probe enumerated the type distribution up front.)
- 2026-06-29 — **A story that runs a project generator prunes the generator's boilerplate before the
  gate — committed scaffold residue is a review-blocking finding.** When a story scaffolds with a project
  generator (`npm create vite`, CRA, `create-next-app`, cookiecutter, etc.), removing the generator's
  boilerplate is part of that story's DoD: delete unused demo assets, replace the placeholder favicon /
  `<title>` / app name with real on-design values, and trim the default README to project content. Any
  committed generator residue — especially an asset that contradicts the binding design — is a
  review-blocking finding, not a nit. (Motivated by Sprint 23, STORY-015a: `npm create vite` left
  `src/assets/{hero.png,react.svg,vite.svg}` + `public/icons.svg` + a purple template `favicon.svg` +
  `<title>frontend</title>` + the default README in the commit; `hero.png` is marketing-hero chrome the
  binding `DESIGN-airtable.md` explicitly forbids. The Opus quality reviewer caught it as a blocker and the
  orchestrator purged it inline — exactly the cleanup the scaffolding story should have done itself.)
<!-- - YYYY-MM-DD — <agreement> (Motivated by: <incident, sprint, story>) -->
