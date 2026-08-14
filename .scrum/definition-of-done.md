# Definition of Done — Uptime Monitor V3
#
# OPERATIONAL gate (the gate runner reads THIS file). Mirrors the root-level
# `definition-of-done.md` companion referenced by the inception seed; if the two
# ever diverge, this `.scrum/` copy is authoritative for the gate.
#
# Every item below must hold before any story is marked Done. The gate runner
# executes each command literally and records command, exit code, output tail,
# and commit SHA into sprint-current.yaml. Nonzero exit = not Done, no exceptions.
#
# This DoD is NOT generic — its core commands are the architecture's own CI
# contracts. The canonical boundary the whole design rests on (core never imports
# an adapter or vendor type; the schema spine never FKs into a feature table) is
# CHECKED ON EVERY STORY, from Sprint 0 onward. That is what makes horizontal,
# zone-by-zone slicing safe: the boundary is enforced before the logic inside it
# is even written.
#
# BOOTSTRAP NOTE (Sprint 0 only): the commands assume the scaffold wires them.
# A command counts toward a story's gate once the story that creates it has run:
#   - `pytest` works from STORY-001 (harness exists, zero tests = exit 0 OK).
#   - `lint-imports` + `check_fk_direction.py` become real in STORY-002.
#   - `alembic upgrade head` becomes real in STORY-003.
# Within Sprint 0, a story is Done when every command that exists at that point
# passes; later stories inherit the full gate.

# EFFECTIVE AMENDMENT (PO approval 2026-07-14; landed STORY-087 sprint-49):
# The persistence floor is now the DynamoDB-Local-backed pytest suite (STORY-082).
# `alembic upgrade head` and `python scripts/check_fk_direction.py` are retired.

## Commands (backend)
- [ ] Tests pass: `python -m pytest` -> exit 0 (requires-env: REQUIRE_DYNAMO)
      (2026-07-31, PO-approved: invocation changed from the bare `pytest` exe shim, which the
       same Windows Device Guard / Application Control policy began blocking MID-SPRINT-66 --
       green at 11:16 UTC, blocked at 16:33 UTC the same day, with no code change in between.
       Identical to the 2026-07-12 change made for `lint-imports` below: SAME check, SAME
       tests, module path instead of the blocked shim. Verified: 689 passed, 0 skipped.
       Filed as STORY-210.)
      (2026-07-30, sprint-64 retro amendment A6: a green `pytest` does NOT by itself
       mean the persistence floor ran. With Docker down and DYNAMO_ENDPOINT_URL unset,
       `backend/tests/conftest.py`'s `dynamo_local` fixture skips every DynamoDB-gated
       test and pytest STILL EXITS 0, so this gate records PASS. Measured at 805287f,
       same commit, same command: `561 passed, 53 skipped` vs `614 passed, 0 skipped`.
       `REQUIRE_DYNAMO=1` makes that fixture FAIL instead of skip -- that fixture is
       the ENFORCING rung. This `(requires-env: ...)` annotation only makes the runner
       SURFACE the var when unset; it is advisory in yt_gate.py and never blocks.
       Record the pass/skip COUNTS on every backend gate record; a nonzero skip count
       is an incomplete gate, not a pass.)
