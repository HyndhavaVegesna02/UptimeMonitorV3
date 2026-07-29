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

- 2026-07-29 — **The "Window Check" — read the session window at every agent boundary, and park
  rather than die mid-agent.** Invocable by name: "run a window check", or "window check before
  you dispatch".
  **When:** immediately after EVERY subagent completes (implementer, spec reviewer, quality
  reviewer, plan verifier, scout — the reviewer pair counts as one boundary since they run
  concurrently) and before dispatching the next one. Not per story — per agent. Every such
  boundary has a commit behind it, so parking there costs nothing and dying there costs one step.
  **How (mechanical — the number is read, never estimated):** the PO's statusline command writes
  its full payload to `~/.claude/statusline-latest.json` on every render. Read it:
  ```
  python -c "import json,time,os;d=json.load(open(os.path.expanduser('~/.claude/statusline-latest.json')));r=d['rate_limits']['five_hour'];print('5h used %s%%, resets %s'%(r['used_percentage'],time.strftime('%H:%M',time.localtime(r['resets_at']))));print('7d used %s%%'%d['rate_limits']['seven_day']['used_percentage'])"
  ```
  **Thresholds:** `five_hour.used_percentage` **< 85** → dispatch freely. **85–94** → finish work
  already in flight on the CURRENT story (a re-work implementer, a gate, a reality gate) but do NOT
  start a new story's implementer. **>= 95** → park until `resets_at`, then resume from the board.
  Separately, `seven_day >= 90` → tell the PO instead of parking; a 7-day reset cannot be waited
  out inside a session.
  **Recording:** every park updates `.scrum/session.lock`'s `NEXT:` line with the head commit, the
  percentage, the reset time and the exact next step, so a session that dies anyway resumes at the
  same place; parks are summarised in the sprint's `review.md` as process data for the retro.
  **Caveat, stated because it bounds the rule:** the file is only rewritten when the statusline
  renders, so it can lag during a long agent run. It is accurate at an agent boundary, which is
  the only moment this rule reads it.
  (PO directive 2026-07-29, mid-sprint-63: "just check after each agents work is done if the
  session limit is near end; if it is near end then pause until the reset time and continue",
  refined to per-agent granularity: "what I meant is you can pause after any agent." Motivating
  history: sprint 46 was pushed to an external agent by a session limit; sprint 45 consumed two
  full 5-hour windows; STORY-149's first implementer died mid-story on a session limit. In all
  three the limit arrived unseen — this rule exists because it no longer has to.)
  (Rung: prose + an inlined mechanical command. The script rung WAS considered and is where this
  belongs long-term — the check is pure arithmetic over a JSON file and would be project-generic,
  since `statusline-latest.json` is a Claude Code artifact, not a project one. It is not taken now
  for two reasons: tooling is frozen mid-sprint by the 2026-01-01 agreement, and the 2026-07-15
  entry forbids ad-hoc skill-script edits outside a story. File it at the sprint-63 retro.)

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
  (b) **Clean-container gates:** before any full gate run, stop idle dev-DB containers so only the
  gate's own DB is running (the proven sprint-45 flake root cause was idle-container contention).
  STORY-080 is the durable fix and is PO-prioritized for next refinement; no test is skipped in the
  meantime. (Rung: prose until STORY-080 lands the test-rung fix.)
  (c) **Board evidence hygiene:** at sprint close, superseded `dod_evidence`/`gate_notes` narrative
  moves into the sprint's `review.md`; `sprint-current.yaml` carries only the final evidence block —
  it is re-read at every standup. (Rung: prose.)
  (d) Landed the same day at the script/agent rungs: `yt_wiki.py` format-only auto-verify (a
  whitespace-only diff since `verified_sha` bumps the sha mechanically — one formatter commit had
  re-staled 7 articles) + staleness-amplifier `refs` lint (advisory; `--strict-refs` to block);
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

- 2026-07-15 — **Expedite STORY-080; the dev-db flake is a standing full-gate false-red until it lands**
  (sprint-46 retro). STORY-080 (dev-db container port-collision / connection-disconnect) is elevated to
  top backlog priority to enter the next sprint. It false-red'd BOTH sprint-46 full-gate runs (two
  different `test_dev_db_*` members), each requiring the contention-proof protocol. Correction to the
  proposed interim: pytest here runs SERIALLY (no xdist, no addopts), so "serialize the harness tests"
  is a no-op — the flake is Docker/connection *resource* contention across the full suite (each dev-db
  test spawns its own container; the gate's own DB container aggravates it), which is exactly STORY-080's
  domain. Until it lands, the existing 2026-07-06 contention false-red protocol governs (prove: empty
  diff since sprint cut + passes isolated), and 2026-07-14(b) clean-container hygiene stands. (Rung:
  backlog priority; the durable fix is STORY-080's own test-rung work — not an ad-hoc skill-script edit
  outside a story.)

## Prune record
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
  mid-sequence, resume from the FAILED step, never restart the sequence � completed
  steps (e.g. an ECR push) survive. Motivating incident: sprint-51 redeploy � push
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
