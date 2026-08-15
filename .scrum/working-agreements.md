# Working Agreements
# True process rules only (YourTeam v2). Everything routable lives lower on the enforcement
# ladder — gate/test > script > hook > agent definition > checklist > prose — per the
# PO-approved YOURTEAM_V2_MIGRATION_MAP.md (2026-07-12): conventions in .scrum/checklists/,
# git discipline in .claude/hooks/yt_git_guard.py, gate/wiki mechanics in the yourteam skill
# scripts, model tiering in .claude/agents/yt-*.md, modes in references/execution-modes.md.
# Append-only, with the sanctioned prune exception (each prune recorded below; removed text
# lives in git history). Team-proposed amendments enter only via retro with PO approval and
# must name their ladder rung; PO-stated rules are appended IMMEDIATELY when stated and
# outrank observed codebase patterns wherever they conflict.

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
  **AMENDED 2026-08-01 — the freeze does NOT cover the enforcement ladder.** See
  A14 below: landing a lesson at its correct mechanical rung is exempt.
- 2026-01-01 — One active session: honor .scrum/session.lock; a second session
  runs read-only. (Default)

## PO-stated rules (added during work — binding immediately)
- 2026-07-13 — **YourTeam skill changes stay project-GENERIC.** Anything under
  `.claude/skills/yourteam/` (scripts, references, templates, agent definitions) must work for
  any project: no hardcoded project names, paths beyond the standard `.scrum/`/`docs/scrum/`
  layout, stacks, ports, or vendor assumptions. Project specifics live ONLY in generated/
  instantiated artifacts (`.scrum/checklists/`, `.scrum/definition-of-done.md`, config, CLAUDE.md);
  project examples in skill text are labeled as examples. (PO directive at the sprint-44 review:
  "keep it generic so it can be used on other projects also.")

- 2026-07-29 — **The "Window Check"** — RELOCATED TO THE HOOK RUNG AND DELETED HERE by
  **A21** (sprint-72 retro, PO-approved 2026-08-15). The rule is unchanged and now lives in
  `.claude/hooks/yt_window_check.py`, which runs on every agent dispatch. It is no longer
  prose because prose did not work: it went nine sprints without being routed to the rung it
  named for itself, and in sprint 72 it was run **zero times across seven agent boundaries**
  while two agents died on the limit. Full text in git history; see A21 below.

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
- 2026-06-23 — **Defer auth cleanly.** Auth's absence never blocks a story.
  (**D1, sprint-67 retro, PO-approved 2026-08-03:** the CORS clause was DELETED. It read "From the
  deployment story onward, CORS is restricted to the Vercel origin (+ localhost for dev)" and was
  factually wrong at HEAD — `grep -rn "CORSMiddleware\|allow_origins" backend/src/` returns nothing,
  no CORS middleware exists, and Vercel was superseded. A binding agreement instructing a future
  story to do something wrong is the same failure class as sprint 67's ten prose findings, sitting
  in this file. The auth half above still binds.)

## Amendments
- 2026-07-06 — **A DoD-gate red caused by resource contention rather than the code under
  test is an INVALID signal — prove it, re-run isolated for the valid result, and file a
  story to make the gate deterministic.** When a gate command false-reds, the orchestrator
  must PROVE it is contention before discounting it: the failing unit has an EMPTY diff
  since the sprint cut (`git diff sprint-N-start..HEAD -- <failing file>`) AND it passes
  when given adequate resources (in isolation and/or serialized, e.g. Vitest
  `--no-file-parallelism`). Only then is the red discounted; the VALID gate signal is the
  resource-isolated re-run, recorded as the DoD evidence with a prominent note. A gate that
  can flake is filed as a defect so the mechanical floor stays trustworthy — a flaky gate is
  never left as the standing gate. If the contention proof does NOT hold (the unit changed
  this sprint, or it fails in isolation too), the red is REAL and the story is not Done.
  (Motivated by Sprint 37, STORY-046; generalizes the sprint-28 DB-concurrency incident.
  `yt_gate.py` prints this protocol on any red.)

