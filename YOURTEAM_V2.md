# YourTeam v2 — The Complete Record

**What this is:** the comprehensive record of the YourTeam skill redesign — evidence base,
architecture, everything built, the migration, the pilot sprint that proved it, and the
amendments that followed. Dates: 2026-07-12 → 2026-07-13. Status: **shipped on main**,
skill version **2.1.1**.

**Document map:**

| Document | Content |
|---|---|
| `YOURTEAM_INCEPTION.md` | v1 inception (2026-06-23) — the original methodology contract |
| `YOURTEAM_REDESIGN_REVIEW.md` | The architecture review that motivated v2 (43-sprint evidence, 9 issues, 7 redesign moves, roadmap) |
| `YOURTEAM_V2_MIGRATION_MAP.md` | Entry-by-entry routing of ~40 working agreements down the enforcement ladder (PO-approved 2026-07-12) |
| **this file** | The master record and current-state reference |
| `docs/scrum/sprints/2026-07-12-sprint-44/` | The pilot sprint's plan / review / retro — v2's proving ground |
| `.claude/skills/yourteam/SKILL.md` | The living skill itself (generic; start here to operate it) |

---

## 1. Why v2 — the one-paragraph version

Forty-three sprints of v1 proved the *methodology* (mechanical DoD gates, hard-locked sprints,
provenance-tracked wiki, four PO touchpoints) and disproved its *substrate*: nearly every
invariant lived in prose that an LLM had to remember, and the retro loop grew
`working-agreements.md` to ~557 binding lines — most of them patches for failures that
machinery should have prevented. The marquee failure class ("green tests, wrong contract",
7+ incidents) showed that mechanical gates plus dual Opus review verify internal consistency,
not reality. v2's thesis: **apply "mechanical gates over promises" to the process itself.**

## 2. The enforcement ladder — v2's central principle

Every rule lives at the LOWEST rung that can hold it; prose is the residue, not the default:

```
1. Gate command / standing test     (import-linter, the skill self-test)
2. Script                           (yt_gate.py, yt_wiki.py, yt_selftest.py)
3. Hook                             (yt_git_guard.py — fail-closed, PreToolUse)
4. Agent definition                 (model, effort, tool allowlist, report schema)
5. Role checklist                   (.scrum/checklists/*, generated per project)
6. Working agreement                (true process rules only)
```

Retros now route every proposed amendment down this ladder and must name its rung.

## 3. What was built (component inventory)

### 3.1 The team — real agent definitions (`.claude/agents/yt-*.md`)

Replaced v1's markdown prompt-templates (hand-interpolated into generic dispatches) with
harness-enforced definitions. Briefs shrank to variables only (story file, plan steps, branch,
mode flags, verified wiki Facts); each agent loads its own checklist; each returns a strict
YAML report/verdict schema.

| Agent | Model / Effort | Tools | Role |
|---|---|---|---|
| yt-implementer | sonnet / high | all | One story, strict TDD, commit-per-green-step (≤30 min uncommitted, ever), never writes `.scrum/` |
| yt-spec-reviewer | opus / high | read-only + Bash (run tests) | AC compliance with a mandatory AC↔test trace — reads test BODIES; name-matching is not verification |
| yt-quality-reviewer | opus / high | read-only + Bash (run tests) | "Code we want to live with" + the tests-that-lie taxonomy (6 members, all CRITICAL) |
| yt-plan-verifier | opus / xhigh | read-only + Bash (probes) | **New role.** Adversarial pre-lock plan check: units/scale cited from producing code, producer-gap claims proven by live failure-path probes, edge behavior per method, fixture provenance |
| yt-scout | haiku / low | read-only | Fast inventory/reconnaissance; UNKNOWN over guessing |

Reasoning effort is pinned per agent (v2.1.1) — an unpinned effort silently inherits the
session's, and the PO's 2026-07-02 "Sonnet at HIGH" clause had been dropped in migration.

### 3.2 The mechanical floor — scripts (`.claude/skills/yourteam/scripts/`)

- **`yt_gate.py`** — runs every command in `.scrum/definition-of-done.md` (per-section cwd from
  headings), SEQUENTIALLY by construction (the DB-contention rule), refuses dirty trees (gate
  counts only at a committed HEAD), and emits the `dod_evidence` YAML fragment itself — no more
  hand-transcription. UTF-8 capture and output (two pilot bug-fixes).
