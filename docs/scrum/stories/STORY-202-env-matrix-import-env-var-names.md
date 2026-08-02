---
id: STORY-202
title: env_matrix.py must import ALL SEVEN child env-var NAMES from settings.py, not re-declare them
type: defect
points: 3
status: ready
filed: 2026-07-31
refined: 2026-08-02
rescoped: 2026-08-02
---

## Context

Filed during sprint 66, the boundary/code-discipline audit (`ZR-3`). **Authoritative detail:**
`docs/scrum/sprints/2026-07-31-sprint-66/audit-api-composition-tools.md` §6, plus the STORY-196
quality review that widened it from 2 names to 7 and re-ordered the severity.

## The defect

`tools/demo_loop_gate/env_matrix.py` hardcodes the literal env-var **key names** it injects into the
demo harness's two child processes, duplicating names the `backend/src/` side owns:

| `env_matrix.py` | name | owned by |
| --- | --- | --- |
| `:64` | `CONFIG_DIR` | `settings.py:32` (function-body literal) |
| `:65` | `AWS_REGION` | `settings.py:33` (function-body literal) |
| `:66` | `DYNAMO_ENDPOINT_URL` | `settings.py:37` (function-body literal) |
| `:67` | `DYNAMO_OBSERVATIONS_TABLE` | `settings.py:34-35` (function-body literal) |
| `:68` | `DYNAMO_CONTROL_TABLE` | `settings.py:36` (function-body literal) |
| `:75` | `STATUSPAGE_PAGE_ID` | `settings.py:49` `STATUSPAGE_PAGE_ID_VAR` (module constant) |
| `:77` | `STATUSPAGE_API_KEY` | `settings.py:50` `STATUSPAGE_API_KEY_VAR` (module constant) |

**Consequence of a rename on the `settings.py` side:** the harness's injection silently stops
matching, and `composition/asgi.py`'s own `load_dotenv()` fills the gap from the repo-root `.env`
instead. Nothing raises; the harness still reports green.

**`CONFIG_DIR` is the most severe of the seven, above the credential pair.** The fake Statuspage
credentials are defence in depth. `CONFIG_DIR` is what selects `config/demo`, which is what makes
`Config.statuspage_mapping()` empty, which is what makes `build_publisher` fall through to a
`LoggingPublisher` — **it IS the publish guard.** `decide` publishes recoveries with no human gate
and sprint 65 proved that path fires.

## The part that makes this 3 points, not 1 — THREE files, not two

**Five of the seven names have nothing to import yet.** `settings.py:32-38` reads them as
function-body literals inside `load_settings()`, not as module constants — which is also the only
reason they escaped the ZR-3 sweep, a formatting accident on the `src` side rather than a difference
in risk. So the story is three edits, in order:

1. **`backend/src/composition/settings.py`** — promote the five to module constants alongside the
   existing `STATUSPAGE_PAGE_ID_VAR` / `STATUSPAGE_API_KEY_VAR` at `:49-50`, and have
   `load_settings()` read through them. Follow the existing naming convention (`<NAME>_VAR`).
2. **`tools/demo_loop_gate/env_matrix.py`** — import the seven and use them as the dict keys.
3. **`tools/demo_loop_gate/harness.py`** — the same, at six sites. **See the section below; this
   edit is not optional, it is what keeps the gate green.**

Edit 1 is in `backend/src/`, so this story touches production code, not just `tools/`. The default
values (`"config/apps"`, `"us-east-1"`, `"uptime-observations"`, `"uptime-control"`) are a separate
concern and are **out of scope** — STORY-203 owns the duplicated *values*. This story is about the
duplicated *key names* only.

## The promotion CREATES six new ZR-3 collisions, and they must be fixed in this story

**Found by plan verification before implementation; PO-approved scope expansion 2026-08-02
(2 -> 3 points).**