- 2026-07-14 — **Token-economy amendments** (PO-approved after the sprint-45 token audit — one
  sprint consumed two 5-hour limit windows; constraint: no meaningful loss of quality/purpose).
  (a) **Scoped story gates:** mid-sprint, per-story DoD gates MAY run `yt_gate.py --only <cmds>`,
  limited to the commands the story's diff can affect; the FULL nine-command gate remains mandatory
  — and is the evidence of record — at least once at sprint close on the final HEAD. A red at any
  scope still blocks. (Rung: prose — orchestrator procedure; `--only` already exists in the script.)
  (b) **DELETED 2026-08-05 — D3, sprint-68 retro.** See the prune record.
  (c) **Board evidence hygiene:** at sprint close, superseded `dod_evidence`/`gate_notes` narrative
  moves into the sprint's `review.md`; `sprint-current.yaml` carries only the final evidence block —
  it is re-read at every standup. (Rung: prose.)
  (d) Landed the same day at the script/agent rungs: `yt_wiki.py` format-only auto-verify (a
  whitespace-only diff since the baseline cannot have changed a Fact, so the article is simply not
  stale — one formatter commit had re-staled 7 articles; the mechanical *sha bump* this originally
  performed went away with `verified_sha` on 2026-08-12, the skip did not) + staleness-amplifier
  `refs` lint (advisory; `--strict-refs` to block);
  `yt_gate.py` strips decorative banner lines from evidence tails; both reviewer agent defs scoped
  to the story's diff pack (targeted context reads allowed, broad repo re-exploration prohibited).
  PO quality constraints honored: spec/quality reviewers stay SEPARATE (independence), no coverage
  skipped, format-only auto-verify is conservative (any non-whitespace change still stales).
  (Motivated by: sprint-45 token audit — wiki churn was 10 of 33 commits; measured 285 code_refs /
  239 files; `pyproject.toml` cited by 5 articles.)

- 2026-07-15 — **External-delivery pivots must set `mode: external` immediately** (sprint-46 retro).
  When implementation is delegated outside the in-process pipeline mid-sprint — a CC session limit,
  a PO pivot to an external agent — the orchestrator sets `mode: external` on `sprint-current.yaml`
  the moment it happens. This mechanically mandates the external-mode verification floor on resume
  (spec + quality review per story regardless of points, plus an independent full-gate re-run) so it
  is never a judgment call. (Motivating incident: sprint-46 was implemented by Antigravity after a
  session limit; the board stayed `mode: in-process` and external-mode verification was applied only
  because the orchestrator recognized the situation — which caught a MAJOR self-review had missed.
  Rung: prose; may harden to a plan-verification checklist item later.)

## Prune record
- 2026-08-05 — **D3, sprint-68 retro, PO-approved: the THIRD rule deleted on its merits.**
  The 2026-07-14 token-economy amendment's clause **(b) "Clean-container gates"** — *stop idle dev-DB
  containers before a full gate run … (Rung: prose until STORY-080 lands the test-rung fix.)*
  Removed whole, on three independent grounds: its own stated expiry condition was met (STORY-080
  accepted at **sprint 47**, "standing gate false-red resolved"); its subject is retired with the
  Postgres layer (`backend/tests/` has no `test_dev_db_*` file, it has `test_no_postgres_guard.py`);
  and it has **zero citations across sprints 63–68**. Nothing is lost — the general case is the
  2026-07-06 contention protocol, which HAS fired and is untouched. Clauses (a), (c) and (d) of the
  same amendment all still fire and stay. Full text:
  `git show e982927:.scrum/working-agreements.md`.

- 2026-08-03 — **sprint-67 retro, PO-approved: the first two rules ever deleted on their merits**
  (every prior removal was a PO-directed amnesty or a routing exercise; A15 asked "has this fired?"
  and these two answered no because they are DEAD, not merely quiet).
  **D1** — the CORS clause of the 2026-06-23 "Defer auth cleanly" agreement. Factually wrong at
  HEAD: no CORS middleware exists anywhere under `backend/src/`, and the Vercel origin it names was
  superseded. Full text is in the entry itself, which records the deletion inline; the auth half
  survives.
  **D2** — the 2026-07-15 "Expedite STORY-080" amendment, removed WHOLE. Fully spent: STORY-080 was
  accepted at sprint 47, and the `test_dev_db_*` family, `alembic` and `DATABASE_URL` it governs
  belong to the retired Postgres layer. The 2026-07-06 contention protocol it pointed to is
  unaffected and still binds. Full text: `git show 626f6b0:.scrum/working-agreements.md`.

- 2026-07-04 — PO-directed prune (post-sprint-32): removed 3 entries that no longer bind —
  (1) 2026-06-26 "External implementation from Sprint 9" and (2) 2026-06-28 "Every sprint lock
  produces an implementer prompt", both superseded wholesale by the 2026-07-02
  implementation-returns-in-process directive (the one surviving obligation — plan.md
  self-containment + conventions checklist — is restated inside the 2026-07-02 entry and the
  2026-06-27 checklist agreement); (3) 2026-06-27 "ruff is being added as a DoD gate", a
  transitional tooling decision fully implemented by STORY-033 — the live gate is recorded in
  `.scrum/definition-of-done.md` + CLAUDE.md, so the adoption note carried no ongoing rule.
  Full text of all three: `git show b2aff76:.scrum/working-agreements.md`.
