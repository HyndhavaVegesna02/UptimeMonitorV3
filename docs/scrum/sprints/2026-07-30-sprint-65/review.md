# Sprint 65 — Review

**Date:** 2026-07-30 · **Mode:** `external` (fix round taken in-process on PO instruction)
**Verdict: PO ACCEPTED all five stories. Velocity 13/13.**
**Branch `sprint-65` stays UNMERGED** — the standing "don't merge with main" directive, re-confirmed
at the sprint-64 review, holds. Final commit: `3ee3e68`; evidence commit `b3e1767`.

## Sprint goal — met

> Make the failure half of the system real.

Before this sprint no `DOWN` or `DEGRADED` observation could reach the pipeline through the real
ingest path at all, and nothing here could be described as having a tested failure path. All three
steps landed: a bad row is survivable (STORY-190), a provisional failure mapping exists
(STORY-177), and a real `DOWN`, a real `DEGRADED`, a quarantined poison row **and a real recovery
publish** were driven through the live loop (STORY-191).

## Delivered

| # | Story | Pts | Verdict |
| --- | --- | --- | --- |
| 1 | STORY-188 — normalize `.scrum/` encoding + mechanical guard | 1 | accepted |
| 2 | STORY-190 — quarantine the bad row, keep the batch | 3 | accepted, 1 fix round |
| 3 | STORY-177 — provisional failure-code mapping | 3 | accepted, 1 fix round |
| 4 | STORY-191 — a real `DOWN` and a real recovery publish through the loop | 5 | accepted, 1 large fix round |
| 5 | STORY-185 — un-gate the unsafe side of the publish proof | 1 | accepted |

## Gate evidence

