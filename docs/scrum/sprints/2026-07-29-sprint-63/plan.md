# Sprint 63 plan — the demo fleet runs, and the engine stops lying about itself

**Status: DRAFT, not locked.** Awaiting PO approval.

## Goal

Make the demo engine actually *drive* the system: a scripted scenario player, a ≥12-component
fictional fleet in STORY-146's nested config shape, and an end-to-end run of the **unmodified**
`python -m src.composition.run` producing real observations for a fleet that does not exist —
with a publish guard that holds even though real Statuspage credentials sit in the repo-root
`.env`. Alongside it, close the two demo-engine defects that only start to matter once the engine
is long-running, and retire twelve stale code references that no gate can see.

**Not in this sprint:** any frontend work (the design-system + shell sprint comes later, and opens
with a PO look-and-feel checkpoint); any failure-path scenario (STORY-177 — see the scope note in
STORY-176); STORY-147 (re-deferred 2026-07-29 to land with its consuming frontend).

## Scope — 8 points, 3 stories

| Order | Story | Pts | Ceremony | Why here |
|---|---|---|---|---|
| 1 | **STORY-180** — demo-engine polish (8 deferred minors) | 2 | 1–2 pointer: implementer → gate → reality gate | Opens `tools/demo_engine/` first so STORY-176 inherits a bounded token cache and a window that cannot diverge silently, instead of working around them and forcing rework on files it just restructured |
| 2 | **STORY-176** — scenario player, demo fleet, real loop run | 4 | 3+ pointer: implementer → spec ∥ quality → gate → reality gate | The risk peak and the sprint's reason to exist. Gets the bulk of the time |
| 3 | **STORY-181** — retire 12 stale code references | 2 | 1–2 pointer: implementer → gate → reality gate | Fully independent, comment-only, cannot block anything. Deliberately last |

**Order tradeoff, stated rather than hidden.** The skill's default is high-risk-first, which would
put STORY-176 at position 1. I am putting the 2-point STORY-180 ahead of it because the two touch
the same files (`tools/demo_engine/store.py`, `server.py`) and STORY-180's fixes are *about* the
long-running behaviour STORY-176 introduces — doing them after means either rework or a workaround
baked into 176. The cost of being wrong is small: if STORY-176 blocks late, the sprint still
delivers 4 points of completed work, and STORY-180 is short enough that it cannot eat the sprint.

