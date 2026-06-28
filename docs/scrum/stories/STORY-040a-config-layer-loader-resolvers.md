---
id: STORY-040a
title: Config layer — per-app config files + fail-fast loader + in-memory resolvers
type: feature
---

## Context
Spec: dossier §7 (Mapping ownership, **decision D6 = Option C**: config owns the mapping, Git-versioned,
one file per app) + §10 (per-app anti-flap thresholds) + §4 (config loading is a COMPOSITION concern,
never core — see `composition/settings.py`). Split from STORY-040 at Sprint 16 planning. This is the
**config-reading half** — pure, no DB, no migration — and it **unblocks the pipeline orchestration
(STORY-016a)**, which needs to resolve `signal_key → component_id` and `component → AntiFlapThresholds`.
The DB seed + the signal→component spine migration are the separate STORY-040 (the topology-seed half).

The `config/` dir (repo root, outside `backend/`) is an empty placeholder today; PyYAML is not yet a
dependency.

## Description
1. **Dependency:** add `pyyaml` to `[project.dependencies]` in `pyproject.toml` (runtime — config loads
   at boot). Re-`pip install -e ".[dev]"`. (A planning-sanctioned dependency add.)
2. **Config files** (`config/apps/*.yaml`, one per app — include a representative
   `config/apps/sockshop.yaml` for the demo app + as a load fixture). Each declares:
   - `app`: `id`, `name`, `monitor_provider` (e.g. `dynatrace` — the future-provider seam).
   - `components`: list of `{ id, name }` (the internal components shown on the dashboard).
   - `signals`: list of `{ signal_key, native_id, name, component_id }` — the native_id→signal_key→
     component mapping (the three §7 arrows). `component_id` references a declared component.
   - `thresholds` (optional): `{ major, partial, degraded, recovery }` per-app anti-flap; absent →
     the dossier-§10 defaults (`5/3/2/2`).
   (Shared `config/publishing.yaml` — Statuspage page + notification channel — is DEFERRED to the
   publish/deploy story; the orchestration does not need it. Note the deferral in the story.)
3. **Config models** (composition zone, e.g. `backend/src/composition/config.py` or a
   `composition/config/` subpackage): frozen pydantic `AppConfig`, `ComponentConfig`, `SignalConfig`
   (+ a top-level `Config` aggregate). May import core types (`AntiFlapThresholds`,
   `ComponentStatus`) — composition imports core. Cross-field/referential validation via
   `model_validator(mode="after")`.
4. **Loader + fail-fast validation** `load_config(config_dir) -> Config`: read every `config/apps/*.yaml`,
   validate, and FAIL FAST with a clear error on: malformed YAML, missing required field, a
   `signal.component_id` that references no declared component (referential integrity), a duplicate
   `signal_key` or `component.id` (across all apps — ids are global/stable), or a non-positive threshold.
5. **In-memory resolvers** (what STORY-016a consumes), as methods on `Config` (or a `TopologyResolver`):
   - `component_for_signal(signal_key) -> str` — the component a signal feeds; raises a clear domain
     error (e.g. `UnknownSignalError`) on an unknown signal_key.
   - `thresholds_for(component_id) -> AntiFlapThresholds` — the component's app's thresholds (or §10
     defaults); raises on an unknown component_id.

## Acceptance Criteria (refined — PO-approved 2026-06-28)
- [ ] AC1 (load + resolve happy path): `load_config` over a valid `config/apps/` (incl. the sample
      `sockshop.yaml`) returns a `Config`; `component_for_signal(known_key)` returns the mapped
      component_id; `thresholds_for(known_component)` returns its `AntiFlapThresholds` (and the §10
      defaults `5/3/2/2` when `thresholds` is omitted). Tested.
- [ ] AC2 (fail-fast validation): each of these raises a CLEAR error at load (tested, one per case):
      malformed YAML; a missing required field; a `signal.component_id` referencing an undeclared
      component; a duplicate `signal_key`; a duplicate `component.id`; a non-positive threshold.
- [ ] AC3 (resolver edges): `component_for_signal(unknown)` and `thresholds_for(unknown)` raise a
      clear, named domain error (not a leaked `KeyError`), tested.
- [ ] AC4 (boundary): the config loader/models live in `composition/` (NOT core, NOT an adapter);
      `lint-imports` stays **5 kept / 0 broken**; core imports nothing from the config layer. No DB,
      no migration, no `src→tests` import.
- [ ] AC5 (full SIX-command DoD gate green). Forward blast radius: seed/update a wiki article for the
      config layer (or extend `architecture-boundary.md`/`dev-setup-and-dod.md`) + re-verify.

## Conventions checklist
- Module + public class/function docstrings cite dossier §7/§10/§4.
- Frozen config models enforce referential/coherence invariants via `model_validator(mode="after")` +
  tests of rejected and valid shapes (working-agreements.md 2026-06-26).
- Empty/edge tested (empty `config/apps/`, an app with no signals); resolver unknown-key behavior is a
  named error (working-agreements.md 2026-06-25). Pure reads/loads → TOCTOU N/A.
- Scoped staging; production `src/` never imports `tests` (contract-enforced).

## Resolved Questions
- **Config format → per-app YAML under `config/apps/`** (dossier §7 Option C / D6). `pyyaml` added.
- **Loader/models live in composition** (config loading is a composition concern, dossier §4).
- **`publishing.yaml` deferred** to the publish/deploy story (not needed by the orchestration).
- **Thresholds default to §10 `5/3/2/2`** when a per-app `thresholds` block is absent.

## History
- 2026-06-28: split from STORY-040 (Sprint 16 planning) as the config-reading half that unblocks the
  orchestration. Estimate **5** (config models + loader + fail-fast validation + 2 resolvers + sample
  config + tests; pure, no DB). Status: draft → ready.
