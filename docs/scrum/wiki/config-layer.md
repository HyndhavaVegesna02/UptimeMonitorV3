---
title: Config layer — per-app YAML files, fail-fast loader, and in-memory resolvers
code_refs: [backend/src/composition/config.py, config/apps/httpcheck.yaml, pyproject.toml]
verified_sha: ed19084
verified_sprint: sprint-22
status: verified
---

## Facts (verified against code)

### Design decision (dossier §7 Option C / D6)
Config owns the signal→component mapping.  One Git-versioned `*.yaml` file per
app lives under `config/apps/` (repo root, outside `backend/` — a topology
file, not a code file per dossier §4).  The loader reads the whole directory
at boot and builds in-memory indexes.  No DB read; the config is the source of
truth for the mapping.

### File format (`config/apps/httpcheck.yaml`)
Each file is a YAML document with four top-level keys:

```yaml
app:          # id, name, monitor_provider
components:   # list of {id, name, statuspage_component_id?}
signals:      # list of {signal_key, native_id, name, component_id, interval_seconds}
thresholds:   # optional {major, partial, degraded, recovery} — dossier §10 defaults 5/3/2/2
```

`statuspage_component_id` (optional, STORY-016) is the non-secret Statuspage
component id this component publishes to — topology, not a secret (the live
publish chain reads it via `Config.statuspage_mapping()`).

`signal_key` and `component.id` must be **globally unique** across all app
files (ids are stable references used by the pipeline + dashboard).
`component_id` on each signal must reference a component declared in the same
app file (referential integrity enforced at load time).

### Config models (`backend/src/composition/config.py`)
Three frozen pydantic models, all with `model_config = ConfigDict(frozen=True)`:

- `ComponentConfig{id: str, name: str, statuspage_component_id: str | None}` — a
  single component declaration. `statuspage_component_id` (optional, default
  `None`, STORY-016) carries the Statuspage component id for the live publish
  mapping.
- `SignalConfig{signal_key, native_id, name, component_id, interval_seconds}` — the three §7
  mapping arrows: native_id (provider key) → signal_key (canonical internal
  key) → component_id, plus the expected monitor cadence `interval_seconds` (STORY-016a, validated `> 0`).
- `AppConfig{id, name, monitor_provider, components, signals, thresholds}` —
  the full per-app config.  `thresholds` defaults to the §10 values
  (`AntiFlapThresholds(major=5, partial=3, degraded=2, recovery=2)`) when
  omitted.  A `model_validator(mode="after")` enforces:
  1. Every `signal.component_id` references a declared component.
  2. No duplicate `signal_key` within the app.
  3. No duplicate `component.id` within the app.
  4. All threshold fields are positive integers.

Symbol citations:
- `backend/src/composition/config.py::ComponentConfig`
- `backend/src/composition/config.py::SignalConfig`
- `backend/src/composition/config.py::AppConfig`
- `backend/src/composition/config.py::AppConfig::_validate_referential_and_uniqueness`

### Config aggregate (`backend/src/composition/config.py::Config`)
`Config(apps: list[AppConfig])` is the runtime aggregate built by `load_config`.
At `__init__` it builds three O(1) dict indexes:
- `_signal_to_component: dict[str, str]` (signal_key → component_id)
- `_component_to_thresholds: dict[str, AntiFlapThresholds]` (component_id → thresholds)
- `_signal_key_to_signal: dict[str, SignalConfig]` (signal_key → SignalConfig)

These are the indexes consumed by the two resolvers.

### Fail-fast loader (`backend/src/composition/config.py::load_config`)
```python
def load_config(config_dir: str | Path) -> Config
```
Reads every `*.yaml` in `config_dir`, validates each file into an `AppConfig`
(intra-app invariants), then enforces **global uniqueness** of `signal_key` and
`component.id` across all files.  Raises a clear `ValueError` (naming the
offending id and both filenames) on any violation.  An empty directory returns
an empty `Config` (no error).  Empty apps (zero signals) are valid.