**Mode: `in-process`** — the standing directive after the sprint-60 external rejection ("you only
implement"). Every story gets the DoD gate plus a reality gate.

## Branch and baseline

- **Branch `sprint-63` from `sprint-62`, NOT from main.** The PO accepted sprint 62 but kept it
  unmerged (standing "don't merge with main"), so `main` (`debug/ingest-stall-sample-mode`, tip
  `517fc38`) does not contain STORY-146's config shape or STORY-148's engine — both of which
  STORY-176 `depends_on`. Branching from main would be branching from a repo where this sprint's
  prerequisites do not exist.
- **Baseline:** sprint 62 closed with the full 8-command gate GREEN at `2b0bf86` (pytest 572,
  8 import contracts, npm 363/build/lint). Commits after it are docs and `.scrum/` state only.
  Re-run the backend five at the branch point before dispatching story 1, so a red inherited from
  the branch operation itself cannot be mistaken for a story's doing.

## Verified contracts (re-verified at HEAD `95afc97`, 2026-07-29)

STORY-176's carry note (`docs/scrum/sprints/2026-07-28-sprint-62/story-176-carried-to-sprint-63.md`)
warned that its citations were confirmed at `57aa523` and that STORY-146 changed `config.py`
beneath them. **All fifteen were re-checked by reading the code. Twelve hold exactly; three
drifted and are corrected here.** Use these addresses, not the story's or the carry note's.

### Publish exposure — the safety-critical chain

| Claim | Address (verified) | Status |
|---|---|---|
| The loop builds its publisher inside `build_live_loop`, no injection point | `run.py:121-128` | ✅ exact |
| `load_dotenv()` walks up from the **source file**, not CWD — so the repo-root `.env` supplies real credentials from any launch directory | `run.py:178` | ✅ exact |
| **The one gate both routes pass through** — `if statuspage_page_id and statuspage_api_token and component_mapping:` | `publish_helper.py:211` | ✅ exact |
| `StatusWritebackPublisher.publish` makes no external call (Dynamo `set_status`, then delegate) | `publish_helper.py:172-180` | ✅ exact |
| Route 2: the API's approve trigger builds its own publisher from its OWN config | `app.py:160-183` (mapping `171-175`, `build_publisher` `176-183`) | ⚠️ story says `160-182`; the block ends at 183 |
| `statuspage_mapping()` includes only components with a non-None `statuspage_component_id` | **`config.py:554-564`** | ⚠️ **story says `292-299` — STORY-146's rewrite moved it 260 lines. Semantics identical.** |
| The API's other publisher branches reach only `LoggingPublisher` | `app.py:184-196` | ✅ exact |
| `ApprovalService` takes the injected publisher, never builds one | `app.py:198-206` | ✅ verified |
| `CONFIG_DIR` defaults to `config/apps` | `settings.py:32` | ✅ exact |
| The live config that must NOT be loaded by either process declares a real component id | **`config/apps/httpcheck.yaml:8`** | ⚠️ **story says `:6` — STORY-146's nested rewrite moved it.** |
| `decide` publishes recoveries with **no human gate** | `decide.py:122-126` | ✅ exact |

### Ingest and time base

| Claim | Address (verified) | Status |
|---|---|---|
| Rolling window `since = until - (max_threshold + 2) * interval` | `orchestrate.py:94-98` | ✅ exact |
| `SignalObservation` rejects naive/non-UTC `observed_at` | `signal.py:81-92` | ✅ exact |
| A failed cycle is **logged with a traceback**, not silent | **`composition/pull_loop.py:200-207`** | ⚠️ **the file is under `composition/`, not `adapters/inbound/`. Lines exact.** |
| `check_vendor_id_health` runs before any loop is built | `run.py:196` | ✅ exact |
| `_HEALTH_CHECK_WINDOW = "2h"`, and count 0 → WARN "VENDOR-ID DRIFT SUSPECTED" | `vendor_health.py:37`, `:113-124` | ✅ exact |
| Only `"0"`/`"HEALTHY"` maps to UP — and it is an **`or`**, so either half alone suffices | `health_mapping.py:65` | ✅ exact (this is also STORY-180 minor 6: `rows.py` calls it "the ONLY pair", which overstates) |
| One bad row loses the whole batch (bare comprehension) | `dispatch.py:80` | ✅ exact |
| Monkeypatching is the only route to a DOWN — unavailable over a socket | `test_pull_loop.py:139-145` | ✅ exact |

## Story 1 — STORY-180, demo-engine polish (2 pts)

AC and the eight minors: `docs/scrum/stories/STORY-180-demo-engine-polish.md`.

### Steps
- [ ] 1. Minor 6 (AC1): correct `rows.py:36-37` against `health_mapping.py:65`'s `or` — "the ONLY
      pair accepted" is false; either half alone suffices. Read the operator, don't reword the
      sentence.
- [ ] 2. Minor 1 (AC2): make the vendor-health window unable to diverge — parse it from the query,
      or add a test that fails if `store.py`'s constant and `vendor_health.py:37` disagree.
- [ ] 3. Minor 5 (AC4): bound `_DemoHTTPServer.results` (`server.py:47`) with a test proving the
      bound.
- [ ] 4. Minor 2 (AC3): route the 0- and 6-digit watermark cases through the real
      `build_dql_query`; keep the 9-digit literal with its reason stated at the literal.
- [ ] 5. Minors 3, 4, 7 (AC5): fold the stdlib-only test into a docstring; rename the overstated
      test; drop the unused clock read from the ingest path. State the test-count drop.
- [ ] 6. Minor 8 (AC6): decide the `sys.path` insertion position explicitly and record the reason
      in `conftest.py`.

### Reality gate (180) — must be shown able to fail
Per the sprint-62 retro amendment A1. The load-bearing new guarantee is AC2, so: in a worktree,
change `vendor_health.py`'s `_HEALTH_CHECK_WINDOW` to `"3h"` and confirm the new test/parse goes
**RED**; restore. A guard that stays green when the constant it guards moves is not a guard.
Record both outcomes in `reality_gate.discrimination_proof`.

## Story 2 — STORY-176, scenario player + demo fleet + real loop run (4 pts)

AC: `docs/scrum/stories/STORY-176-demo-fleet-scenarios-and-loop-run.md` (9 ACs, already rescoped
for PO decision D-A: **UP + absence only**). The carry note holds the original step sketch — read
the story, not the note, where they disagree.

### Steps
- [ ] 1. **AC3(a) first, before any loop is ever started.** Author the demo config declaring **no**
      `statuspage_component_id` on any component; assert `statuspage_mapping() == {}` and that
      `build_publisher` with an empty mapping and non-empty credentials returns a chain whose
      delegate is a `LoggingPublisher`.
- [ ] 2. **AC3(b):** prove the **running API's** runtime mapping is `{}` — against the live
      process, not only the loaded config — with `CONFIG_DIR` set on the API too. Document
      `CONFIG_DIR` as required on **both** processes, naming both publish routes.
- [ ] 3. Scenario file format + player (AC1): per-signal, per-cycle, per-location outcomes expanded
      to rows at each monitor's own `interval_seconds`; test exact row counts.
- [ ] 4. Time base (AC2 a–e): anchor to `clock.now()` inside the 7-cycle window; 9-digit `Z`
      timestamps; monotonic across queries; intervals ≤ 60 s; **≥2 h backfill** relative to each
      request instant, so `check_vendor_id_health` does not report 40+ dead ids at t₀.
- [ ] 5. The fleet (AC4): ≥12 components, ≥40 signals, ≥4 locations, nested shape, declared
      `locations:` + `freshness:`. Fabricated `SYNTHETIC_LOCATION-*` ids are fine here.
- [ ] 6. Scenarios (AC5 a–e): clean fleet; fully dark location; fully dark monitor; staggered
      intervals; late-returning monitor.
- [ ] 7. The run (AC6): unmodified `python -m src.composition.run`, `DYNATRACE_ENV_URL` → the demo
      engine, `CONFIG_DIR` → the demo config. Verify via the observations table **and**
      `GET /api/v1/components` + `/api/v1/topology` over live HTTP; `check_vendor_id_health`
      reports no dead ids.
- [ ] 8. AC7: assert `/api/v1/approvals` returns a well-formed **empty** result and say plainly in
      the demo README that the approval path is NOT exercised until STORY-177.
- [ ] 9. AC8: verify mechanically that no file under `backend/src/` changed.

### Reality gate (176) — two-sided on the safety claim
The loop run *is* the gate, but a run that ingests cleanly proves nothing about the guard. Both
sides are required, per A1:
1. **Positive:** the full run ingests ≥12 components / ≥40 signals / ≥4 locations, visible over
   live HTTP, with no dead monitor ids and an empty-but-well-formed approvals response.
2. **Discriminating:** with a config that DOES declare a `statuspage_component_id`, the same
   runtime check must show a **non-empty** mapping and a real `StatuspagePublisher` selected — run
   against a throwaway config with a fake component id and **no** network call permitted (assert
   the selected publisher type; do not publish). A guard whose check cannot come back "unsafe" is
   not evidence.
3. **Backfill, both ways:** with an engine that has no history, `check_vendor_id_health` WARNs for
   every signal; with ≥2 h of backfill it is silent. Only the pair proves the second grammar works.

⚠ **`decide` publishes recoveries with no human gate** (`decide.py:122-126`). No demo loop starts
until steps 1–2 pass. Additionally, run with `STATUSPAGE_API_KEY` unset as belt-and-braces and
record that in the evidence — the config guard is the contract, the unset key is the seatbelt.

## Story 3 — STORY-181, retire stale code references (2 pts)

AC: `docs/scrum/stories/STORY-181-retire-stale-code-references.md` (12 sites, 8 ACs).

### Steps
- [ ] 1. (A) Dead platforms: `run.py:177`, `client.ts:18-19`.
- [ ] 2. (B) Phantom classes: `component.py:17`, `publication.py:35`,
      `component_repository.py:53` — preserve each claim, fix the citation.
- [ ] 3. (B) Remaining retired-persistence prose: `persistence/__init__.py:1`,
      `ports/__init__.py:7`, `run.py:4`, `windowState.ts:8` (keep the invariant), `pyproject.toml:50`.
- [ ] 4. (C) Dead story pointers: `middleware.py:4` (state that no CORS is needed at all),
      `actor.ts:3-5` (auth is unassigned).
- [ ] 5. AC7: re-scan `CLAUDE.md` + `docs/scrum/wiki/` for the same phrases (expected no-op after
      `e9a8ad3`, but verified ≠ assumed).

### Reality gate (181) — the grep that must be empty, and must have been non-empty
AC6's scan returns zero hits at the story head. Its discrimination proof is free and exact: run
the identical scan at the story's parent commit and record **12 hits**. Same shape as STORY-149's
pre-fix run — a check that was never capable of failing proves nothing.

## Tooling notes (known friction, not blockers)

- **STORY-179** — `dynamo_local` picks an ephemeral host port Docker maps but Windows won't route.
  Every DynamoDB-gated run this sprint needs `DYNAMO_ENDPOINT_URL` pointed at a fixed-port
  container; record it as an `env_note` on each gate record, as sprint 62 did.
- **STORY-178** — `yt_gate.py`'s emitted fragment carries ESC bytes from `npm run build`, making it
  invalid YAML. Strip before merging and record the strip. Third sprint running.
- **Retro amendment A1 now binds:** every `reality_gate` record needs
  `discrimination_proof` **or** `two_sided_note`. All three gates above are written to satisfy it.
- **Retro amendment A2 now binds:** behavioural wiki Facts cite the test that pins them. Relevant
  to the demo-engine article's blast radius when STORY-176 lands.

## Wiki blast radius (expected)

`demo-engine.md` (all of STORY-180 and most of 176), `config-layer.md` (the demo config shape),
`dev-setup-and-dod.md` + `CLAUDE.md` (the demo run recipe and `CONFIG_DIR`-on-both-processes),
`ingest-service-and-pull-loop.md` and `statuspage-publish.md` (the publish guard). STORY-181's
diff touches `code_refs` in several articles while changing no behaviour — those get explicit
re-verification, not a bulk SHA stamp.

## Plan verification

This sprint **is** contract-sensitive (a vendor-path adapter, a real loop run, and a
safety-critical publish guard), so `yt-plan-verifier` is dispatched before the PO sees this plan,
per the token-economy amendment's criteria. Its findings are folded in above before lock.
