# Sprint 16 — Plan

**Goal:** Build the config layer (dossier §7 Option C) — `config/apps/*.yaml` + a fail-fast
loader/validator + in-memory resolvers (`signal_key→component_id`,
`component→AntiFlapThresholds`) — the prerequisite that unblocks the pipeline orchestration.

**Branch:** `sprint-16` · **Start tag:** `sprint-16-start` · **Baseline:** `c797bb3` (refinement on
branch; from main `d1beb8f`).

**Committed: 5 pts** — STORY-040a (single-story sprint).

---

## How this sprint runs (external implementation — working-agreements.md 2026-06-26)
The PO implements this plan externally onto `sprint-16`, OR (quota permitting) the orchestrator
finishes via a **Sonnet** implementer subagent (as in sprints 14/15). This `plan.md` is the only
contract — self-contained. When ready, say **"do your review"**; the orchestrator diffs
`sprint-16-start..HEAD`, runs the full six-command gate, runs the Opus spec + quality reviewers,
resolves the wiki blast radius, then review → verdict → merge → retro. **TDD + commit-after-green.
Scoped staging only. Do NOT write `.scrum/` board state.**

### The six-command DoD gate — exit 0 each
`pytest` · `lint-imports` (**5 kept / 0 broken** — config loader lives in `composition/`, which may
import core; NO new contract) · `python scripts/check_fk_direction.py` · `alembic upgrade head` ·
`ruff check .` · `ruff format --check .`. DB-gated: `scripts/dev_db.py up` → run → `down`.
**No new migration this sprint.** The config layer is pure — fully unit-testable, no DB.

### Established facts the implementer builds on
- Config loading is a **composition-zone** concern (never core — see `composition/settings.py`'s
  docstring). Put the config code under `backend/src/composition/` (e.g. `composition/config.py`, or a
  `composition/config/` subpackage if it grows). Composition may import core types.
- `AntiFlapThresholds` is `core/services/pipeline.py::AntiFlapThresholds` — frozen, fields
  `major, partial, degraded, recovery` (ints). Dossier §10 defaults: `major=5, partial=3, degraded=2,
  recovery=2`.
- The `config/` dir (repo root, outside `backend/`) holds the YAML files; it currently has only a
  `README.md` placeholder. Frozen-pydantic + `model_validator(mode="after")` pattern: mirror
  `core/domain/proposal.py::StatusProposal` / `maintenance.py::MaintenanceWindow`.

---

## STORY-040a — Config layer (5 pts) — gate + Opus reviewers

Pure composition-zone code + config files. No DB, no migration. No datetime params (the tz-aware-param
agreement is N/A). No writes (TOCTOU N/A).

### Phase A — dependency + sample config
- [ ] **A1** Add `"pyyaml"` to `[project.dependencies]` in `pyproject.toml`; run
      `.venv/Scripts/python.exe -m pip install -e ".[dev]"`. (Planning-sanctioned dependency add; not a
      DoD-command change.)
- [ ] **A2** Create `config/apps/sockshop.yaml` (representative sample for the demo app + a load
      fixture):
      ```yaml
      app:
        id: sockshop
        name: Sock Shop
        monitor_provider: dynatrace
      components:
        - { id: checkout, name: Checkout }
        - { id: catalogue, name: Catalogue }
      signals:
        - { signal_key: checkout-http, native_id: SYNTHETIC_TEST-ABC, name: Checkout HTTP, component_id: checkout }
        - { signal_key: catalogue-http, native_id: SYNTHETIC_TEST-DEF, name: Catalogue HTTP, component_id: catalogue }
      thresholds: { major: 5, partial: 3, degraded: 2, recovery: 2 }
      ```

### Phase B — config models (TDD)
- [ ] **B1** Failing test (`backend/tests/test_config.py`): construct an `AppConfig` from a valid dict;
      and each invalid shape RAISES at construction — a missing required field; a `signal.component_id`
      referencing an undeclared component; a duplicate `signal_key` within the app; a duplicate
      `component.id`; a non-positive threshold.