`tools/zr3_duplicate_sweep.py:110-127` (shape (i)) treats **any** module-level `UPPER_CASE` constant
with a literal value under `backend/src/` as a *declared value*. So the moment AC1 promotes the five
names, the strings `"CONFIG_DIR"`, `"AWS_REGION"`, `"DYNAMO_ENDPOINT_URL"`,
`"DYNAMO_OBSERVATIONS_TABLE"` and `"DYNAMO_CONTROL_TABLE"` become declared — and every matching
literal under `tools/` becomes a collision. Simulated at planning: **15 collisions today -> 26 after
promotion**, six of them new in `harness.py`:

```
harness.py:540   f"env CONFIG_DIR={api_env['CONFIG_DIR']!r}"
harness.py:609   f"CONFIG_DIR={loop_env['CONFIG_DIR']!r}"
harness.py:736   result["config_dir_api"]    = api_env["CONFIG_DIR"]
harness.py:742   result["dynamo_endpoint_url"] = api_env["DYNAMO_ENDPOINT_URL"]
harness.py:743   result["observations_table"]  = api_env["DYNAMO_OBSERVATIONS_TABLE"]
harness.py:744   result["control_table"]       = api_env["DYNAMO_CONTROL_TABLE"]
```

**These are true positives, not sweep noise.** `api_env["CONFIG_DIR"]` re-types a key name that
`settings.py` owns, and it breaks on a rename in exactly the way `env_matrix.py:64` does — the same
mechanism, the same silent failure. Fixing them is the consistent completion of the story rather
than an unrelated chore.

**Watch the collision with STORY-203:** `harness.py:747` and `:750` are *already* adjudicated to
STORY-203 (duplicated table-name **values**, not key names). Do not touch those two. Two stories now
meet in this file, so keep the distinction sharp — **this story edits key-name strings only.**

## Acceptance Criteria

- [ ] **AC1** — `settings.py` declares all seven env-var names as module-level constants, and
      **`load_settings()`** reads `os.environ` through those constants rather than through inline
      string literals. No behaviour change: every resolved value and default is identical.

      **`load_live_secrets()` is NOT in scope** — despite an earlier revision naming it. Verified: it
      reads only `DYNATRACE_ENV_URL`/`DYNATRACE_API_TOKEN` (`settings.py:100`, `:103`), neither of
      which is among the seven, and its Statuspage reads already delegate to
      `load_statuspage_secrets()`, which already uses the constants (`:88-89`). Including it would be
      silent scope expansion.
- [ ] **AC2** — `env_matrix.py` imports the seven names from `src.composition.settings` and uses them
      as its dict keys. **No literal of any of the SEVEN remains in `env_matrix.py`.**

      **Scoped to the seven deliberately — do NOT write "no env-var key literal remains".** Two more
      live at `env_matrix.py:71` and `:73` (`DYNATRACE_ENV_URL`, `DYNATRACE_API_TOKEN`), and they are
      genuinely the same drift risk — but their `settings.py` side is also a function-body literal,
      so pulling them in means promoting two more constants and widening the collision surface AC8
      has to account for. **Filed as a follow-up rather than absorbed**, so this story stays bounded
      and the two are not silently forgotten.
- [ ] **AC3** — The harness's test expectations are pinned to the **imported symbols**, not to
      re-typed string literals, so a future rename moves the expectation with it instead of passing a
      now-wrong key. (This was flagged at filing as "the good one" and it is: a test that hardcodes
      `"CONFIG_DIR"` re-creates the defect one layer out.)
- [ ] **AC4** — **Mutation proof, two-sided.** Rename one constant's *value* in `settings.py` (e.g.
      `CONFIG_DIR` -> `CONFIG_DIR_X`) and confirm (i) the harness follows automatically — the child
      process still receives whatever name `settings.py` now declares — and (ii) no test asserts the
      old, now-wrong key. Restore and confirm `git diff` is empty. Doing this at the pre-fix commit
      must show the harness and `settings.py` DISAGREEING; that divergence is the proof.