**Full 8/8 DoD gate at `b3e1767`** — `pytest` **685 passed, 0 SKIPPED** with `REQUIRE_DYNAMO=1`
(sprint-64 close baseline was 666, so +19 net new tests); `Contracts: 8 kept, 0 broken`;
`ruff check` / `ruff format --check` / `cfn-lint` / `npm test` / `npm run build` / `npm run lint` all
green. `yt_selftest` **30/30** (was 28/28; +2 from STORY-188's guard). `yt_wiki` CLEAN on sweep,
facts, links and integrity.

The zero skip count is the load-bearing number (agreement A6): it proves the 53 DynamoDB-gated tests
actually ran rather than being silently skipped.

## The STORY-191 reality gate — the sprint's evidence of record

`tools/demo_loop_gate/failure_path_reality_gate.py`, **PASS / exit 0, twice** (re-run after later
changes). A real loop run: embedded demo engine + real `uvicorn` API + the **unmodified**
`python -m src.composition.run`, all as OS subprocesses. Every assertion reads **persisted state**;
nothing parses log text.

```
down-ladder      api-gateway-health       healths=[down, up]      rows=40
partial-breadth  auth-service-login       healths=[down, up]      rows=32
degraded-ladder  payments-service-charge  healths=[degraded, up]  rows=32
poison-row       search-service-query     4 locations, rejected_rows=True

cdn-edge: major_outage -> operational   == THE RECOVERY PUBLISH FIRED
publications rows: 0                    == NOTHING LEFT THE PROCESS
```

That pair is two-sided by design. `StatusWritebackPublisher.publish` is the **only** writer of
component status, so the change proves it executed; `RecordingPublisher` writes a publications row on
**every** attempt and exists **only** in the credentialed+mapping chain, so an empty table proves the
`LoggingPublisher` fallback was selected. Either half alone would be worthless — "publications is
empty" is trivially satisfied by a run in which the publish path never executed, which is the state
every previous sprint was in.

**This is the first time the publish path has fired in this repo's history, and the config-only guard
held under genuine load.** Shown failing first (agreement A7): `--self-test` feeds all six
assertions deliberately bad evidence and requires each to be rejected — all eight bad cases are.

## The PO's zone directive — verified, not assumed

The 2026-07-30 directive ("always respect the code boundaries and discipline I wanted to follow")
was given specifically because an inbound adapter importing
`src.core.ports.rejected_observation_repository` would **pass all eight `lint-imports` contracts**
while being architecturally wrong. `yt-quality-reviewer` checked it import-by-import: the only `core`
import anywhere under `backend/src/adapters/inbound/` is `src.core.domain`. The adapter returns
values and persists nothing; the failure types are adapter-local, not in `core/domain/`; only
`composition` decides what happens to them. Eight contracts kept, unedited.

A useful sharpening came out of it: the gate **does** catch the *concrete*
`adapters.persistence.*` variant. Only the core-port route is invisible — so a red gate means the
concrete route was taken, but **a green gate does not mean the right route was taken.**

## What the verification chain caught — three times, and it earned its keep

1. **The independent gate caught a delivery that self-reported "verified."** `ruff check` was red
   with 22 errors, including `F821 Undefined name 'httpx'`. Rule 2 of the delivery contract exactly.
2. **That deletion had broken the reality-gate harness entirely — and silently.** `NameError` is an
   `Exception`, so `_wait_for_last_signal`'s `except Exception: pass` swallowed it and returned
   `False` after burning the timeout. **AC3 was never met**: the delivery's tests had zero references
   to `run_positive_side`/subprocess/uvicorn, and the `extra_scenarios` seam it added was **dead code
   called by nothing** — which is precisely why the broken import went unnoticed.
3. **Both reviewers caught defects the orchestrator had personally accepted.**
   - `yt-spec-reviewer`: AC3's pre-fix stall test was **tautological** — it constructed a
     `watermark_repo`, never passed it to anything, called `normalize_rows` directly, then asserted
     the watermark was still `None`, which holds whether or not anything raises.
   - `yt-quality-reviewer`: the backward-compat test **asserted nothing**, and it proved so by
     **mutation** — making the legacy cycle branch emit `DOWN`, silently turning every pre-existing
     scenario DOWN, left the test green.
   - Also a genuine behavioural hole: the lenient path caught only three *named* classes, so a
     **present-but-invalid** value still stalled a signal. Verified live — an unparsable `timestamp`
     (`ValueError`) and a null location (pydantic `ValidationError`) both escaped to `run_periodic`.
     Now catches `ValueError` (all four are subclasses) but deliberately **not** `Exception`, so a
     `TypeError` still surfaces instead of being recorded as a bad vendor row.

Both rewritten tests were **discrimination-probed**: the reviewer's own mutation now fails the
backward-compat test, and removing the monkeypatch makes the stall test fail.

## Orchestrator errors, recorded rather than tidied away

- **Two full runs lost to a bug of my own making.** The AC6 precondition wrote to
  `pk=COMPONENT#<id>/sk=META` while `DynamoComponentRepository` uses
  `pk=TOPOLOGY/sk=COMPONENT#<id>`. The write hit a phantom key and the read-back "verified" it
  against *the same wrong key*, so the check passed **vacuously**; `decide` correctly declined to
  publish because there was genuinely nothing to recover from, and the gate reported the guard as
  broken. Both paths now go through the real repository, which makes that drift impossible.
- **The "13 damaged sites" planning figure was a double-count** — measuring with
  `errors="replace"` converts each invalid byte *into* a `U+FFFD`, so the two columns tallied the
  same damage twice. The repair script's own `!= 13` assertion caught it. The plan verifier had
  "independently reproduced" the bad table by repeating the same method: **reproducing a measurement
  is not validating it.**
- **I accepted the tautological AC3 test** in my own review before the spec reviewer found it.
- A wrong first theory (orchestrate-window timing) drove a component change before the real cause
  was found. The change was harmless and its arithmetic is now documented as a real constraint, but
  it was not the bug.

## Filed, not bodged

- **STORY-192** — `docs/scrum/wiki/` carries the same em-dash corruption STORY-188 fixed in
  `.scrum/`: 246 mojibake sequences across 6 files. Different shape (valid UTF-8 carrying a
  cp1252-through-UTF-8 round trip), so **STORY-188's guard does not catch it** and needs a third check.
- **STORY-193** — proposal *formation* is not reliably assertable in a loop run. Two consecutive runs
  with identical scenarios disagreed. Observations are watermark-driven and deterministic; a proposal
  additionally needs `anti_flap` to still see a streak, and orchestrate's look-back is only
  `6 * interval` = 180s for every 30s failure signal in `config/demo`, which the 41-signal
  vendor-health sweep can outrun. AC5 therefore validates whatever proposals are present, strictly,
  and records the count **without asserting presence** — a flaky assertion in a proof harness is
  worse than none. Corroboration that this is the mechanism: the recovery assertion needs the same
  kind of streak and was made reliable purely by moving it to a 60s-interval signal.

## The claim, stated precisely

"The failure path is tested" is now true in a **specific, limited sense**: tested against an
**ASSUMED** vendor code, through the real unmodified ingest path, in a real loop run. Never against
anything Dynatrace has confirmed — no real failure code has ever been observed, and STORY-154 still
replaces the contents of that single constant when a tenant exists.

`CLAUDE.md` was **outright false** on this until the quality review caught it (it still said
`map_synthetic_status` raises on everything else, that dispatch discards the whole batch, and that
`DOWN`/`DEGRADED` cannot reach the pipeline). It now carries the three-step resolution, the
provisional/unverified framing and a superseded note — it is the file every session reads first.

## Cut at verification (PO-approved)

**STORY-186** and **STORY-189** returned to the backlog as sprint-66 candidates. Not only sizing:
186 rewrites the very `test_scenario.py` rejection tests and loader validation that 191 extends, and
189 fights 191 over `demo-engine.md` frontmatter. Cutting them removed two fix-round risks, and the
sprint held the 13 points already approved (STORY-191 was re-pointed 3 → 5 on the verifier's
independent judgement).

## Carried into the retro

- The PO's requested **boundary/code-discipline AUDIT sprint** — raise at sprint-66 planning.
- STORY-186, STORY-189, STORY-192, STORY-193 are all sprint-66 candidates.
- STORY-178 (`yt_gate.py` exits 0 when `--only` matches nothing) remains unscheduled and was a
  standing caveat on every scoped run this sprint.
- Leftover `story182-*` throwaway DynamoDB table pairs continue to accumulate in the long-lived local
  container (in-memory, uniquely suffixed, vanish on restart) — still judged not worth a story.
