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

<!-- - YYYY-MM-DD — <agreement> (Motivated by: <incident, sprint, story>) (Rung: <ladder rung considered and why prose>) -->