Fail-fast error cases (all raise with a descriptive message at `load_config` time):
- Malformed YAML (`yaml.YAMLError` re-raised as `ValueError` with filename).
- Missing required field (pydantic `ValidationError` re-raised with context).
- `signal.component_id` referencing an undeclared component.
- Duplicate `signal_key` within an app.
- Duplicate `component.id` within an app.
- Duplicate `signal_key` or `component.id` across apps.
- Non-positive threshold field.

### Named domain errors
- `backend/src/composition/config.py::UnknownSignalError` (inherits `ValueError`)
- `backend/src/composition/config.py::UnknownComponentError` (inherits `ValueError`)

Both follow the codebase convention (`ProposalNotFoundError(ValueError)`).
Neither is a raw `KeyError` leak — resolvers always raise the named type.

### In-memory resolvers (what STORY-016a will consume)
Two methods on `Config`:

```python
def component_for_signal(self, signal_key: str) -> str
```
Returns the `component_id` that `signal_key` feeds.  Raises `UnknownSignalError`
on an unknown key.

```python
def thresholds_for(self, component_id: str) -> AntiFlapThresholds
```
Returns the app's `AntiFlapThresholds` (or the §10 defaults when the app omitted
the `thresholds` block — the default is baked in at `AppConfig` construction, so
the index always has a value).  Raises `UnknownComponentError` on an unknown id.

```python
def signal(self, signal_key: str) -> SignalConfig
```
Returns the full `SignalConfig` for `signal_key` (STORY-016a). Raises `UnknownSignalError` on an unknown key.

```python
def statuspage_mapping(self) -> dict[str, str]
```
Returns `{component_id: statuspage_component_id}` for every component (across all
apps) that declares one; components without a `statuspage_component_id` are
skipped (STORY-016). The live publish chain feeds this to `StatuspagePublisher`
as its `component_mapping`. Symbol: `backend/src/composition/config.py::Config.statuspage_mapping`.


### Composition-zone placement (dossier §4)
`backend/src/composition/config.py` lives in the composition zone.  It imports
`AntiFlapThresholds` from `src.core.services.pipeline` (composition → core is
allowed).  Core never imports from `src.composition` (enforced by the
`core-independence` import-linter contract).  No new contract was added; the
five existing contracts all stay KEPT (verified sprint-16).

### Dependency
`pyyaml` was added to `[project.dependencies]` in `pyproject.toml` (sprint-16,
STORY-040a Phase A).  It is a runtime dependency — config loads at boot.

## Inference (synthesis, not verified)
- `config/apps/` is a topology directory; adding a new app file is a config
  change, not a code change.  The loader picks it up at boot via `glob("*.yaml")`.
- The §10 defaults (`5/3/2/2`) are baked into `AppConfig.thresholds` as a
  pydantic field default, not as a runtime fallback in the resolver — so the
  index always has a value and `thresholds_for` never needs to fall back.
- `create_app` (`app.py::create_app`) triggers fail-fast config loading at construction time from `CONFIG_DIR` (default: `"config/apps"`). If configuration is invalid, it raises `ValueError` immediately, blocking server boot (dossier §17).

## History
- sprint-16: created (STORY-040a — config layer bootstrap: models + loader +
  resolvers + sample config/apps/sockshop.yaml). verified_sha = 9b60fac.
- sprint-17: updated (STORY-016a — config layer updated to support `interval_seconds` for signal cadences). verified_sha = b062132.
- sprint-18: updated (STORY-040 — config is loaded fail-fast in `create_app` and stored in `app.state.seed_config` for database seeding at lifespan startup). verified_sha = 19eefc8.
- sprint-20: updated (STORY-016 — `ComponentConfig.statuspage_component_id` + `Config.statuspage_mapping()` for the live publish chain; sample config is now `config/apps/httpcheck.yaml` (sockshop dropped)). verified_sha = d9c2a77.
- sprint-22: re-verified (STORY-016c). No config-layer change; the only `pyproject.toml` edit was a ruff
  `.agents/` exclude unrelated to the config loader/resolvers. verified_sha = ed19084.