- **`yt_wiki.py`** — mechanizes the wiki protocol: staleness **sweep** (git arithmetic;
  unresolvable SHA = stale), **facts** coverage lint (every Fact-cited file must be inside its
  article's `code_refs`, else it rots invisibly — first run found 19 real gaps), **links** lint.
  Prints why every unswept article is unswept; an unrecognized `status:` is a finding (a
  comment-blind parser had silently skipped an article — the exact hole the sweep exists to
  close; found and fixed in the pilot).
- **`yt_selftest.py` + `scripts/tests/`** — 28 stdlib-`unittest` tests for the floor itself
  (gate parsing/tails/evidence schema, wiki frontmatter/coverage/links/skip behavior, the
  hook's block/allow matrix as real subprocess runs, template↔instance parity). Run at every
  standup. Added by retro amendment #1: *the gate gets a gate* — three script bugs had surfaced
  only under live load.

### 3.3 Fail-closed guardrails — hook (`.claude/hooks/` + `.claude/settings.json`)

`yt_git_guard.py` (PreToolUse on Bash|PowerShell): during an ACTIVE sprint, blocks bulk staging
(`git add -A`/`.`) and any `git commit` off the sprint/hotfix branch — the two prose invariants
with the worst v1 incident history (a swept state-edit; a whole story committed to master after
a silent checkout failure). Fails open on internal errors; prose rules remain the fallback for
hook-less environments. Fired once in the pilot — correctly, on the orchestrator itself.

### 3.4 Role checklists (`.scrum/checklists/` — GENERATED, project-specific by design)

Four files (implementer, spec-review, quality-review, plan-verification) carrying the ~30
engineering conventions distilled from the retired agreements, each item keeping its
date + motivating-incident provenance. Loaded by the agent that enforces each. This is where
the evidence pointed: standing checklists beat per-story AC wording (the five-file-shape test
was missed twice *despite explicit AC*).

### 3.5 Pipeline changes (SKILL.md + references)

- **Reality gate** — a per-story pipeline stage after the DoD gate: consumer/rendering stories
  get a live render-vs-wire spot check; adapter stories get a live vendor-path probe with full
  event-type enumeration; an AC that cannot execute inside review **blocks or splits** — never
  ships on promise; fixtures derive from real captured samples. (Every major v1 escape was
  ultimately caught only by a live check; this makes reality a stage, not an accreted amendment.)
- **Plan verification gates the lock** — the drafted plan goes to yt-plan-verifier; only
  LOCK_READY plans reach the PO.
- **Execution modes** (`references/execution-modes.md`, new): `in-process` (default) |
  `external` (plan-as-contract + post-hoc verification) | `parallel-waves` (worktree isolation,
  mandatory branch-sync step 0) | `debug` (one-file, no-points record) | `parked` (board
  snapshot + resume path). Declared per sprint in `sprint-current.yaml` (`mode:` field) — one
  line instead of a working-agreement amendment per deviation.
- **Concurrency/isolation pattern** — every concurrently dispatched agent touching a stateful
  resource (DB, container, port) gets its own instance, named in its brief.
- **Cadence policing** — the orchestrator checks `git log` recency at every board touch; a
  >30-minute silent gap = stalled agent (kill, verify tree, fresh dispatch).
- **Ceremony updates** — lock sequence (branch+tag first, board second, commit separately —
  the hook enforces the order); reviews may run concurrently; retro routes amendments down the
  ladder; capacity planning dropped velocity-as-formula (it measured cadence, not capacity).

### 3.6 Multi-project bootstrap (`templates/` + BOOTSTRAP.md)

The skill is self-installing and **project-generic by PO rule** (2026-07-13): scripts and
references are never copied (they read project state at runtime — one copy, fixes propagate);
agent definitions, the hook + settings fragment, and checklist seeds are copied per project at
inception (merge, never overwrite; PO confirms model/effort tiers and hook strictness). Every
generated file carries a `yourteam_version` marker; drift is detected by the parity self-test.
This repo is the reference instantiation.

### 3.7 The great agreements migration

`YOURTEAM_V2_MIGRATION_MAP.md`, PO-approved and executed 2026-07-12: ~40 of ~45 entries routed
off `working-agreements.md` (~557 → ~100 lines). What remains as prose: the 5 defaults, the
5 PO inception rules, the contention false-red protocol (a judgment procedure), and PO-stated
rules (model/effort tiering became agent frontmatter; the genericity rule was added 07-13).
Full pre-prune text preserved in git history (`git show b025b3c:.scrum/working-agreements.md`).

## 4. The pilot — sprint 44 (2026-07-12/13, mode: in-process, 5 pts, accepted 5/5)

Two stories chosen to exercise every component once: **STORY-064** (HTTP status code + check
type threaded from live Dynatrace through normalizer → domain → migration → DTO → frontend)
and **STORY-079** (the wiki Facts-coverage cleanup the new lint demanded).

**What each layer caught — the pilot's real evidence:**

| Layer | Catch |
|---|---|
| Baseline gate (planning) | Unformatted v2 scripts; `lint-imports.exe` blocked by a new Windows Application Control policy → DoD command moved to the module path, CLAUDE.md synced |
| **Plan verifier (round 1: GAPS)** | Checked-in fixtures stored `response_status_code` as int `200` vs the string-typed real wire — the str→int parse would have shipped green-but-untested (the S32 class, killed pre-lock) |
| Hook | Blocked the orchestrator's own mis-sequenced lock commit (checkout+commit chained) |
| Crash recovery | Implementer connection-drop mid-wiki-pass; loss = one article's frontmatter (commit cadence + per-article commits + edge-case #13 tail completion) |
| Spec review | AC↔test trace run live; rewrite-not-delete check on the inverted column test |
| **Quality review (079: FIX_REQUIRED)** | 3 MAJORs on *prose*: two over-broad hot-file `code_refs` (CLAUDE.md, pyproject.toml — the false-stale busywork mode) + a Fact contradicting its own frontmatter → fresh-agent fix loop → APPROVE |
| **Reality gate** | Live render-vs-wire EXACT match: wire `{code: 200, check_type: "http", latency_ms: 531}` → grid `HTTP · 200 · 531 ms`; 120 live-ingested rows |
| Self-inflicted findings | 3 tooling bugs (yt_gate cp1252 capture, UTF-8 stdout, yt_wiki comment-blind parser) — fixed in-sprint, then pinned by the self-test suite; STORY-080 filed (hardcoded test port, contention proven per protocol) |

**All five pilot success criteria MET** (scorecard in the sprint's `review.md`). PO accepted
both stories; the fast-forward merge to main (`e9840b7`) landed the stories AND v2 together.

## 5. Post-pilot amendments

- **v2.1** (`4bb2e54`, retro-approved): the self-test suite; lock-sequence ceremony fix;
  generic stateful-resource isolation pattern; sweep-skip visibility; the PO genericity rule
  recorded in `working-agreements.md` and SKILL.md.
- **v2.1.1** (`54f8525`, PO catch at review): reasoning effort pinned per agent — definitions
  had pinned model but not effort, so dispatches inherited the session's effort and the
  2026-07-02 HIGH-effort clause had been silently dropped in migration.

## 6. Operating v2 — the flow at a glance

```
Session start   standup: lock check → yt_selftest → yt_wiki (sweep) → board report → resume
Refinement      scouts/probes ground AC in reality BEFORE estimating (probe > promise)
Planning        draft plan.md → yt-plan-verifier (LOCK_READY gates the lock) → PO approves
                goal + stories + MODE → branch+tag, then board, then commit (hook-safe order)
Per story       yt-implementer (TDD, commit-per-green-step)
                → [3+ pts] yt-spec-reviewer ∥ yt-quality-reviewer (isolated DBs)
                → yt_gate.py (evidence written mechanically)
                → reality gate (live render-vs-wire / vendor probe)
                → board: done (orchestrator is the SOLE .scrum writer)
Sprint end      yt_wiki exit 0 (compile pass) → review.md → PO verdicts → merge LAST
Retro           amendments routed down the ladder, each naming its rung
```

## 7. Known gaps and the road ahead

- **Untested in anger:** `external` and `parallel-waves` modes (written from the v1 evidence
  that improvised them); the bootstrap into a genuinely fresh repo — that is the next
  milestone, together with relocating the skill to `~/.claude/skills/yourteam/`.
- **`.scrum` write-protection** stays agent-definition prose — the harness doesn't expose
  agent identity to hooks (watch-item).
- **STORY-080** (gate port-collision defect) should enter the next sprint — a flaky gate is
  never left standing.
- **Prose-regrowth watch:** does retro routing keep `working-agreements.md` small over the
  next ten sprints? That is the long-run test of the ladder.

## 8. Key commits

| SHA | What |
|---|---|
| `e4d0c98`…`b025b3c` | v2 build: agents+checklists, scripts, hook, skill docs+templates, review+map |
| `a3ba958` | PO-approved agreements migration executed (~557 → ~100 lines) |
| `024e6c6`…`f50bfc6` | Pilot sprint 44 (33 commits: lock → stories → reviews → fix loop → close) |
| `e9840b7` | Sprint 44 + YourTeam v2 fast-forward-merged to main |
| `4bb2e54` | v2.1 — pilot amendments (self-test suite et al.) |
| `54f8525` | v2.1.1 — per-agent reasoning effort pinned |
