# Sprint 57 Retro — 2026-07-18

1. **A1 (sprint-57): gate-then-board sequences run as SEPARATE verified tool calls** — the
   aff0a05 incident (commit message claiming a board state its own commit didn't contain,
   because a failed gate short-circuited the middle of a multi-line shell chain while a
   later line still ran) is exactly the class of error atomic, single-purpose calls prevent.
   (Rung: orchestrator procedure, recorded here + in the journal.)
2. **A2 (sprint-57): salvage pointers in briefs must be existence-verified first** (git
   cat-file on the exact path) — STORY-108's brief named a function that only existed in a
   never-verified WIP commit; the implementer handled it honestly, but the brief should not
   have asserted it. (Rung: brief-writing practice.)
3. Reality gates continue to catch what reviews structurally cannot: this sprint they
   cross-checked UI counts against API truth (877/877) and proved tint thresholds on real
   data spanning all three bands — keep API-truth assertions standard (extends sprint-56 A1).
