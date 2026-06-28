# Sprint 13 — Retrospective

**Outcome:** 7/7 points accepted (STORY-014b 5 + STORY-035 2). The Dashboard + Approvals read
endpoints and their two new read ports are live; the two STORY-014 API minors are cleared.
Velocity history now `…, 4, 7, 7`; last-3 mean **6.0** — fully recovered from the sprint-11 dip.

## What went well
- A clean two-story sprint; the external implementer hit the plan closely (Component type, both
  ports, both five-file features, wiki updates all landed in the right shape).
- The `httpx2` deprecation fix is genuinely clean — a real package, warning gone (verified 0
  occurrences in the pytest run).
- The wiki blast-radius machinery caught 5 articles drifting (from a ruff-format pass + the inline
  fix) and the compile pass re-verified them — no stale claim reached `main`.

## What dragged — one fix loop on STORY-014b (3 findings), two recurring
1. **MAJOR — `src -> tests` import slipped the mechanical floor.** `composition/app.py` imported
   `tests.fakes` into production; no import-linter contract forbids `src` importing `tests`, so the
   gate passed and only the Opus reviewer caught it. This is precisely the class the
   "boundary violations are build failures" principle exists to mechanize.
2. **Five-file-shape test omitted AGAIN** (STORY-014 sprint 12 + STORY-014b sprint 13 — both caught
   in a fix loop). The AC stated it both times; the implementer missed it both times.
3. AC2 multiple-open-proposals test missing (one-off).

No blockers, no effort-cap trips, no hotfixes.

## Process changes (PO-approved)
1. **New chore STORY-038** (draft): add a 5th `import-linter` contract forbidding `src` from
   importing `tests` (+ command-sync DoD/CLAUDE/architecture-boundary update). Mechanizes the catch
   so this MAJOR class fails the gate, not just a reviewer — the second of the two allowed
   tooling-change moments (retro). Like STORY-033 added ruff.
2. **New working agreement (2026-06-28):** every new five-file API feature ships its five-file-shape
   test (exact `{__init__,controller,models,validation,service}.py` set) in the same story, as a
   named conventions-checklist deliverable. (Generalizes the twice-missed AC into the standing
   checklist.)

## Follow-up backlog (drafts)
- **STORY-038** — the `src -> tests` contract (above).
- **STORY-014c** — Availability + Check History read endpoints.
- **STORY-036 / STORY-037** — Maintenance / Publications feature modules (need new backing state).

## Note
STORY-038 should be sequenced early in a future sprint (cheap, ~1 pt, and it hardens the floor for
all subsequent API work).
