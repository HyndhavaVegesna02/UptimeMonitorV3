---
id: STORY-202
title: env_matrix.py must import ALL SEVEN child env-var NAMES from settings.py, not re-declare them
type: defect
points: 2
status: ready
filed: 2026-07-31
refined: 2026-08-02
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

## The part that makes this 2 points, not 1

**Five of the seven names have nothing to import yet.** `settings.py:32-38` reads them as
function-body literals inside `load_settings()`, not as module constants — which is also the only
reason they escaped the ZR-3 sweep, a formatting accident on the `src` side rather than a difference
in risk. So the story is two edits, in order:

1. **`backend/src/composition/settings.py`** — promote the five to module constants alongside the
   existing `STATUSPAGE_PAGE_ID_VAR` / `STATUSPAGE_API_KEY_VAR` at `:49-50`, and have
   `load_settings()` read through them. Follow the existing naming convention (`<NAME>_VAR`).
2. **`tools/demo_loop_gate/env_matrix.py`** — import all seven and use them as the dict keys.

Edit 1 is in `backend/src/`, so this story touches production code, not just `tools/`. The default
values (`"config/apps"`, `"us-east-1"`, `"uptime-observations"`, `"uptime-control"`) are a separate
concern and are **out of scope** — STORY-203 owns the duplicated *values*. This story is about the
duplicated *key names* only. Keep the two apart or the two stories will collide.

## Acceptance Criteria

- [ ] **AC1** — `settings.py` declares all seven env-var names as module-level constants, and
      `load_settings()` + `load_live_secrets()` read `os.environ` through those constants rather than
      through inline string literals. No behaviour change: every resolved value and default is
      identical.
- [ ] **AC2** — `env_matrix.py` imports all seven names from `src.composition.settings` and uses them
      as its dict keys. No env-var key-name string literal remains in `env_matrix.py`.
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
      STORY-202"), and both ZR-3 tests pass. Do **not** touch the `:39` entry — that one cites
      STORY-203 and is a duplicated *value*, not a key name. The guard's stale-adjudication test goes
      RED if entries are left behind, so this AC is self-verifying.
- [ ] **AC6** — The publish guard is re-verified, not assumed: with `CONFIG_DIR=config/demo`,
      `Config.statuspage_mapping()` is still `{}` and `build_publisher` still yields a
      `LoggingPublisher`. This story edits the mechanism that selects the demo config, so it may not
      land on the assertion that it "should be equivalent".
- [ ] **AC7** — Full DoD gate green.

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
