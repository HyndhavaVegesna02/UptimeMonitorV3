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
- [ ] Tests pass: `pytest` -> exit 0
- [ ] Import boundary holds: `python -c "from importlinter.cli import lint_imports_command; lint_imports_command()"` -> exit 0
      (2026-07-12: invocation changed from the `lint-imports` exe shim, which a Windows
       Application Control policy now blocks; same check, same 8 contracts, module path)
      (import-linter; the five contracts from dossier §4, §13, and Sprint 14:
       core-independence, core-internal-layering [domain<-ports<-services],
       adapter-independence, api-feature-independence, src-no-tests)
- [ ] Code linting check: `ruff check .` -> exit 0
- [ ] Code formatting check: `ruff format --check .` -> exit 0

## Commands (frontend — live from STORY-015a, Sprint 25, run from `frontend/`)
- [ ] Frontend tests pass: `npm test` -> exit 0
- [ ] Frontend type-check/build: `npm run build` -> exit 0
- [ ] Frontend lint: `npm run lint` -> exit 0

## Standing rules (mechanically checked where possible)
- [ ] Every acceptance criterion has at least one test exercising it.
- [ ] Core-zone stories (zones 1–4) are tested with in-memory canonical fixtures —
      no story in those zones requires live Dynatrace / Statuspage / Neon to pass.
      Real adapters are their own zones and use recorded fixtures + a test DB.
- [ ] No SQL above the repository layer; no vendor type inside core; vendor
      identifiers only in provenance fields. (Belt-and-suspenders to lint-imports.)
- [ ] No persisted verdicts. Availability/status are derived on read. A caching
      story may exist ONLY after a measurement story shows a real read problem.
- [ ] Forward blast radius resolved: wiki articles whose code_refs overlap this
      story's diff are updated or re-verified (verified_sha bumped).
- [ ] If the story changed build/test/run commands, stack, or architecture:
      CLAUDE.md updated in the same commit.
- [ ] If the story deleted code: the reason is recorded in the story file History.

## Notes
- `lint-imports` and the FK-direction check are the non-LLM floor for the
  architecture. They are not advisory — a red contract means the story is not
  Done, with no human override (per working agreement).
- STORY-002 is responsible for making `lint-imports` and `check_fk_direction.py`
  real and exit-0 on the empty skeleton, so every later story inherits a working gate.
