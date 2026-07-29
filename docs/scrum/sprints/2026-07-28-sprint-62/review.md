# Sprint 62 Review — the config shape, a Grail-faithful demo wire contract, and one closed anti-flap hole

**Goal (as locked):** land the config authoring shape that communicates the
component → monitor → location hierarchy; build a Grail-faithful demo-engine wire
contract proven field-and-scale against a real captured sample and through the real
executor; and close the one anti-flap damping hole that goes live the moment a second
location exists. Backend only, no frontend work.

**Outcome: all three stories Done. 9 of 9 points.** Full 8-command gate GREEN on final
HEAD `2b0bf86` — pytest **572**, import-linter **8 contracts kept**, ruff check, ruff
format (218 files), cfn-lint, `npm test` **363**, `npm run build`, `npm run lint`.
Nothing merged to main; the branch `sprint-62` is unmerged and awaiting your verdict.

**Baseline for comparison:** the sprint opened at 529 backend tests. It closes at 572
(+43) with the frontend suite unchanged at 363, which is expected — this sprint touched
no frontend file.

---

## STORY-146 — config authoring shape: nested monitors, declared locations, freshness (5 pts) — DONE

Re-estimated 3 → 5 at the second verifier pass (13 test files to migrate). The shape is
the one you approved at planning ("this shape looks good", `config-shape-proposal.yaml`).

| AC | Evidence |
|----|----------|
| AC1 nesting | `ComponentConfig` takes a nested `monitors:` list; `AppConfig.signals` survives as a *derived* attribute |
| AC2 deleted validator loses nothing | The referential validator is gone; the new loader **rejects** the old flat shape by design — proven because the reality gate needed two code versions to replay it |
| AC3 declared locations | Top-level `locations:` alias map; an undeclared alias raises `UndeclaredLocationAliasError` |
| AC4 freshness | Top-level `freshness:` block with `stale_after_cycles` |
| AC5 named error classes | `ConfigError(ValueError)` hierarchy, raised *outside* `load_config`'s try/except so it is not re-wrapped |
| AC6 per-app scoping | `locations:`/`freshness:` scoped per app, stated in the model |
| AC7 seven surviving consumers | All seven verified **semantically byte-identical**, not just compiling (`d004da7`) |
| AC8 real config migrated | `config/apps/httpcheck.yaml` rewritten to the nested shape; downstream values identical |
| AC9 gate | 8/8 at `f8ef730`, re-run 8/8 at post-rework head `81bf71a` |

**Reality gate — PASS, and it caught its own false pass twice.** A byte-level
before/after of the seeded topology: a worktree at the pre-implementation commit seeded
`uptime-control-before` with the old flat config, the migrated code seeded
`…-after`, both control tables were dumped, canonicalised and diffed. 3 topology items
each side, **byte-identical, md5 `461c9e42e872eacffb1bad6eaaa94adc` on both sides**.

Worth your attention because it is the archetypal reality-gate lie: the *first* run
reported IDENTICAL on two **empty** dumps (`md5 d41d8cd9…` — the empty-file hash). Cause:
the DynamoDB-Local container runs without `-sharedDb`, so it partitions databases by
access key, and the dump script used a different key than the code under test. A second
false pass followed from filtering on uppercase `PK/SK` where the schema uses lowercase.
The dump script now **refuses to emit an empty dump** (exit 2) and the harness refuses to
diff when either side fails.

**Reviews:** spec PASS. Quality FIX_REQUIRED → **5 majors, all fixed and each
independently re-verified by me** rather than taken on the implementer's word: dead
dict branches deleted (F1); the `interval_seconds > 0` invariant pinned by tests — the
wiki had already asserted it as verified Fact with **nothing** holding it (F2); a
happy-path `expected_locations` test proven load-bearing by deliberately sabotaging the
production code and watching it fail (F3); `DuplicateAppIdError` added after my own probe
showed two files with the same `app.id` previously loaded silently, discarding one (F4);
plus a deduped validator via a shared `PositiveIntervalSeconds` type.

---

## STORY-148 — Grail demo engine, part 1: the wire contract (3 pts) — DONE

Split out of a 7–8 point story at the verifier pass. New package `tools/demo_engine/`,
outside `backend/src/` on purpose. **Zero files under `backend/src/` changed** (AC9).

| AC | Evidence |
|----|----------|
| AC1 all seven required fields | Asserted field-by-field against the **real captured sample** `grail_synthetic_events.json`, read off disk (fixture predates this story — committed `fc65483`) |
| AC2 optional fields at real scale | `duration_ms` taken in natural units and converted in the builder (`str(ms * 1_000_000)`) — no string `duration` parameter exists to get wrong |
| AC3 ingest grammar | Three filter clauses parsed: monitor id, `event.type`, watermark bound |
| AC4 watermark parsed at 3 precisions | Delegates to the **real** `_assembly.parse_ns_timestamp`, so bound and rows compare as `datetime`s, never strings |
| AC5 vendor-health grammar | `summarize count()` probe + its 2h window, computed against the request instant read fresh per call |
| AC6 HTTP protocol | The **async** branch: POST → 202 + `requestToken`, GET poll → `SUCCEEDED` + records |
| AC7 through the real executor | Driven by the real unmodified `make_grail_executor` with its own default `httpx` |
| AC8 assumptions labelled | One named module for the assumed failure code, marked UNVERIFIED |
| AC9 production untouched | Mechanically verified |
| AC10 gate | 8/8 at `29430ff` (570 tests) |

