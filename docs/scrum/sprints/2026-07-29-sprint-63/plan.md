# Sprint 63 plan — the demo fleet runs, and the engine stops lying about itself

**Status: DRAFT, not locked.** Awaiting PO approval.

## Goal

Build everything the demo run needs and make it **safe to attempt**: a scripted scenario player,
a ≥12-component fictional fleet in STORY-146's nested config shape, a time base whose six
constraints are each asserted, and a publish guard that holds even though real Statuspage
credentials sit in the repo-root `.env`. Alongside it, close the two demo-engine defects that only
start to matter once the engine is long-running, and retire sixteen stale code references that no
gate can see.

**The run itself is STORY-182, sprint 64** — split out at planning after the verifier re-estimated
the combined story at 6 points. This sprint ends with the fleet authored, the player tested and the
guard proven; nothing is launched.

**Not in this sprint:** the loop run itself (STORY-182, sprint 64); any frontend work (the
design-system + shell sprint comes later, and opens with a PO look-and-feel checkpoint); any
failure-path scenario (STORY-177 — see the scope note in STORY-176); STORY-147 (re-deferred
2026-07-29 to land with its consuming frontend).

## Scope — 7 points, 3 stories

| Order | Story | Pts | Ceremony | Why here |
|---|---|---|---|---|
| 1 | **STORY-180** — demo-engine polish (8 deferred minors) | 2 | 1–2 pointer: implementer → gate → reality gate | Opens `tools/demo_engine/` first so STORY-176 inherits a bounded token cache and a window that cannot diverge silently, instead of working around them and forcing rework on files it just restructured |
| 2 | **STORY-176** — part 2a: scenario player, demo fleet, time base, publish guard | 3 | 3+ pointer: implementer → spec ∥ quality → gate → reality gate | The risk peak. Everything that must be true **before** a loop may be started |
| 3 | **STORY-181** — retire 16 stale code references | 2 | 1–2 pointer: implementer → gate → reality gate | Fully independent, comment-only, cannot block anything. Deliberately last |

**Split at planning (PO decision, 2026-07-29).** `yt-plan-verifier` re-estimated the combined
STORY-176 at **6 points**, not 4 — evidence, not feel: STORY-148 delivered the entire wire contract
(rows, both grammars, store, HTTP server, 23 tests) for 3 points, while the combined story
additionally carried a YAML schema and player, a ≥12-component/≥40-signal/≥4-location config
authoring task, five scenarios, a three-process live run under two known env-friction defects, three
publish-guard checks, and a two-sided gate needing a second config and a second run. The PO chose to
split rather than cram (standing pacing directive):

- **STORY-176 (this sprint, 3 pts)** — the player, the fleet, the time base, the publish guard.
- **STORY-182 (sprint 64, 3 pts)** — the real loop run and its two-sided gate. AC6/AC7 moved there.

The split is structural, not cosmetic: STORY-176's guard checks are exactly what must pass **before
any loop starts** (`decide` publishes recoveries with no human gate, `decide.py:122-126`, published
at `:171-172`), so putting the run in its own story makes that ordering impossible to reshuffle.

**Order tradeoff, stated rather than hidden.** The skill's default is high-risk-first, which would
put STORY-176 at position 1. I am putting the 2-point STORY-180 ahead of it because the two touch
the same files (`tools/demo_engine/store.py`, `server.py`) and STORY-180's fixes are *about* the
long-running behaviour the demo run introduces — doing them after means either rework or a
workaround baked in. `yt-plan-verifier` agreed with the order, on one condition it raised: STORY-180
AC2's route had to be **decided at planning** rather than left as an either/or, because the two
routes need opposite reality gates and an undecided route is exactly what makes story 1 expand and
story 2 start late. That route is now fixed (equality test, not parse).