- 2026-07-12 — **PO-approved YourTeam v2 migration prune** (YOURTEAM_V2_MIGRATION_MAP.md,
  approved in full): ~40 entries routed down the enforcement ladder and retired from this
  file — engineering conventions → `.scrum/checklists/{implementer,spec-review,
  quality-review,plan-verification}.md` (each item keeps its date + motivating incident);
  git discipline (scoped staging, wrong-branch commits) → `.claude/hooks/yt_git_guard.py`;
  gate mechanics (clean-tree, sequential DB-gated runs, evidence recording) → `yt_gate.py`;
  wiki mechanics (mechanical sweep, Facts coverage) → `yt_wiki.py`; model tiering + role
  rules → `.claude/agents/yt-*.md`; external/parallel/debug/parked shapes + the spent
  sprint-42/43 exceptions → `references/execution-modes.md` + the per-sprint `mode:` field;
  live-verification rules → the reality gate (SKILL.md + ceremonies §5); "orchestrator may
  finish trivial tails" → edge-cases.md #13. Full pre-prune text:
  `git show b025b3c:.scrum/working-agreements.md`.

- 2026-07-15 — **Token-economy amendments v2.1.2 (PO-approved, out-of-sprint):**
  (1) `yt-spec-reviewer` runs on sonnet — the AC↔test trace is mechanical verification;
  (2) `yt-implementer` carries an explicit tool allowlist (Read, Write, Edit, Grep, Glob,
  Bash) — an unrestricted implementer inherited every session MCP tool schema, re-writing a
  ~125k cached prefix per dispatch; (3) `yt-plan-verifier` is dispatched conditionally —
  contract-sensitive sprints only (consumer contracts / adapter-vendor paths / units-scale
  logic / external mode), with any skip + reason recorded in `plan.md` at approval.
  (Motivated by: session-limit burn audit 2026-07-15 — a $22 session changed 9 lines;
  1.7M cache-write tokens traced to subagent prefix re-writes and an always-on opus
  plan-verifier.) (Rung: agent definitions + skill text — this entry is the record; the
  enforcement lives in `.claude/agents/yt-*.md` frontmatter and SKILL.md/ceremonies.md §4.)

- 2026-07-15 — **External deliveries arrive committed per-story; self-reported gate results are
  never trusted** (sprint-47 retro). The `external` execution mode now carries an explicit delivery
  contract stated at handoff and checked on return: commit per story with `STORY-NNN:` messages
  (ideally the per-green TDD cadence); if the work arrives as one uncommitted tree, the orchestrator
  reads each diff and commits it per-story as the reviewable object BEFORE reviewing (reviewers need
  a stable per-story diff; the gate refuses a dirty tree). An external "all gates green" summary is a
  to-verify list, never evidence — the orchestrator's own `yt_gate.py` run on the final HEAD is the
  only record that counts. (Motivating incident: sprint-47 external delivery arrived as one
  uncommitted blob with no cadence and self-reported "all nine gates clean" while carrying two
  quality MAJORs and two gate commands that had never run against a DB. Rung: reference — the
  contract lives in `references/execution-modes.md` §2; this entry is the pointer.)

- 2026-07-15 — **The gate warns up front on unset env preconditions instead of surfacing a raw error
  mid-run** (sprint-47 retro). `yt_gate.py` now runs a generic precondition scan and prints a named
  WARNING when a command's required env var is unset (advisory — the command still runs). Kept
  project-GENERIC per the 2026-07-13 rule: the runner hardcodes no var names; the project's DoD line
  declares them via a `(requires-env: VAR, ...)` annotation (added here to the `alembic upgrade head`
  and `check_fk_direction.py` lines). (Motivating incident: a standalone full-gate run left
  `DATABASE_URL`/`DATABASE_URL_DIRECT` unset, so the two DB-gated commands errored on a raw KeyError
  — a false-red distinct from the code failing — costing a diagnose-and-re-run cycle. Rung: script
  + project config — the mechanism is in `scripts/yt_gate.py`, the var names in
  `.scrum/definition-of-done.md`; this entry is the record.)

<!-- - YYYY-MM-DD — <agreement> (Motivated by: <incident, sprint, story>) (Rung: <ladder rung considered and why prose>) -->

- (2026-07-17, sprint-51 retro) Before any multi-step live-cloud CLI sequence (image
  push + service updates, stack operations), verify credential freshness first
  (`aws sts get-caller-identity`); temporary/SSO tokens expire mid-sequence. On expiry
  mid-sequence, resume from the FAILED step, never restart the sequence — completed
  steps (e.g. an ECR push) survive. Motivating incident: sprint-51 redeploy — push
  succeeded, both update-service calls died on ExpiredTokenException, handoff blocked.
