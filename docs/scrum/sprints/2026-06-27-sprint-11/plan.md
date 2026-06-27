# Sprint 11 — Plan (implemented externally by the PO / Gemini)

**Goal:** Tooling + cleanup consolidation — land the **ruff** DoD gate (STORY-033) and clear the two
carried review chores (STORY-032 decide minors, STORY-031 sprint-9 nits) before the Zone 6 API push.

**Branch:** `sprint-11` · **Start tag:** `sprint-11-start` · **Started:** 2026-06-27
**Capacity:** 6 · **Committed:** 4 — a **deliberate under-commit** (PO choice: solidify the floor and
clear the decks; Zone 6 / STORY-014 is NOT opened this sprint).
**Order (matters): STORY-033 FIRST, then STORY-032, then STORY-031.** Ruff's reformat pass touches the
whole tree and subsumes the cosmetic parts of the two chores, so it must land first.

## How this sprint runs (workflow — working-agreements.md 2026-06-26)
The PO implements these stories externally (Antigravity / Gemini), committing onto `sprint-11`. Build
to the AC + the steps below — this plan is the contract. Then the PO says "do your review" and the
orchestrator runs the DoD gate + wiki blast radius + review/retro/merge.

**All three stories are ≤ 2 pts → GATE ONLY (no LLM reviewers).** A story is Done when the DoD gate
exits 0 on every command.

### ⚠ The DoD itself changes mid-sprint (STORY-033)
Until STORY-033 lands, the gate is the existing **four** commands. **From the STORY-033 commit
onward, the gate is SIX commands** (the two ruff commands below are added). Re-run the full current
gate for each subsequent story.

- `.venv/Scripts/python.exe -m pytest` → 0
- `.venv/Scripts/lint-imports.exe` → 0 (`3 kept, 0 broken`)
- `.venv/Scripts/python.exe scripts/check_fk_direction.py` → 0  (DB-gated)
- `.venv/Scripts/alembic.exe upgrade head` → 0  (DB-gated; **NO new migration this sprint**)
- **(STORY-033 onward)** `.venv/Scripts/ruff.exe check .` → 0
- **(STORY-033 onward)** `.venv/Scripts/ruff.exe format --check .` → 0

DB-gated commands need a throwaway Postgres: `.venv/Scripts/python.exe scripts/dev_db.py up` (prints
the two `export DATABASE_URL...` lines; `down` to tear down). `dev_db.py up` now self-heals a leftover
container (STORY-030).

## Conventions checklist (working-agreements.md 2026-06-27 — all new/changed code held to these)
- **Docstrings**: any new module / public class / public function gets a docstring citing the relevant
  dossier § where applicable, mirroring peer modules (`ingest_service.py`, `pipeline.py`, `status.py`).
  (Low surface this sprint — mostly config + minor edits — but applies to any new helper.)
- **Frozen value/result types** enforce cross-field coherence with `model_validator(mode="after")` +
  test. (None expected this sprint.)
- **Empty-input / non-aligned boundary tests** where a function takes a collection/window. (N/A here.)
- **Scoped staging** — never `git add -A`; stage only the files changed for the step.
- **Follow existing import/naming/structure patterns** — and, once STORY-033 lands, let `ruff` own
  import order + formatting (do not hand-fight it).
- **Command-sync**: any change to a DoD/build/test/run command updates `.scrum/definition-of-done.md`
  + `CLAUDE.md` in the SAME commit (load-bearing for STORY-033).

**Baseline at lock:** all gates green on main @ `5e35a01` — `pytest` 275 passed, `lint-imports` 3/0.

---

## STORY-033 — Add ruff (format + import-sort) as a mechanical DoD gate (2 pts) — DO FIRST

Story file: `docs/scrum/stories/STORY-033-ruff-format-import-sort-dod.md` (AC verbatim there). Ruleset
resolved at planning to **MINIMAL**: format + isort (`I`) + pyflakes (`F`) + pycodestyle essentials
(`E`, `W`) — no broad families (`B`/`UP`/`SIM`/…) this round.

Read first: `pyproject.toml` (dev extras at line 19; `[tool.*]` sections — add `[tool.ruff]` near the
pytest/importlinter config), `.scrum/definition-of-done.md` (the canonical gate list the runner reads),
`CLAUDE.md` "Key commands" + "Tooling inventory" tables, root `definition-of-done.md` (must stay a
one-line pointer — working-agreements.md 2026-06-23).