**Mode: `in-process`** — the standing directive after the sprint-60 external rejection ("you only
implement"). Every story gets the DoD gate plus a reality gate.

## Branch and baseline

- **Branch `sprint-63` from `sprint-62`, NOT from main.** The PO accepted sprint 62 but kept it
  unmerged (standing "don't merge with main"), so `main` (tip **`517fc38`**) does not contain
  STORY-146's config shape or STORY-148's engine — both of which STORY-176 `depends_on`. Branching
  from main would be branching from a repo where this sprint's prerequisites do not exist.
  (`main` and `debug/ingest-stall-sample-mode` (tip `1257cc9`) are **two different branches**; an
  earlier draft of this line conflated them. Both are ancestors of HEAD, so the conclusion stands.)
- **Baseline:** sprint 62 closed with the full 8-command gate GREEN at `2b0bf86` (pytest 572,
  8 import contracts, npm 363/build/lint). Commits after it are docs and `.scrum/` state only.
  Re-run the backend five at the branch point before dispatching story 1, so a red inherited from
  the branch operation itself cannot be mistaken for a story's doing.
- **Clean tree at the branch point**, verified — not assumed. `yt-plan-verifier` independently
  confirmed `2b0bf86` exists, `pytest --collect-only` = 572, eight `importlinter` contracts in
  `pyproject.toml`, and that every commit after the baseline touches only `docs/`, `.scrum/`,
  `CLAUDE.md` and `frontend/README.md`. The stray repo-root `package.json`/`package-lock.json`/
  `node_modules/` were deleted 2026-07-29, so nothing is untracked.

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
| `decide` publishes recoveries with **no human gate** | decision at `decide.py:122-126`, **the publish call itself at `:171-172`** | ⚠️ corrected: `122-126` *decides*; citing it alone as "publishes" over-claims |

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

**Citations corrected pre-lock.** `yt-plan-verifier` re-checked all eight of this story's addresses
(I had verified STORY-176's fifteen and inherited these unchecked). **Five had drifted**, one
dangerously:

| Minor | Cited | Actual | Note |
|---|---|---|---|
| 6 | `rows.py:36-37` | **`rows.py:26-27`** | `36-37` is the *nanosecond-format* docstring — a literal implementer edits the wrong text and reports AC1 done |
| 7 | `store.py:57-61` | **`store.py:46-50`** | `57-61` is `_answer_ingest`'s comprehension |
| 5 | `server.py:47` | **`server.py:48`** | `:47` is `self.store = store` |
| 4 | `test_assumed_failure_codes.py:29-40` | **`:26-37`** | cited range spanned into the next test |
| 2 | `test_watermark_precision.py:19-26` | **`:20-27`** | off by one |
| 1, 3, 8 | `store.py:22`, `test_watermark_precision.py:63-70`, `conftest.py:30` | — | exact |

Also corrected: minor 1's premise. It said `parse_query` "discards the `from:now()-2h` clause it
parsed" — there is **no `from:` regex at all** (`query_grammar.py:28-31`) and `VendorHealthQuery`
(`:47-51`) has no window field. The clause is never parsed.

### Steps
- [ ] 1. Minor 6 (AC1): correct **`rows.py:26-27`** against `health_mapping.py:65`'s `or` — "the
      ONLY pair accepted" is false; either half alone suffices. Read the operator, don't reword it.
- [ ] 2. Minor 1 (AC2), **route decided at planning — equality test, not parse**: a test importing
      `vendor_health.py:37`'s `_HEALTH_CHECK_WINDOW` fails if it disagrees with `store.py:22`.
- [ ] 3. Minor 5 (AC4): bound `_DemoHTTPServer.results` (**`server.py:48`**) with a test proving it.
- [ ] 4. Minor 2 (AC3): route the 0- and 6-digit watermark cases through the real `build_dql_query`
      **with `overlap=timedelta(0)`** — at the 5-minute default the bound lands before the row, the
      row is included regardless of precision handling, and the test silently stops discriminating
      the STORY-051 stall while staying green. Keep the 9-digit literal with its reason.
- [ ] 5. Minors 3, 4, 7 (AC5): fold the stdlib-only test into a docstring; rename the overstated
      test (**`:26-37`**); drop the unused clock read (**`store.py:46-50`**). State the count drop.
- [ ] 6. Minor 8 (AC6): decide the `sys.path` insertion position explicitly, record the reason.

### Reality gate (180) — route-matched, per working agreement A1
The load-bearing new guarantee is AC2. Because the route is now fixed to the **equality test**, the
discrimination proof is unambiguous: in a worktree, change `vendor_health.py:37` to `"3h"` and
confirm the new test goes **RED**; restore. Record both outcomes in
`reality_gate.discrimination_proof`.

*Why the route had to be decided first:* under the parse route the same edit would correctly change
**nothing** (the engine would follow the query), so this proof would have scored FAIL against a
correct implementation. A gate and an undecided implementation choice cannot both be right.

## Story 2 — STORY-176, part 2a: player, fleet, time base, publish guard (3 pts)

AC: `docs/scrum/stories/STORY-176-demo-fleet-scenarios-and-loop-run.md` — **amended pre-lock**:
AC2 gained a sixth constraint and a decided timeline direction; AC3 gained a third mechanical check
and a satisfiable observation mechanism; AC5(b)(c)(e) were reworded to their real effects; AC6/AC7
moved to STORY-182; AC8 names the config dir and the `app.id` trap.

### Steps
- [ ] 1. **AC3 first — the guard, before anything else exists.** Author `config/demo/` declaring
      **no** `statuspage_component_id`; assert `statuspage_mapping() == {}`; assert `build_publisher`
      with an empty mapping and non-empty credentials yields a `LoggingPublisher` delegate.
- [ ] 2. **AC3(c) — the bypass the verifier found.** Assert
      `set(demo ids) & set(load_config("config/apps") ids) == set()`. `StatuspagePublisher` keys on
      the canonical component id (`statuspage/__init__.py:41-46`), so a demo id colliding with
      `http-check` on an API running the DEFAULT `CONFIG_DIR` — which is what CLAUDE.md's own recipe
      step 4 does — PATCHes the **real** page. The only automatic layer is `UnmappedComponentIdError`
      (`:43`) swallowed by `BestEffortPublisher` (`publish_helper.py:59-66`), and it saves a
      NON-colliding id only.
- [ ] 3. **AC3(b) — in-process, not over HTTP.** `CONFIG_DIR=config/demo python -c "...create_app()..."`
      asserting `app.state.seed_config.statuspage_mapping() == {}` and the delegate's type. All 14
      v1 routes were enumerated: **none** exposes the mapping, the publisher or the loaded config, so
      the original "assert against the live process over HTTP" needed a `backend/src` change that
      AC8 forbids — the same unsatisfiable-AC shape this story already hit once before lock.
- [ ] 4. Scenario file format + player (AC1), **past-anchored** (decided at planning): expand
      **backwards from `clock.now()`**, not forwards from t0.
- [ ] 5. Time base (AC2 a-f), all six asserted — including the new **(f)**: `FUTURE_TOLERANCE = 5min`
      (`ingest_service.py:37`) quarantines future-dated rows at `:119-125`, and `run.py` passes no
      `on_cycle`, so the rejected count is **discarded — nothing logs it**. Forward playback would
      have hit this on every cycle beyond t0+5min; past-anchored expansion avoids it entirely.
- [ ] 6. The fleet (AC4/AC8): `config/demo/`, >=12 components, >=40 signals, >=4 locations, nested
      shape, declared `locations:` + `freshness:`, and **a distinct `app.id` per file** —
      `config.py:585-587` silently discards a duplicate `app.id`'s `locations`/`freshness`, so a test
      asserts every declared block survives loading.
- [ ] 7. Scenarios (AC5 a-e) with the **reworded** claims: clean fleet; dark location → lower
      `distinct_locations` on `/availability` (NOT a completeness swing — the denominator uses
      OBSERVED locations, `availability.py:265`/`:74`); dark monitor → empty window → `streak None`
      → NOOP (`orchestrate.py:113-121`); staggered intervals; late return → ingest resumes.
      **None of `expected_locations`/`freshness_for`/`stale_after_cycles`/`reentry_cycles` has any
      consumer under `backend/src`** (verified by grep; `config.py:261` says so itself), so these
      scenarios are fixtures for STORY-151/152, not tests of freshness logic.
- [ ] 8. AC8: verify mechanically that no file under `backend/src/` changed.

### Reality gate (176) — two-sided on the guard, which is the whole point
The run is **not** in this story, so the gate is the guard itself:
1. **Safe side:** the demo config yields `statuspage_mapping() == {}`, a `LoggingPublisher`
   delegate, and disjoint ids — asserted in-process with `CONFIG_DIR` set.
2. **Unsafe side (the discrimination proof):** with a throwaway config that DOES declare a
   `statuspage_component_id` (a fake vendor id), the same checks must report a **non-empty** mapping
   and a real `StatuspagePublisher` selected. **Assert the publisher's TYPE; make no network call.**
   A guard whose check cannot come back "unsafe" is not evidence.
3. **The collision case, explicitly:** a config declaring `http-check` must be caught by AC3(c)'s
   disjointness check. Run it and record the catch.

No loop is started in this sprint at all. `decide` publishes recoveries with no human gate
(decision at `decide.py:122-126`, publish call at `:171-172`) — that is precisely why the guard
ships a sprint ahead of the run.

## Story 3 — STORY-181, retire stale code references (2 pts)

AC: `docs/scrum/stories/STORY-181-retire-stale-code-references.md` — **expanded pre-lock from 12
sites to 16.**

`yt-plan-verifier` reproduced my twelve exactly, confirmed every one is genuinely stale, then found
four the phrase list structurally could not see (family (D)): `run.py:170` (`DATABASE_URL` —
**seven lines above** the in-scope `:177`), `query.py:15` (`UNIQUE(observations.source_event_id)`, a
constraint that no longer exists), and two "INSERT ... ON CONFLICT DO NOTHING" descriptions of a
DynamoDB transaction (`ports/observation_repository.py:5`, `ingest_service.py:101`).

### Steps
- [ ] 1. (A) Dead platforms: `run.py:177`, `client.ts:18-19`.
- [ ] 2. (B) Phantom classes: `component.py:17`, `publication.py:35`,
      `component_repository.py:53` — preserve each claim, fix the citation.
- [ ] 3. (B) Remaining retired-persistence prose: `persistence/__init__.py:1`,
      `ports/__init__.py:7`, `run.py:4`, `windowState.ts:8` (keep the invariant),
      `pyproject.toml:49-51` — correct the **whole** sentence: `inbound.dynatrace` and
      `outbound.statuspage` both exist now, so "do not exist yet" is wrong about all three, not just
      `persistence.neon`.
- [ ] 4. (C) Dead story pointers: `middleware.py:4`, `actor.ts:3-5`.
- [ ] 5. (D) The four SQL-prose sites above — keep each claim (idempotent insert, no duplicate on
      replay), drop the SQL mechanism that never ran here.
- [ ] 6. AC7: re-scan `CLAUDE.md` + `docs/scrum/wiki/`. Expected no-op after `e9a8ad3`, but verified
      is not the same state as assumed. `.scrum/definition-of-done.md` is **out of scope** — it had
      the same rot ("the five contracts", three lines under a line already saying "same 8
      contracts") and the orchestrator fixed it at planning, because implementers may never write
      `.scrum/` state.

### Reality gate (181) — the grep that must be empty, and must have been non-empty
AC6's scan returns zero hits at the story head; the same scan at the parent commit records **16**.
**The scan must pass `--include="*.py" --include="*.ts" --include="*.tsx"` (or `-I`)** — without it,
`grep -rn "Postgres[A-Za-z]*Repository" backend/src` returns **15** hits against **3** real ones,
the other twelve being `__pycache__` binaries left by the SQL repositories STORY-087 deleted. An AC
whose scan can never come back empty sends the implementer hunting phantoms.

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
16-site diff touches `code_refs` in several articles while changing no behaviour — those get explicit
re-verification, not a bulk SHA stamp.

## Plan verification — `yt-plan-verifier`, verdict GAPS, all folded in

Dispatched before the PO saw this plan (the sprint is contract-sensitive: a vendor-path adapter, a
real loop run, a safety-critical publish guard). It returned **9 findings, 6 of them blocking**, and
I verified every blocker at source myself before acting. Two were errors of mine.

**It confirmed:** my three corrected STORY-176 addresses are right and the other twelve hold; the
publish-route enumeration is complete (`publish_helper.py:211-221` is the only
`StatuspagePublisher`/`make_statuspage_executor` construction anywhere under `backend/src`,
`scripts/`, `infra/`, `tools/`, the Dockerfile; `build_publisher` has exactly two production call
sites; no outbox/retry/`BackgroundTasks`; `api.statuspage.io` appears once); STORY-181's twelve sites
reproduce exactly and are all genuinely stale; the baseline claims (572 tests, 8 contracts, clean
tree); and my watermark-carryover hypothesis is **not reachable** (`advance` is an unconditional put
and the bound is `watermark − 5min overlap`, so a stale watermark *widens* the window and can never
exclude now-anchored rows).

**Blockers, all fixed above:**
1. **The publish guard had a bypass** — component-id collision + an API on the default `CONFIG_DIR`
   PATCHes the real page. → AC3(c), a mechanical disjointness check.
2. **A silent sixth time constraint** — `FUTURE_TOLERANCE = 5min` quarantines future rows and the
   rejected count is discarded. → AC2(f), plus the timeline direction decided (past-anchored).
3. **The permanent `EVT#…/DEDUPE` marker** lets a repeat run on a reused table ingest zero rows
   while passing a naive row count. → STORY-182 AC2 (fresh table or `observed_at >= run-start`).
4. **AC5(b)(c)(e) claimed to exercise code with zero consumers.** → reworded to real effects (PO
   decision); the scenarios stay as fixtures for STORY-151/152.
5. **AC3(b) was unsatisfiable** — no v1 route exposes the runtime mapping. → in-process
   `create_app()` assertion.
6. **`/components` and `/topology` are seed-derived** and pass with zero ingest. → STORY-182 AC3
   requires an observation-derived probe (`/history`, `/availability`).

**Gaps also folded in:** `DYNAMO_ENDPOINT_URL` is absent from `.env` and unset points boto3 at real
AWS (STORY-182 AC1b); a leftover sample-mode flag forces every observation `DOWN` (AC1c); AC2(e)
over-specified backfill by ~95% — `check_vendor_id_health` needs only `count > 0`, so one row per
signal inside the trailing 2 h suffices, versus 19,200 sequential `TransactWriteItems` for dense
history; STORY-180's five drifted citations and its route/overlap decisions; STORY-181's four extra
sites and the `__pycache__` grep mechanics; and the plan hygiene items (clean tree stated,
`main` vs `debug/…` untangled, gate counts resolved per story, `config/demo/` named, distinct
`app.id` required).

**Two of my own errors it caught:** I cited `decide.py:122-126` as "publishes recoveries" when those
lines *decide* and `:171-172` publishes; and I wrote "`main` (`debug/ingest-stall-sample-mode`, tip
`517fc38`)" as if they were one branch — `main` is `517fc38`, `debug/ingest-stall-sample-mode` is
`1257cc9`. Both corrected in the tables above.

**Its sizing verdict drove the split.** It put the combined STORY-176 at 6 points with STORY-148's
3-point delivery as the yardstick; the PO chose to split into 176 (part 2a, this sprint) and
STORY-182 (part 2b, sprint 64) rather than run a 10-point sprint whose verification would be the
tail of a 6-pointer.
