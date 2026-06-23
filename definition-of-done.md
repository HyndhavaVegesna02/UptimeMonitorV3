# Definition of Done — Uptime Monitor V3

# Every item below must hold before any story is marked Done. The gate runner
# executes each command literally and records command, exit code, output tail,
# and commit SHA into sprint-current.yaml. Nonzero exit = not Done, no exceptions.
#
# This DoD is NOT generic — its core commands are the architecture's own CI
# contracts. The canonical boundary that the entire design rests on (core never
# imports an adapter or vendor type; the schema spine never FKs into features) is
# CHECKED ON EVERY STORY, from Sprint 0 onward. That is what makes horizontal,
# zone-by-zone slicing safe: the boundary is enforced before the logic that lives
# inside it is even written.

## Commands (backend)
- [ ] Tests pass: `pytest` → exit 0
- [ ] Import boundary holds: `lint-imports` → exit 0
      (import-linter; the three contracts from dossier §4:
       core-independence, core-internal-layering [domain←ports←services],
       adapter-independence)
- [ ] Schema FK-direction holds: `python scripts/check_fk_direction.py` → exit 0
      (the spine never references a feature table; dossier §9)
- [ ] Migrations apply on a fresh DB: `alembic upgrade head` → exit 0
      (uses the Neon DIRECT connection; never create_all)

## Commands (frontend — activate from the frontend zone onward; placeholder until then)
- [ ] Frontend tests pass: `npm test` → exit 0
- [ ] Frontend type-check/build: `npm run build` → exit 0
- [ ] Frontend lint: `npm run lint` → exit 0

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
- Command names above assume the Sprint 0 scaffold wires them. STORY-002 is
  responsible for making `lint-imports` and `check_fk_direction.py` real and
  exit-0 on the empty skeleton, so every later story inherits a working gate.