- [ ] **B2** Implement frozen pydantic models in `composition/config.py`:
      `ComponentConfig {id: str, name: str}`, `SignalConfig {signal_key: str, native_id: str,
      name: str, component_id: str}`, `AppConfig {id: str, name: str, monitor_provider: str,
      components: list[ComponentConfig], signals: list[SignalConfig], thresholds: AntiFlapThresholds =
      <§10 defaults>}`. A `model_validator(mode="after")` on `AppConfig` enforces: every
      `signal.component_id` references a declared component; no duplicate `signal_key`; no duplicate
      `component.id`. (Thresholds validity — positive ints — comes from `AntiFlapThresholds`; if it has
      no such guard, validate `> 0` here.) Module + class docstrings cite §7/§10/§4. Green. Commit.

### Phase C — loader + fail-fast validation (TDD)
- [ ] **C1** Failing test: `load_config(<dir with sockshop.yaml>)` returns a `Config` aggregating all
      apps; malformed YAML raises a clear error; a `signal_key` or `component.id` duplicated ACROSS two
      app files raises (ids are global/stable).
- [ ] **C2** Implement `composition/config.py::Config` (aggregate: `apps: list[AppConfig]`) +
      `load_config(config_dir: str | Path) -> Config`: read every `config/apps/*.yaml` via
      `yaml.safe_load`, build `AppConfig`s, and validate GLOBAL uniqueness of `signal_key` /
      `component.id` across apps (fail-fast with a clear error naming the offending id). An empty
      `config/apps/` → an empty `Config` (tested). Green. Commit.

### Phase D — resolvers (TDD)
- [ ] **D1** Failing test: `Config.component_for_signal("checkout-http") == "checkout"`;
      `component_for_signal("nope")` raises `UnknownSignalError`. `Config.thresholds_for("checkout")`
      returns the app's `AntiFlapThresholds` (and the §10 defaults `5/3/2/2` when the app omitted
      `thresholds`); `thresholds_for("nope")` raises `UnknownComponentError`.
- [ ] **D2** Implement the two resolver methods on `Config` (build dict indexes
      `signal_key→component_id` and `component_id→AntiFlapThresholds` once at construction). Define
      `UnknownSignalError` / `UnknownComponentError` (clear named errors, NOT leaked `KeyError`).
      Green. Commit. (These are what STORY-016a will consume.)

### Phase E — wiki blast radius + gate
- [ ] **E1** Seed a `docs/scrum/wiki/config-layer.md` article (Facts: the §7 Option-C config layer —
      file format, `load_config`, the models, the two resolvers, the composition-zone placement;
      `code_refs`: `backend/src/composition/config.py`, `config/apps/sockshop.yaml`, `pyproject.toml`;
      symbol citations). Set `verified_sha` to the latest commit + `verified_sprint: sprint-16`. If
      `pyyaml` in `pyproject.toml` makes `dev-setup-and-dod.md` / `architecture-boundary.md` stale,
      re-verify + bump those too.
- [ ] **E2** Full SIX-command gate green.

**AC mapping:** AC1 ← B2/C2 + D2 (happy path); AC2 ← B1/C1 (fail-fast cases); AC3 ← D1 (resolver
unknown-key errors); AC4 ← lint-imports 5/0 + composition placement; AC5 ← E.

---

## Standing conventions checklist (binds all new code)
- [ ] Module + public class/function docstrings cite the dossier § (§7/§10/§4).
- [ ] Frozen config models enforce referential/coherence invariants via `model_validator(mode="after")`
      + tests of BOTH rejected and valid shapes (2026-06-26).
- [ ] Resolver unknown-key behavior is a clear NAMED domain error, not a leaked `KeyError` (2026-06-25);
      empty `config/apps/` and an app with no signals tested.
- [ ] Config code lives in `composition/` (never core/adapter); core imports nothing from it; `src/`
      never imports `tests` (contract-enforced). Scoped staging.

## Notes / risks
- This is a brand-new subsystem + format design — keep the config model minimal (only what the
  resolvers + the orchestration need); `publishing.yaml`, SLA, and gap-policy config are deferred.
- `pyyaml` is the only dependency add. No migration, no new lint contract.