- (2026-07-29, sprint-62 retro) **A reality gate must be shown able to fail.** No reality gate
  may be reported PASS without a recorded answer to "how could this have failed?", in one of
  two forms:
  - **Defect / fix stories:** run the SAME, unmodified gate at the pre-fix commit (a worktree
    is enough) and record BOTH scores in the board's `reality_gate.discrimination_proof`. A
    gate that also passes at the pre-fix commit is not a gate.
  - **Every other story:** for each assertion that could pass one-sidedly, name the second
    side that was asserted in `reality_gate.two_sided_note` -- or state explicitly that the
    assertion is one-sided and why that is acceptable.
  One of the two fields is REQUIRED on every `reality_gate` board record; its absence is
  grep-visible. Motivating incidents (all sprint-62): STORY-146's gate reported "IDENTICAL" on
  two EMPTY dumps twice over (DynamoDB Local partitions by access key without `-sharedDb`;
  then uppercase `PK/SK` against a lowercase schema); one of STORY-148's 19 checks passed as a
  tautology because httpx/h11 refuses to transmit a header value with a trailing space, so the
  request never left the client; and STORY-149's 12/12 means something ONLY because the same
  gate scored 7/12 at the pre-fix commit. The rule generalises all three: a PASS whose failure
  mode is indistinguishable from "nothing happened" is not evidence. (Rung: prose + a required
  state-file field. A mechanical rung was considered and rejected -- a reality gate is bespoke
  per story, so no script can judge whether a given assertion could have failed. The required
  field is the lowest rung that holds: it makes the omission visible even though it cannot
  make it impossible.)

- (2026-07-29, mid-sprint-63) **A1 refinement — a worktree proof must prove WHICH code it ran.**
  A1 above mandates re-running a gate at the pre-fix commit "a worktree is enough". In THIS repo a
  worktree is NOT automatically enough: the package is installed editable
  (`package-dir = {"" = "backend"}` in `pyproject.toml`), so setuptools' editable finder resolves
  `src.*` to `<repo>/backend/src` — the MAIN tree — from inside any worktree, whatever pytest's cwd
  is. A worktree proof of a change under `backend/src/` therefore runs the SAME code on both sides
  and comes back identical. Before reporting either score, print the imported module's `__file__`
  and the value under test and confirm the path lies inside the worktree; force
  `PYTHONPATH=<worktree>/backend` (it precedes the editable finder), or patch the main tree in place
  and restore it with `git diff` verified empty. (Motivating incident: sprint-63 STORY-180's AC2
  discrimination proof reported 4/4 on BOTH sides on its first run; verified by importing the module
  inside the worktree and finding the main tree's path and the unpatched value. The failure mode is
  worse than a plain false PASS — "green both sides" reads as "this constant does not matter", so
  the proof would have argued against a correct fix. Re-run PYTHONPATH-forced: 3/4 patched, 4/4
  restored. Sprint-62's STORY-149 proof is NOT retroactively in doubt — it scored 7/12 pre-fix vs
  12/12 at HEAD, and a redirected run would have scored 12/12, so it demonstrably executed the
  pre-fix code.) (Rung: checklist — landed the same day as a line in
  `.scrum/checklists/implementer.md`, which is what agents actually read; this entry is the record
  and the reason. A SCRIPT rung is available and better — a helper that asserts import provenance
  before a proof runs — and is deliberately NOT taken mid-sprint: tooling is frozen by the
  2026-01-01 agreement and ad-hoc skill-script edits outside a story are forbidden by the
  2026-07-15 entry. Proposed at the sprint-63 retro, together with whether the reviewer and
  plan-verification checklists need the same line.)

- (2026-07-30, sprint-63 retro) **A3 — a two-sided proof must assert that the two sides DIFFER.**
  A1 requires every reality gate to carry a discrimination proof or a two-sided note. A3 says what
  makes one valid: it records both outcomes AND asserts they diverge. Identical outcomes on both
  sides is a FAILED proof, never a passed one, whatever value appeared — the proof's authority comes
  entirely from the divergence, so "green both sides" means it did not discriminate. (Motivating
  incident: THREE proofs came back identical on both sides inside sprint 63, each by a different
  mechanism — STORY-180's discrimination proof via the editable-install/worktree trap (the A1
  refinement above); the orchestrator's own publish-guard harness, which walked a `delegate`
  attribute where `publish_helper.py:51/:96/:169` store `_delegate`, so it reported a one-element
  chain on both sides with the safe side green for the wrong reason and the unsafe side falsely
  looking safe; and — the same shape one rung out — STORY-176's Docker-gated guard test, which
  silently SKIPS where Docker is absent, degrading a two-sided proof to one-sided with no output
  saying so (now STORY-185). The A1 refinement covers IMPORT PROVENANCE only and would have caught
  just the first: the mechanisms differ, the symptom does not, so the SYMPTOM is the trigger.)
  (Rung: checklist — landed in `.scrum/checklists/implementer.md` and
  `.scrum/checklists/quality-review.md`. A mechanical rung was considered and rejected for the same
  reason A1's was: the harness is bespoke per story, so no script can judge whether a given pair of
  assertions could have diverged. What CAN be mechanised is narrower and belongs in a story, not an
  agreement: an import-provenance helper, proposed at this retro and still unfiled.)