**Reality gate — PASS, 19/19,** deliberately one level *above* the story's own tests: it
drove the two **composition-level** callers the real loop uses (`adapter.py::
fetch_observations` and `vendor_health.py::check_vendor_id_health`) over real HTTP
against a running server. Every assertion is two-sided where a one-sided version could
pass on a broken engine — necessary, because `check_vendor_id_health` swallows every
exception and only logs, so a probe that merely *called* it would report success against
a completely broken engine.

Three results worth naming:
- **Nanosecond scale survives end-to-end** — latencies came back `[755, 755, 755, 1234] ms`
  through the real assembler. The units trap is closed in reality, not only in a unit test.
- **The watermark bound genuinely discriminates** — 4 observations at `watermark == t1`
  vs 1 at `t1+1s`, with the timestamp on a **whole second**: the exact shape where
  `isoformat()` drops the fraction and a string comparison reproduces the STORY-051 stall.
- **AC8 held under execution** — the assumed `"1"/"UNHEALTHY"` row reached the real
  `map_synthetic_status`, raised, and **took the whole batch with it** (`dispatch.py:80`).

**One correction I made to my own gate, recorded rather than quietly fixed:** one of the
19 checks initially passed for a bogus reason. It asserted an empty API token is
rejected — but `api_token=""` produces the header value `"Api-Token "`, and httpx/h11
*refuses to transmit a header value with a trailing space*. The request never reached the
server; the assertion was a tautology dressed as an auth test. Replaced with what a probe
then established: the engine checks the **scheme prefix only** — wrong scheme and absent
header both 401, an arbitrary junk token returns 202. That satisfies AC6 (which pins the
header's *presence*) and is a sound demo simplification, but it is **not** token
validation and is not reported as such.

**Reviews:** spec PASS 10/10. Quality FIX_REQUIRED → 2 majors fixed: the README documented
a recipe using the very `conftest.py` this story had **deleted** (a bare `__init__.py`-less
conftest collides on `sys.modules['conftest']` and silently broke an unrelated test — so
following the docs re-created the bug); and the advertised fail-loud contract shipped with
**zero** test coverage, which matters more than an ordinary gap because the executor
returns `[]` on an unexpected envelope, making a regression from loud to silent
indistinguishable from "no data". 8 non-blocking minors routed to STORY-180 rather than
absorbed — that is how a 3-pointer becomes a 6.

### ⚠ The one thing not to over-read in this story
Per your decision D-A, this engine emits **`HEALTHY` rows and absence, nothing else**.
Nothing in this sprint may be read as "the failure path is tested" — the failure path is
proven **rejected**, which is the opposite claim. Provisional failure mapping is STORY-177.

---

## STORY-149 — anti-flap: require a streak for DEGRADED, symmetric with the DOWN ladder (1 pt) — DONE

A defect story. `anti_flap` proposed `degraded` for a `DEGRADED` streak of **any** length
with no damping at all, while the `DOWN` branch immediately above it required
`length >= thresholds.degraded`. Since `_collapse_health` returns `DEGRADED` for *any*
disagreement between a cycle's locations, one location hiccuping **once** proposed a
public status change with zero anti-flap protection — the moment a second location exists.

| AC | Evidence |
|----|----------|
| AC1–AC3, AC5 the new ladder | 4 tests: `>= degraded` proposes; `== 1` warns internally; between → nothing; length 0 → nothing |
| AC4 regression is load-bearing | Reverting the fix makes the length-1 test fail (run, not assumed) |
| AC6 the two tests that encoded the defect | Both **rewritten**, not deleted, each renamed to state the new rule |
| AC7 the docstring that *was* the defect | Updated in the same commit as the fix |
| AC8 no collateral change | Verified at the diff level: `collapse`, `streak`, the whole `DOWN` ladder and the `UP` check are **byte-identical** |
| AC9 gate | Scoped 5/5 at `1e025a8` (572 tests); full 8/8 at final HEAD |

**Reality gate — PASS 12/12, and it is proven able to fail.** Per your decision D-A this
is *not* a demo-engine run (a demo gate would have false-passed: with no ingestible
failure row, "no proposal appeared" would have held because nothing was ingested). It is
an `orchestrate_signal`-level test over **seeded** multi-location observations, entering
the pipeline below the vendor mapping, against real DynamoDB-Local tables and the real
`/api/v1/approvals` endpoint over live HTTP:

- one disagreeing cycle (the blip) → `NOOP`, **no** proposal row, endpoint returns an empty list;
- sustained disagreement → `PROPOSED`, exactly one open proposal, endpoint serves it, nothing published;
- the two phases are asserted to **discriminate**, so neither can pass by the pipeline being inert.

I then ran the **same gate unchanged at the pre-fix commit** in a worktree: **7/12**,
failing on exactly the five checks this fix owns and nothing else. Pre-fix, one blip wrote
a proposal and `/api/v1/approvals` served it over live HTTP. That is the defect visible
end-to-end rather than argued from a unit test — and it is the check a four-line fix most
needs and most often skips.

**Honest limit:** both phases are seeded, because no vendor mapping produces `DOWN` or
`DEGRADED` on the live path today. This proves the core chain damps a location
disagreement; it does not prove a real vendor failure reaches that chain (STORY-177).

**Process note:** the implementer for this story **died mid-story** on an API session
limit, after step 7. Crash recovery worked as designed — steps 1–7 were already committed,
so the only thing lost was the wiki pass, which I completed. No code was re-derived and
nothing was discarded.

---

## Knowledge (wiki) — compile pass complete

`yt_wiki.py` sweep / facts / links / integrity all **CLEAN**.

- **New article `demo-engine.md`** — written at the compile pass, not inside the story, because
  the reality gate changed what was worth saying (auth is a scheme-prefix check, not
  validation; the assumed failure code is rejected end-to-end and takes its batch with it).
- **`core-pipeline-and-availability.md`** — the anti-flap Facts said `DEGRADED` is "always
  degraded, regardless of length … so no length comparison applies". That sentence *was
  the defect*, faithfully mirroring the code's own docstring — which is exactly how the
  hole survived every verification pass since sprint-8: **article and code agreed, so the
  staleness machinery had nothing to catch.** Rewritten, with that failure mode recorded.
- Re-verified without bulk-stamping: `canonical-types-and-ports.md` (its only `pipeline.py`
  claim is about `collapse`, byte-identical in the diff), plus `dev-setup-and-dod.md`,
  `persistence-adapters.md`, `sample-mode.md`, `config-layer.md`.
- **CLAUDE.md corrected**: it documented no `tools/` package, and claimed import-linter
  enforces "the five contracts" when the runner prints `Contracts: 8 kept`. Contracts 5–7
  had landed without the file being updated.

## Carried out of this sprint (nothing silently dropped)

- **STORY-176** (demo fleet + loop run) — deferred to sprint 63 by your decision D-B; the
  carry note is `story-176-carried-to-sprint-63.md`.
- **STORY-177** — provisional failure mapping, created by decision D-A. The gap this
  sprint made concrete: no vendor failure can reach the pipeline at all today.
- **STORY-180** — STORY-148's 8 non-blocking review minors.
- **STORY-178** (three `yt_gate.py` defects) and **STORY-179** (two `dynamo_local`
  defects) — tooling defects found while running this sprint's own gates.
- **D1/D2** (the breadth-ceiling anti-flap model, Phase 2) stay out of scope, recorded in
  `decisions-and-future-work.md`.

## Decisions needed from you

1. **Verdict per story:** STORY-146, STORY-148, STORY-149 — accept (merge to main) or reject?
2. **Merge shape on acceptance:** merge the `sprint-62` branch, or cherry-pick per story?
   (Standing instruction from 2026-07-28 was "don't merge with main" — I have merged
   nothing, and will not until you say so here.)
3. **Sprint 63 opening scope:** STORY-176 is queued first by D-B. The frontend work
   (design system + shell, with a look-and-feel checkpoint **before** six pages get built
   on the language) is the other candidate. Which opens 63?

---

## PO verdicts (2026-07-29)

1. **All three stories ACCEPTED** — STORY-146, STORY-148, STORY-149. Velocity recorded:
   sprint 62, committed 9, accepted 9.
2. **Kept UNMERGED.** The standing "don't merge with main" instruction stands; `main`
   (`debug/ingest-stall-sample-mode`, tip `517fc38`) is untouched and the accepted work
   stays on the `sprint-62` branch. Recorded in the backlog against each story so a future
   session cannot mistake "accepted" for "on main".
3. **Sprint 63 opens with STORY-176** — demo engine part 2: the scenario player, the demo
   fleet config, and the real loop run (4 pts, `story-176-carried-to-sprint-63.md`). The
   frontend design-system + shell work, with the look-and-feel checkpoint before any pages
   are built, is not opening 63 and stays queued.

**Consequence to carry into sprint-63 planning:** because nothing merges, sprint 63
branches from `sprint-62` rather than from main, and the safety precondition in this
sprint's board still applies to STORY-176 — `decide` publishes recoveries with **no human
gate**, so the demo loop run needs its config-only publish guard *plus* `CONFIG_DIR` on the
API process, which is a separate process reading its own config.