### Steps (commit after each coherent step)
- [ ] 1. Add `ruff` to `[project.optional-dependencies].dev` in `pyproject.toml`; `pip install -e
        ".[dev]"` so `.venv/Scripts/ruff.exe` exists. Add a `[tool.ruff]` section: `target-version =
        "py313"`, `line-length = <N>` chosen to MINIMIZE reflow (run `ruff format --diff .` at a couple
        of candidates — try 100, then 88 — and pick the one with the smallest diff), `[tool.ruff.lint]`
        `select = ["E", "W", "F", "I"]`. Commit (config only). NOTE: do not commit a reformat yet.
- [ ] 2. One-pass reformat + import-sort over the tree: `ruff check --fix .` (import order / unused
        imports) then `ruff format .`. Verify the diff is FORMATTING-ONLY (no logic changes — skim it),
        then `pytest` (full suite) + `lint-imports` stay green. Commit the mechanical reformat as ONE
        clearly-labelled commit (e.g. "STORY-033: one-pass ruff format + import-sort"). (AC2)
- [ ] 3. Wire the gate: add `ruff check .` and `ruff format --check .` (each exit 0) to
        `.scrum/definition-of-done.md`; document both in `CLAUDE.md` "Key commands" + add ruff to the
        Tooling inventory table; keep root `definition-of-done.md` a one-line pointer. SAME commit
        (command-sync). (AC3)
- [ ] 4. DoD gate — now SIX commands, all exit 0 (the four existing + the two ruff). Forward blast
        radius: update `docs/scrum/wiki/dev-setup-and-dod.md` (ruff is now part of the DoD + a new
        tool) — add Facts + ensure `pyproject.toml`/`.scrum/definition-of-done.md`/`CLAUDE.md` are in
        its `code_refs`; bump `verified_sha`. Commit. (AC4)

---

## STORY-032 — decide.py quality minors (1 pt) — AFTER ruff

Story file: `docs/scrum/stories/STORY-032-decide-quality-minors.md`. **After STORY-033, AC3 (import
style + trailing blanks in `decide.py` / `test_decide.py` / `core/domain/__init__.py`) is likely
ALREADY satisfied by the ruff pass** — VERIFY (`ruff format --check .` green there) rather than redo.
The residual real work is AC1 + AC2:

### Steps
- [ ] 1. AC1 — factor the duplicated `StatusProposal(...)` construction + `create_open` + None-check out
        of the two degradation branches in `backend/src/core/services/decide.py` into one small local
        helper (only the success action `PROPOSED` vs `SUPERSEDED` differs). Keep/extend the helper's
        docstring per the conventions checklist. `test_decide.py` passes unchanged. Commit.
- [ ] 2. AC2 — guard `opened.id` before passing it to `resolve(proposal_id: int, ...)` (an `assert
        opened.id is not None` with a clear message — a `get_open` result is always persisted; this
        documents the contract, fail-loud). `test_decide.py` passes unchanged. Commit.
- [ ] 3. AC3 — confirm ruff already handled import style + trailing blanks (no-op if so; note it).
        AC4 — full DoD gate (six commands) exit 0. Blast radius: re-verify
        `core-pipeline-and-availability.md` (no Fact change expected from a DRY refactor + an assert;
        bump `verified_sha` if the cited `decide.py` lines moved). Commit.

---

## STORY-031 — Sprint 9 review cleanups: test/fixture/style nits (1 pt) — AFTER ruff

Story file: `docs/scrum/stories/STORY-031-sprint9-review-cleanups.md`. **After STORY-033, AC3 (hoist
mid-module imports in `test_statuspage_adapter.py`; blank line between `FakeProposalRepository` methods
in `fakes.py`) is likely ALREADY done by the ruff pass** — VERIFY, don't redo. The residual real work
is AC1 + AC2:

### Steps
- [ ] 1. AC1 — remove the leftover import-smoke test `test_publisher_can_be_imported` in
        `backend/tests/test_statuspage_adapter.py` (it only asserts `is not None`; real tests cover the
        adapter). Commit.
- [ ] 2. AC2 — resolve the unused `backend/tests/fixtures/statuspage/component_degraded.json`: PREFER
        adding a `publish()` test that exercises the `DEGRADED → degraded_performance` path end-to-end
        and asserts against the fixture (so the degraded mapping is covered through the publish path);
        only delete the fixture if that proves redundant. Commit.
- [ ] 3. AC3 — confirm ruff handled the style nits (no-op if so; note it). AC4 — full DoD gate (six
        commands) exit 0. Test/fixture-only → no wiki blast radius expected. Commit.

---

## Reviews (orchestrator, after the PO says "do your review")
All three stories are ≤ 2 pts → **mechanical DoD gate only** (no spec/quality LLM reviewers). The
orchestrator re-runs the full current gate (six commands once STORY-033 lands), checks the wiki blast
radius (notably `dev-setup-and-dod.md` for the DoD change), and runs review/verdict/merge/retro.