- (2026-07-30, sprint-63 retro) **A4 — a computational deliverable is pinned only by a mutation.**
  If a story's headline deliverable is computational — arithmetic, spacing, ordering, thresholds,
  windowing — the implementer mutates the computation once and records which tests go RED, then
  restores with `git diff` verified empty. The quality reviewer does the same independently. Zero
  tests RED means the behaviour is UNPINNED and the story is not done, regardless of coverage or of
  a complete AC-to-test trace. (Motivating incident: STORY-176 shipped a suite that was green, spec
  reviewed PASS with all 18 in-scope AC lines traced to tests, and in which a mutant
  `expand_scenario` ignoring `interval_seconds` and hardcoding 30s passed ALL THIRTY new tests. Its
  headline claim was unpinned. The staggered-intervals test even NAMED the behaviour while asserting
  on bucket sets built from arguments the test itself supplied. Reading found nothing; the mutation
  found it in one run.) (Rung: checklist ×2 — deliberately scoped to computational deliverables so it
  does not become a tax on every story. NOT routed to the gate: `yt_gate.py` runs project commands
  and cannot know which computation is a given story's centre.)

- (2026-07-30, sprint-63 retro) **A5 — review debt is recorded on the board, not carried in
  someone's head.** When a story's diff (or part of it) is never read by an independent reviewer —
  a reviewer died, a review was skipped for ceremony size, a fix round landed after the reviewers
  had run — the story's gate record carries a `review_debt` field naming exactly what was not
  reviewed and what was substituted for it. A story may still be accepted with review debt; the PO
  decides. What it may not do is reach review looking fully reviewed. (Motivating incident: sprint
  63's STORY-176 fix round — 11 commits — was never read as code, because the re-reviewer died on
  upstream 529s three times. The orchestrator substituted mechanical verification (a mutation proof,
  two further mutations, a skip check, a validator probe) and recorded the gap voluntarily; nothing
  in the process required it. The PO then authorised the review post-acceptance, it ran, and it found
  one MAJOR that the mechanical checks had not — the `interval_seconds` invariant sitting on the
  loader rather than the type, now STORY-184. So the debt was real and worth naming.) (Rung: board
  schema — a `review_debt` field on the story-gate record, which the orchestrator writes and which is
  visible at review. Lowest rung that holds: it cannot force the review to happen, but it makes the
  omission impossible to miss.)


## A6 — a green `pytest` may not hide a skipped persistence floor (2026-07-30, sprint-64 retro)

**Rung: PROJECT CODE.** `backend/tests/conftest.py`'s `dynamo_local` fixture FAILS instead of
skipping when `REQUIRE_DYNAMO` is set to anything other than empty/`0`/`false`/`no`. The default
remains SKIP, so a contributor without Docker can still run the suite; CI and the DoD gate set the
var. `.scrum/definition-of-done.md` annotates the `pytest` line with `(requires-env: REQUIRE_DYNAMO)`.

**Read this carefully, because the obvious reading is wrong:** the `(requires-env: ...)` annotation
is **ADVISORY in `yt_gate.py` and never blocks** (`yt_gate.py:158-160` - "it never blocks; the
command still runs and reds honestly"). It only surfaces the var when unset. **The fixture is the
enforcing rung**; the annotation is the signpost. Do not cite the annotation as the control.

**Motivating incident.** Establishing sprint 64's baseline, `pytest` exited **0** at
`561 passed, 53 skipped` and the gate recorded PASS, because Docker was down. The same commit and the
same command with the container up gave `614 passed, 0 skipped`. 53 tests - the entire persistence
floor - vanished with no red signal and an identical exit code. The whole sprint then worked around
it by hand, recording pass/skip counts on every gate record. That is prose applied from memory, and
it held only because someone happened to read the count.

**Verified on landing, three-sided:** `REQUIRE_DYNAMO=1` + no endpoint + Docker unreachable -> 4
errors, non-zero exit. `REQUIRE_DYNAMO` unset, same conditions -> 4 skipped (contributor path intact).
`REQUIRE_DYNAMO=1` + a working endpoint -> 4 passed.

**Standing practice retained:** record the pass/skip COUNTS on every backend gate record. A nonzero
skip count is an incomplete gate, not a pass.

## A7 - a reality gate is an exit code, not a paragraph (2026-07-30, sprint-64 retro)

**Rung: role checklists + board schema.** `.scrum/checklists/implementer.md` and
`.scrum/checklists/quality-review.md` each gained a line: any reality-gate, discrimination or proof
artifact must terminate with an explicit verdict and a **non-zero exit on failure**, must be shown
failing on deliberately bad input before it is reported, and must treat a polling timeout as a
FAILURE rather than partial evidence. The board records the artifact's **exit code**; values read out
of stdout are not evidence and may not be recorded as a pass.

**Motivating incident.** STORY-182's positive-side harness computed every AC3/AC4/AC5 value
correctly and printed them, asserted only AC1, and exited 0 regardless; a polling timeout set a flag
and continued. The orchestrator ran it, read correct numbers, and reported "reality gate side 1
PASS". The numbers were right - but the artifact could not have said otherwise, and on a rerun with a
dead monitor id the report would have been identical. Its two sibling gates in the same story both
ended `sys.exit(0 if main() else 1)`, which is what made the inconsistency reviewable at all.

**Relationship to A1 and A3.** A1 asks "how could this have failed?" and A3 asks "did the sides
differ?" - both about the SUBJECT of the proof. Neither asks whether the HARNESS can return failure
at all. A7 is that missing question. The move that closed the defect - feeding all four new
assertions bad evidence and confirming 13/13 raise - is the expected practice, not an extra.

## A8 - a spike states what it REPRODUCED separately from what it TIMED (2026-07-30, sprint-64 retro)

**Rung: prose (this agreement).** Deliberately not a checklist line: spikes are orchestrator work and
there is no orchestrator checklist to hold it. A spike finding must state, per claim, whether it was
**reproduced against the real system** or **measured on a stand-in**, and must never combine the two
in one sentence.

**Motivating incident.** Sprint 64's SPIKE-064 reported: *"all 41 signals fired their FIRST cycle
within 2s ... so the run must span startup, not an interval."* The control-flow half was reproduced
and correct. The timing half was measured on a synthetic stand-in with **no I/O**; the real first
pass, doing sequential HTTP and DynamoDB work, takes 20-90+ seconds. STORY-182's implementer found
this the hard way - its first two harness runs captured 37 of 41 signals before replacing a fixed
sleep with polling - and raised it against the spike, which is how it was corrected. A stand-in that
removes the very I/O the real system spends its time on can validate control flow while
mis-measuring cost by an order of magnitude. The two claims travelled in one sentence, which is what
let the bad half be trusted.

## A14 - the enforcement ladder is EXEMPT from the mid-sprint tooling freeze (2026-08-01, PO-directed)

**Rung: this agreement + `references/ceremonies.md` §6.** The 2026-01-01 default freezes tooling
mid-sprint. That default now carries one exception: **when a lesson's correct rung is a gate
command, a script, a hook or an agent definition, you may land it there immediately — mid-sprint,
without waiting for planning or retro.** The freeze exists to stop scope creep and shiny new
dependencies. It was never meant to stop the process repairing its own safety net, and adding an
assertion to an existing script is not a tooling change in the sense the default means.

Unchanged by this: new MCP servers, new CLIs, new runtime dependencies and anything with an install
step stay frozen mid-sprint. The exemption covers landing an already-decided lesson at an already-
present mechanism. If landing it needs a new dependency, it is not exempt.

**Motivating incident.** THREE amendments explicitly named the script rung, said it was the right
one, and took prose instead — each citing this freeze plus the 2026-07-15 ban on ad-hoc skill-script
edits outside a story:
- A1-refinement (mid-sprint-63): *"A SCRIPT rung is available and better ... deliberately NOT taken
  mid-sprint: tooling is frozen by the 2026-01-01 agreement."*
- A3 (sprint-63 retro): the import-provenance helper, listed under future work as *"the mechanical
  rung A1/A3 keep declining to take"*.
- The 2026-07-29 Window Check: *"The script rung WAS considered and is where this belongs
  long-term ... It is not taken now for two reasons: tooling is frozen mid-sprint."*

In every case the rule landed at the WEAKEST available rung specifically because the strongest one
was procedurally blocked, and in every case the prose subsequently failed to hold — which is how the
six-amendment evidence family (A1 through A9) came to exist at all. A rule that forces lessons
downward is worse than no rule.

**Scope guard.** This is not licence to write production code outside a story: that prohibition is
separate and stands. Where the mechanical rung is substantial new code, file it as a story and say
so (STORY-212 is exactly this case). The exemption is for landing the rung, not for skipping the
gate.

## A15 - rules EXPIRE; the retro audits what exists before adding to it (2026-08-01, PO-directed)

**Rung: `references/ceremonies.md` §6 (retro protocol) + this agreement.** The retro's default
output is now **ZERO amendments**, and every retro begins by auditing the rules already in force
rather than by looking for new ones.

1. **Audit first.** Walk `.scrum/checklists/` and this file. For each item ask: *has this FIRED in
   the last six sprints* — caught something, blocked something, been cited in a review finding? An
   item that has not fired in six sprints is proposed for **DELETION**, not relocation. Deletions
   are PO-approved like additions and recorded here with the reason.
2. **An addition must show no existing rule covered the incident.** If one did and was not followed,
   that is evidence the rule is not being READ, and the correct response is to shorten or relocate
   the existing rule — never to add a second one saying the same thing more emphatically.
3. **Routing down the ladder is not deletion.** Moving a rule from prose to a checklist keeps it
   alive and still costs tokens at dispatch. Only removal removes cost.

**Motivating evidence.** Governance surface (`working-agreements.md` + the implementer and quality
checklists), measured 2026-08-01:

| Date | Bytes | |
| --- | --- | --- |
| 2026-06-23 | 2,593 | inception |
| 2026-07-12 | 58,061 | pre-prune peak |
| 2026-07-12 | 13,195 | v2 migration prune (-77%) |
| 2026-07-31 | 53,776 | 4.07x regrowth in 19 days |

Two PO-directed amnesties in the record and **not one rule ever retired on its own merits**. The
2026-07-12 prune did not delete: it routed ~40 entries into `.scrum/checklists/`, which then grew
3.2x. Meanwhile instruction density is not free — the newest amendments sit at the BOTTOM of the
longest files, which is where instruction-following degrades first, so the rules bought with the
most expensive incidents are the ones most likely to be skipped. That is the documented failure mode
for over-long instruction files, and A3-through-A9 existing at all is this repo's own evidence of it:
each was added because its predecessor was not followed.

**Deliberately NOT claimed:** that any specific rule is wrong. The claim is narrower — that a system
which can only ever add is not learning, and that "has this fired?" is a question the process has
never once asked.

**Baseline, so this agreement is falsifiable — recorded as a COMMAND, not a number.** A total
written into this file changes this file, so it is stale the moment it is saved. Two attempts to
record one here drifted by 1,065 and then 633 bytes; the third is this. Re-derive instead:

```
git show sprint-66:.scrum/working-agreements.md | wc -c      # the baseline side
cat .scrum/working-agreements.md .scrum/checklists/implementer.md \
    .scrum/checklists/quality-review.md | wc -c              # governance at HEAD
```

**The one stable figure: the A1-A9 collapse removed 6,043 bytes from the two CHECKLISTS**
(23,506 -> 17,463), and nothing since has touched them.

**Read the rest honestly: in raw bytes this pass roughly broke even.** What the collapse removed
from the checklists, A14 + A15 + this baseline added back to this file as PROSE — the rung A15
itself calls the last resort. A deliberate de-bloating pass, run immediately after measuring the
ratchet by someone who had just written the case against it, netted approximately zero. That is how
strong the pull toward prose is, and it is the best evidence available that A15 needs its mechanical
rung (an audit script, STORY-212) rather than more words.

**Where it DID pay, because raw bytes hide it:** the two costs are not equivalent. Checklist bytes
are loaded into EVERY subagent dispatch; this file is loaded ONCE per session at standup. So the
real change is -6,043 bytes per dispatch (~-1,500 tokens x every implementer and reviewer run) and
+5,887 once per session, against a CLAUDE.md prune of -9,236 in the highest-priority slot there is.
Per session that is ~-3,350 bytes before a single dispatch. **Prefer removals from the rungs that
are paid repeatedly.**

## A16 - the Facts lint may not report CLEAN about text it never checked (2026-08-03, sprint-67 retro)

**Rung: SCRIPT — landed, not described.** `yt_wiki.py` gained a `citations` check (advisory, like
`refs`; `--strict-citations` promotes it to blocking). It reports two kinds of Fact citation the
Facts lint silently drops: one whose path does not resolve from the repo root, and a bare `` `:NNN` ``
with no filename to anchor on.

Two INDEPENDENT mechanisms bit in sprint 67, both in `status: verified` articles carrying FRESH
stamps — which is what makes this a defect in the floor, not a lapse: STORY-202's six bare `:NNN`
sites (five pointing at `],`, a docstring, a comment) and STORY-200's abbreviated
`core/services/approval.py` citing a file absent from the article's `code_refs`.

**Landing it revealed the real scale: 147 Fact citations across 13 articles had NEVER been checked.**
`facts: CLEAN` was covering a fraction of this wiki. Advisory by design — that backlog is not
fixable in one pass, and the number is the point.

Full narrative, including the first implementation's 515-note false-positive flood and the known
`` `:8000` `` port-vs-line false positive: `docs/scrum/sprints/2026-08-02-sprint-67/retro.md`. The
check's own docstring carries the rest. Kept short deliberately: the enforcement is in the script,
and this file is read at every standup.

**The test at the sixth sprint from now:** run the second command above and compare it against the
same command at the commit that landed A15 (`git log --oneline -S "A15 - rules EXPIRE"` finds it).
Governance must be SMALLER, AND at least one rule must have been deleted on its merits rather than
routed. If it is larger and nothing was deleted, A14/A15 failed and are themselves candidates for
deletion under their own rule.

## A17 — the reviewers are race-immune by construction (2026-08-05, sprint-68 retro)

**Rung: AGENT DEFINITION — landed in both reviewer definitions; the rule is THERE, not here.**
Not a new rule. "You never modify files" already existed and was bypassed **through Bash**, so per
A15 §2 it was made concrete rather than restated. Do NOT serialise the reviews.

## A18 — C3 has a mechanism, and it reaches two of its five failure modes (2026-08-05, sprint-68 retro)

**Rung: SCRIPT — `yt_wiki.py sweep`, run after the story's last commit.** Originally
`yt_wiki.py c3 --range BASE..HEAD`, advisory, read per STORY range; **that check was DELETED
2026-08-12** when the staleness baseline became derived. The derived sweep IS c3's satisfiable
half — "the article moved with the code" is now measured continuously at HEAD as
`baseline == the code_ref's commit` — and it produces a verdict instead of the 45 per-commit notes
c3 emitted over sprint 68, which it could not tell apart from TDD steps. **STORY-219 is the half
that reaches the other three failure modes** (citation resolution) and is unaffected. Narrative:
`docs/scrum/sprints/2026-08-03-sprint-68/retro.md`.

**REDRAFTED 2026-08-12 (sprint-69 retro, PO-approved) — "same commit" is replaced by "same STORY,
no false intermediate".** C3's literal same-commit reading is unsatisfiable in two OPPOSITE
situations, both of which occurred in sprint 69:
- *From below:* under strict per-step TDD commits, a wiki correction that cites code which does not
  exist yet cannot share a commit with it. Three stories hit this; all three disclosed it; the
  `verified_sha` self-reference dance appeared three times.
- *From above:* a commit touching an amplifier `code_ref` (`pyproject.toml` is cited by five
  articles) stales five articles it is not about, and cannot bump them without abandoning its own
  subject.

The rule, as it now reads:
1. The wiki correction lands **within the story**, and **no intervening commit may leave the repo
   asserting something false**.
2. **There is no `verified_sha`** (retired 2026-08-12). The baseline is the article's own last
   commit, derived by `git log -1 -- <article>`, so the self-reference this clause was written to
   forbid is impossible by construction rather than prohibited by prose — a commit carrying the
   article and its `code_ref` together is trivially not stale. The converse now binds: **touching a
   swept article IS re-verifying it**, so do not edit one whose Facts you have not re-read. When no
   Fact changed, the re-verification is an appended `## History` line.
3. **Run `yt_wiki.py` AFTER the story's last commit.** A sweep measured before the final edit is not
   evidence about the story. Sprint 69 opened with a committed "sweep CLEAN" line that was true when
   run and false at HEAD, which is exactly this failure.

Per A15 this REPLACES the earlier reading rather than restating it. Clause 2 was redrafted a second
time on 2026-08-12, when the field it governed was deleted; the amplifier problem it names in the
"from above" case is now bounded by the `map`/`reference` tier split rather than by stamp
discipline. Narrative: RC-9 and RC-10 in `docs/scrum/sprints/2026-08-05-sprint-69/retro.md`.

## A21 — the Window Check is a hook, not a paragraph (2026-08-15, sprint-72 retro)

**Rung: `.claude/hooks/yt_window_check.py` (PreToolUse on agent dispatch), registered in
`.claude/settings.json` on matcher `Agent|Task`.** This is a **RELOCATION, not an addition** —
thresholds and data source are byte-identical to the PO-stated rule of 2026-07-29, and that rule's
prose entry was **DELETED in the same commit** (−34 lines). A15 §3 is explicit that routing down the
ladder is not deletion; moving a rule and leaving it behind keeps the cost and creates the drift.

**Why it was needed, stated as evidence rather than as a principle.** The rule existed for nine
sprints. Its own closing parenthetical named the script rung as where it belonged and said *"File it
at the sprint-63 retro."* That never happened. In sprint 72 it was run **zero times across seven
agent boundaries**, and **two agents died on the session limit** — one mid-fix-round, one before it
touched a file, costing the sprint its last story. Checked at the retro: the statusline file existed
and was current the whole time, and the command worked on first try. Nothing was broken except that
a paragraph in a 558-line file loaded once per session was not read at hour four.

Both stated reasons for the original deferral were void by then: **A14** exempts the enforcement
ladder from the mid-sprint tooling freeze, and a retro-approved amendment landing at a named rung is
the opposite of the ad-hoc skill-script edit the 2026-07-15 entry forbids.

**Behaviour** (unchanged): `five_hour.used_percentage` **< 85** allow silently · **85–94** allow with
a warning naming the percentage and reset time · **≥ 95** **BLOCK** with the reset time and a pointer
to the board · `seven_day ≥ 90` warn only, never block, because a 7-day reset cannot be waited out
inside a session and the PO must be told instead.

**FAILS OPEN by construction** — a missing, stale or malformed statusline allows the dispatch with a
note. Same contract as `yt_git_guard.py`: a backstop, never an outage.

**Guarded, and shown RED.** Nine branches exercised at landing (13/84/85/94/95/99 percent, a 7-day
trip, a missing file, a malformed file) with the exit codes verified 0/0/0/0/2/2/0/0/0. Template
parity now **globs `templates/hooks/*.py`** instead of naming one hook — the hardcoded entry would
have silently excluded this hook, passing while it drifted. Shown RED by mutating the instance.

**Project-generic** (PO directive 2026-07-13): `~/.claude/statusline-latest.json` is a Claude Code
artifact; the hook knows nothing about the project's name, stack, or layout. Its user-facing strings
are pure ASCII, deliberately — this repo has a live mojibake story (STORY-192) and a `.scrum/`
encoding guard, and a hook that prints through a cp1252 console should not add to it.