- [ ] **AC5** — `_ADJUDICATED` entries `("tools/demo_loop_gate/env_matrix.py", 75)` and `(..., 77)`
      are **removed** from `backend/tests/test_zr3_duplicate_declarations.py:64-73` (both cite "Fix:
      STORY-202"), and both ZR-3 tests pass.

      **The `:39` entry must be RE-KEYED, not left alone — and this is an explicit carve-out from
      constraint C1.** An earlier revision said "do not touch it", which is exactly backwards and
      would take the gate RED. `env_matrix.py:39` is `aws_region: str = "us-east-1"`, a duplicated
      *value* belonging to STORY-203 — but AC2 adds a `from src.composition.settings import (...)`
      line above it (the module's only current imports are `from __future__` and `import uuid` at
      `:13-15`), which **shifts it to `:40`+**. Its adjudication key then matches no collision and
      `test_zr3_adjudications_are_still_current` goes RED.

      **C1 governs entries being RETIRED, not entries being DISPLACED.** This one is displaced: the
      collision still exists and still belongs to STORY-203, so its key moves and its reason text
      stays. Re-key it.
- [ ] **AC6** — The publish guard is re-verified, not assumed: with `CONFIG_DIR=config/demo`,
      `Config.statuspage_mapping()` is still `{}` and `build_publisher` still yields a
      `LoggingPublisher`. This story edits the mechanism that selects the demo config, so it may not
      land on the assertion that it "should be equivalent".
- [ ] **AC8** — **`tools/demo_loop_gate/harness.py` imports the same constants** and uses them at all
      six sites (`:540`, `:609`, `:736`, `:742`, `:743`, `:744` at `1e60172` — **re-derive these, the
      earlier edits in this story shift them**). `harness.py:747` and `:750` are **not touched**; they
      are duplicated *values* belonging to STORY-203.
- [ ] **AC9** — **The ZR-3 collision count is re-derived and reported after the last edit**, not
      assumed. Run `python tools/zr3_duplicate_sweep.py` and record the number. Baseline is **15**
      before this story; the promotion alone would take it to **26**; with AC2 and AC8 applied it
      should return to **15 minus the two `env_matrix.py` entries AC5 retires**. A number that does
      not land where expected is reported and explained, never quietly substituted — if collisions
      remain, they are named individually rather than absorbed into a new adjudication.
- [ ] **AC7** — Full DoD gate green, including both ZR-3 tests and both ZR-7 tests.

## Open Questions

None. Citations re-derived against HEAD (`86459ea`) 2026-08-02 and all seven resolve exactly as
tabulated above; `settings.py:49-50` and the `env_matrix.py:64-68` / `:75` / `:77` line numbers are
unchanged since filing.

## History

- 2026-07-31: filed from STORY-196's audit (`ZR-3`, MAJOR x2), widened from 2 names to 7 at the
  STORY-196 quality-review fix round, with `CONFIG_DIR` re-graded most severe.
- 2026-08-02: refined to `ready` at sprint-67 planning; **re-pointed 1 -> 2.** The filing assumed
  seven names could simply be imported; five of them are function-body literals with no symbol to
  import, so the story necessarily edits `backend/src/composition/settings.py` first. AC written
  (the file previously carried a placeholder "to be lifted from the source"), and the ZR-3
  adjudication cleanup (AC5) added — the guard did not exist when this was filed.
- 2026-08-02 (later, post-lock): **plan verification found four more gaps; re-pointed 2 -> 3 with PO
  approval.** In order of consequence:
  1. **The promotion creates six new ZR-3 collisions in `harness.py` and fails the gate** — a third
     file the story did not know it touched. PO chose to expand the story rather than adjudicate
     them, because they are the same defect by the rule's own logic. New AC8 + AC9.
  2. **AC5 said "do not touch the `:39` entry", which was exactly backwards** — AC2's import line
     displaces it and stales its adjudication key. It must be **re-keyed**, and that needed an
     explicit carve-out from constraint C1 (which governs *retired* entries, not *displaced* ones).
  3. **AC1 named `load_live_secrets()`, which touches none of the seven** — verified: it reads only
     `DYNATRACE_*`, and its Statuspage reads already delegate to constants. Removed as silent scope.
  4. **AC2 said "no env-var key literal remains", but `env_matrix.py:71`/`:73` hold two more**
     (`DYNATRACE_ENV_URL`/`DYNATRACE_API_TOKEN`). Scoped explicitly to the seven, with those two
     filed as a follow-up rather than absorbed.