- [ ] Import boundary holds: `python -c "from importlinter.cli import lint_imports_command; lint_imports_command()"` -> exit 0
      (2026-07-12: invocation changed from the `lint-imports` exe shim, which a Windows
       Application Control policy now blocks; same check, same 8 contracts, module path)
      (import-linter; NINE contracts, from dossier §4, §13, Sprint 14 and later:
       core-independence, core-internal-layering [domain<-ports<-services],
       adapters-independence, api-feature-independence, api-outward-independence,
       adapters-edge-only, api-shared-no-feature-imports, src-no-tests,
       inbound-adapters-dont-persist.
       2026-07-29: this list said "five" and named five while the line above it
       already said "same 8 contracts" — the runner's own `Contracts: 8 kept, 0
       broken.` is the count of record, and `pyproject.toml` declares all eight.)
      (2026-08-05, STORY-206: the count of record moved 8 -> 9 -- `pyproject.toml`
       gained a ninth contract, `inbound-adapters-dont-persist` (ZR-1's guard,
       `docs/scrum/wiki/zone-rules.md`), forbidding `src.adapters.inbound` from
       importing the nine repository/watermark ports. The runner's own `Contracts:
       9 kept, 0 broken.` line is now the count of record. This is a CONTRACT count;
       the DoD stays at EIGHT commands -- the new contract runs inside this existing
       command, no ninth command was added.)
- [ ] Code linting check: `python -m ruff check .` -> exit 0
      (2026-08-02, PO-approved, preventive (STORY-210): invocation changed from the bare `ruff`
       exe shim to its module form. `ruff.exe` is NOT blocked today -- measured at sprint-67
       planning: `ruff --version` -> `ruff 0.15.20`, exit 0 -- but the same Windows Device Guard /
       Application Control policy has already widened twice mid-sprint without warning
       (`lint-imports.exe` 2026-07-12, `pytest.exe` + `cfn-lint.exe` 2026-07-31), and the sprint-66
       retro (`docs/scrum/sprints/2026-07-31-sprint-66/retro.md:177`) named the next casualties as
       "`ruff.exe` or the npm toolchain" -- not `ruff.exe` alone. Same check, same rules, same files;
       `python -m ruff --version` returns the identical `ruff 0.15.20`, exit 0 -- only the entry
       point moves.)
- [ ] Code formatting check: `python -m ruff format --check .` -> exit 0
      (2026-08-02, PO-approved, preventive (STORY-210): same reasoning and same verification as
       the line above.)
- [ ] CloudFormation template lint: `python -c "from cfnlint.runner import main; main()" infra/stack.yaml` -> exit 0
      (2026-07-31, PO-approved: same Device Guard cause as `python -m pytest` above, but cfn-lint
       needed a DIFFERENT answer -- it has no `__main__`, so `python -m cfnlint` does NOT work;
       this is its real console-script entry point, `cfn-lint -> cfnlint.runner:main`.
       A blocked `regex` DLL was a second, separate symptom, cleared by reinstalling regex
       (2026.7.10 -> 2026.7.19). Verified exit 0 on the unchanged infra/stack.yaml.)
      (second half of the 2026-07-14 DoD amendment, landed STORY-088)

## Commands (frontend — live from STORY-015a, Sprint 25, run from `frontend/`)
- [ ] Frontend tests pass: `npm test` -> exit 0
- [ ] Frontend type-check/build: `npm run build` -> exit 0
- [ ] Frontend lint: `npm run lint` -> exit 0

# NOT CHANGED (STORY-210, 2026-08-02): `npm` still invokes `npm.cmd`. There is no `-m` module
# form. Measured 2026-08-02: `node "<npm_root>/bin/npm-cli.js" --version` -> `11.6.2`, exit 0 --
# a shim-free analogue that bypasses `npm.cmd`, the direct counterpart of `python -m ruff`. What
# is genuinely UNVERIFIED is whether the Application Control policy would block the `.cmd` while
# permitting `node.exe` -- nothing has tested that, and it cannot be tested until the policy
# actually blocks something. Adopting `node npm-cli.js` here is a SEPARATE PO decision, out of
# scope for STORY-210; do not read this note as "the exposure is closed" or as "no shim-free form
# exists" -- both were caught as inferences-as-measurements during sprint-67 planning.

## Commands (skill self-test)
- [ ] Skill self-test suite: `python .claude/skills/yourteam/scripts/yt_selftest.py` -> exit 0
      (2026-08-14, STORY-224: seven `.claude/skills/yourteam/scripts/tests/` modules --
       including the template-parity and `.scrum/` mojibake-encoding guards, both of which had
       already caught real defects by luck of a human remembering to run `yt_selftest.py` by
       hand -- now gate every story instead of running only when someone remembers. Interpreter
       form, never a console-script shim, matching the rest of this file's invocations (this
       machine's Windows Device Guard / Application Control policy has already widened twice
       mid-sprint unannounced, STORY-210). This section's heading carries no `run from` phrase,
       which is what runs the command from the REPO ROOT: `yt_gate.py` derives `section_cwd`
       from that phrase (`yt_gate.py:63,298`), so its absence means `cwd` stays empty and the
       command runs at `root`, not inside `frontend/` (appending it to `## Commands (backend)`
       above would run it from the same place but count as the 6th backend command, not the
       9th overall, silently turning `CLAUDE.md`'s "Backend (5)" into six).
       Blast radius: this file and `yt_gate.py` are in NO wiki article's `code_refs` -- measured
       zero at STORY-224 refinement, 2026-08-14.)

## Standing rules (mechanically checked where possible)
- [ ] Every acceptance criterion has at least one test exercising it.
- [ ] Core-zone stories (zones 1–4) are tested with in-memory canonical fixtures —
      no story in those zones requires live Dynatrace / Statuspage / Neon to pass.
      Real adapters are their own zones and use recorded fixtures + a test DB.
- [ ] No SQL above the repository layer; no vendor type inside core; vendor
      identifiers only in provenance fields. (Belt-and-suspenders to lint-imports.)
- [ ] No persisted verdicts. Availability/status are derived on read. A caching
      story may exist ONLY after a measurement story shows a real read problem.
- [ ] Forward blast radius resolved: `tier: map` wiki articles whose code_refs overlap
      this story's diff are updated or re-verified WITHIN the story, with no intervening
      commit leaving the repo asserting something false, and
      `python .claude/skills/yourteam/scripts/yt_wiki.py sweep` is CLEAN when run AFTER
      the story's last commit.
      (2026-08-12: `verified_sha` is retired. The staleness baseline is DERIVED — the
       article's own last commit — so there is no stamp to bump and a commit touching the
       article and its code_ref together is trivially not stale. This replaces both the
       "bump the sha" instruction and sprint-68's A18 "same commit" clause, which sprint-69
       redrafted to "same STORY, no false intermediate" after it proved unsatisfiable from
       both ends. The trailing "AFTER the story's last commit" is that redraft's own
       sentence, now mechanically true rather than merely stated.)
- [ ] If the story changed build/test/run commands, stack, or architecture:
      CLAUDE.md updated in the same commit.
- [ ] If the story deleted code: the reason is recorded in the story file History.

## Notes
- `lint-imports` and the FK-direction check are the non-LLM floor for the
  architecture. They are not advisory — a red contract means the story is not
  Done, with no human override (per working agreement).
- STORY-002 is responsible for making `lint-imports` and `check_fk_direction.py`
  real and exit-0 on the empty skeleton, so every later story inherits a working gate.
