---
title: Config layer — per-app YAML files, fail-fast loader, and in-memory resolvers
code_refs: [backend/src/composition/config.py, config/apps/httpcheck.yaml, pyproject.toml]
tier: map
verified_sprint: sprint-69
status: verified
# tier: map, `verified_sha` dropped 2026-08-12 (yourteam 2.3.0): the staleness baseline is now
# this article's own last commit, derived by git, so there is no stamp to keep current.
# WHAT THIS EDIT DID AND DID NOT VERIFY: it did not re-read these Facts against code. It
# established, per-article, that NO code_ref has moved since this article's last commit
# (`git diff <that commit>..HEAD -- <code_refs>` -> empty, and the sweep is CLEAN at HEAD),
# so the verification earned at sprint 69 is not invalidated by anything since. That is
# the same guarantee `status: verified` has always carried here; the frontmatter migration
# adds no new claim. Articles nobody could make that statement for were demoted to `stale`
# in the same pass, not laundered.
---

## Facts (verified against code)

### Design decision (dossier §7 Option C / D6)
Config owns the signal→component mapping.  One Git-versioned `*.yaml` file per
app lives under `config/apps/` (repo root, outside `backend/` — a topology
file, not a code file per dossier §4).  The loader reads the whole directory
at boot and builds in-memory indexes.  No DB read; the config is the source of
truth for the mapping.

### Authoring shape (STORY-146, sprint-62) — nested monitors, declared
locations, freshness block

`config/apps/*.yaml`'s **authoring** shape nests monitors under their
component and adds two new per-app blocks; the **consumption** shape
(`AppConfig.signals: list[SignalConfig]`) is unchanged, so no pre-existing
consumer moved:

```yaml
app:          # id, name, monitor_provider
components:   # list of {id, name, statuspage_component_id?, monitors: [...]}
locations:    # optional, alias -> {native_id, label}
freshness:    # optional {stale_after_cycles, reentry_cycles} — CYCLE COUNTS
thresholds:   # optional {major, partial, degraded, recovery} — dossier §10 defaults 5/3/2/2
```

Each `components[].monitors[]` entry is `{signal_key, native_id, name,
interval_seconds, expected_locations?}` — **no `component_id` field**.
Ownership is structural: a monitor's `component_id` is always its parent
component's `id`, never authored. `signals:` as a raw top-level (flat, sibling)
YAML key is now REJECTED (`FlatSignalsRejectedError`) — the referential
integrity problem it used to risk (a `component_id` typo referencing nothing)
is now structurally impossible instead of separately validated.

`config/apps/httpcheck.yaml` was migrated to this shape with **nesting only**
— it gained no `locations:` block and no `expected_locations` entries, because
the real Dynatrace location ids/names cannot be verified while the trial is
expired (memory: `dynatrace-trial-expired`), and inventing them would put
fabricated vendor identifiers into live config. `locations:`/`expected_locations`
are demo/fixture-only for now (STORY-176 opens sprint 63).

### The derive mechanism (`backend/src/composition/config.py::AppConfig::_derive_signals_from_monitors`)
Field extraction is INLINE in this validator. Two helpers
(`_component_id_and_monitors`, `_monitor_fields`) originally wrapped it to
accept either `ComponentConfig` instances or raw dicts; the dict branches were
dead across the whole suite — every call site passes constructed instances,
since `load_config` builds them before constructing `AppConfig` — and were
deleted in the sprint-62 rework (F1) rather than kept untested.
A `model_validator(mode="before")` on `AppConfig` synthesizes the flat
`signals` list from `components[].monitors` at construction time, stamping
each monitor's parent component id onto the `SignalConfig` it derives. This is
what keeps `AppConfig.signals` — and every one of its seven surviving readers
(below) — working with **no change to their expressions**, even though no
monitor ever authors a `component_id`.

The same validator RAISES `FlatSignalsRejectedError` (rather than silently
deriving over it) if the caller explicitly supplies a non-empty `signals=` on
direct `AppConfig(...)` construction — an unconditional derive would otherwise
silently discard the caller's value, turning a bogus reference into a silent
empty list instead of a loud failure.

### Config models (`backend/src/composition/config.py`)
Six frozen pydantic models, all with `model_config = ConfigDict(frozen=True)`:

- `MonitorConfig{signal_key, native_id, name, interval_seconds, expected_locations: list[str] = []}`
  — a monitor nested under its component (STORY-146 AC1). No `component_id`
  field (structural ownership). `interval_seconds` validated `> 0` (same
  invariant as `SignalConfig`) via the shared `PositiveIntervalSeconds`
  annotated type — the sprint-62 rework replaced two byte-identical
  `_require_positive_interval` model_validator methods with one
  `Annotated[int, AfterValidator(...)]`; error text is unchanged for both
  models, and both now carry rejected-shape tests (zero AND negative). Deliberately NO `kind:` field — `native_kind` is discovered from
  the vendor's `event.type` per row (`dispatch.py:44`); a declared field
  nothing reads would let config lie.
- `ComponentConfig{id, name, statuspage_component_id: str | None, monitors: list[MonitorConfig] = [], group: str | None = None, description: str | None = None}`
  — a component declaration, now carrying its nested monitors, plus two optional display
  fields (STORY-147): `group` (a decorative sub-label, free text — NOT a closed enum, so
  a new category is a config change, never a code change) and `description` (a one-line
  operator-facing description, capped at 80 characters). `group` is normalized to a
  lowercase slug by a `field_validator(mode="after")` ON THIS MODEL
  (`ComponentConfig::_normalize_group_case`) — `Commerce`/`COMMERCE`/`commerce` all
  construct as `commerce`; display-casing is the frontend's concern. The validator never
  raises (it only lowercases); slug-SAFETY (character set) is a separate check, described
  below, that must live in `load_config` rather than on this model for the same
  pydantic-swallows-the-subclass reason `InvalidFreshnessError`/`UndeclaredLocationAliasError`
  do. Neither field reaches Statuspage — the publish payload
  (`backend/src/adapters/outbound/statuspage/__init__.py:54`, `{"component": {"status": vendor_status}}`)
  and `Config.statuspage_mapping()` are built from `statuspage_component_id`/`status` alone.
- `SignalConfig{signal_key, native_id, name, component_id, interval_seconds}` —
  UNCHANGED shape; still the consumption type every existing reader sees, now
  always synthesized rather than authored.
- `LocationConfig{native_id, label}` — a declared probe location alias
  (STORY-146 AC3). `native_id` matches the vendor's opaque
  `dt.entity.synthetic_location` value; `label` is the operator-facing name.
  Aliases are short, non-cloud-provider strings (e.g. `loc-a`, `mumbai`,
  `dublin` — deliberately not AWS region names).
- `FreshnessConfig{stale_after_cycles: int = 3, reentry_cycles: int = 2}` —
  per-app freshness thresholds (STORY-146 AC4). **CYCLE COUNTS, not seconds**
  — multiplied by the owning monitor's own `interval_seconds` at the point of
  use (STORY-151/152 consume this; this article's story only loads/validates/
  exposes the counts). Carries plain `int` fields with **NO** pydantic
  validator, deliberately — positivity is checked in `load_config`
  (`InvalidFreshnessError`), because a `model_validator` cannot raise a named
  error that survives to the caller (see the named-errors section below).
- `AppConfig{id, name, monitor_provider, components, signals, thresholds, locations, freshness}` —
  the full per-app config. `signals` is DERIVED (see above), not authored.
  `locations: dict[str, LocationConfig] = {}` and
  `freshness: FreshnessConfig = FreshnessConfig()` are per-app, no global merge
  (AC6). `thresholds` still defaults to the §10 values when omitted.
  A `model_validator(mode="after")` (`_validate_uniqueness_and_thresholds`)
  enforces:
  1. No duplicate `component.id` within the app.
  2. No duplicate `signal_key` within the app.
  3. All threshold fields are positive integers.

  **The referential-integrity rule this validator used to enforce — "every
  `signal.component_id` references a declared component" — is DELETED**
  (STORY-146 AC2): it is now structurally impossible to violate, since every
  derived signal's `component_id` is its parent component's id by
  construction. A monitor can no longer author a bogus reference at all.

Symbol citations:
- `backend/src/composition/config.py::MonitorConfig`
- `backend/src/composition/config.py::ComponentConfig`
- `backend/src/composition/config.py::SignalConfig`
- `backend/src/composition/config.py::LocationConfig`
- `backend/src/composition/config.py::FreshnessConfig`
- `backend/src/composition/config.py::AppConfig`
- `backend/src/composition/config.py::AppConfig::_derive_signals_from_monitors`
- `backend/src/composition/config.py::AppConfig::_validate_uniqueness_and_thresholds`

### Named config-authoring errors (STORY-146 AC5; STORY-147 AC1 adds a fifth)
`backend/src/composition/config.py::ConfigError(ValueError)` is the base for
five subclasses, all raised by `load_config` **OUTSIDE** its
`except (TypeError, ValueError)` block (below the try that constructs
`AppConfig`), so the named subclass survives to the caller:

- `FlatSignalsRejectedError` — a raw top-level `signals:` key in a YAML file
  (checked directly against `raw`, before/independent of `AppConfig`
  construction); ALSO raised (as itself, inside the code) by
  `AppConfig`'s `mode="before"` derive validator on an explicit non-empty
  `signals=` at direct construction — but at THAT call site pydantic wraps it
  as `ValidationError`, losing the subclass (see below); the important
  behaviour there is "raises loudly", not "exact class survives".
- `UndeclaredLocationAliasError` — a monitor's `expected_locations` names an
  alias not declared in the same app's `locations:` block. Checked after
  `AppConfig` construction succeeds, iterating `app.components[].monitors[].expected_locations`
  against `set(app.locations.keys())`.
- `InvalidFreshnessError` — `app.freshness.stale_after_cycles` or
  `.reentry_cycles` is non-positive. Checked after construction (this is why
  `FreshnessConfig` itself carries no validator).
- `DuplicateAppIdError` — two config files declare the same `app.id`. Added by
  the sprint-62 quality rework (F4) after a probe showed a duplicate loaded
  SILENTLY while one file's `locations`/`freshness` were discarded: the second
  file simply won `freshness_for()`/`locations_for()`. This only became
  reachable when STORY-146 made `app.id` a lookup key — before that nothing
  resolved by app id. Checked beside the existing global
  `signal_key`/`component.id` uniqueness checks, and names BOTH filenames.
- `InvalidComponentFieldError` (STORY-147 AC1) — a component's `group` is not
  slug-safe (`^[a-z0-9]+(-[a-z0-9]+)*$`) AFTER `ComponentConfig`'s own
  case-normalization, or its `description` exceeds 80 characters
  (`_MAX_DESCRIPTION_LENGTH`). Checked in a loop over `app.components` placed
  after the AC4 freshness checks and before the global uniqueness checks,
  naming the yaml file, the component id, and the offending field — never a
  bare `ValueError`, never silent truncation. The 80-char boundary is tested
  non-aligned (exactly 80 is valid, 81 raises) and shown RED by mutation
  (`>` swapped for `>=` fails the exact-80 case naming the component; reverted,
  `git diff` empty).

**Probed (twice, independently):** a `ValueError` subclass raised inside a
pydantic `model_validator` — in EITHER `mode="before"` or `mode="after"` — is
converted to `pydantic.ValidationError` by pydantic-core, losing the
subclass. `ValidationError` *is* a `ValueError`, so `load_config`'s
`except (TypeError, ValueError)` would then re-raise it as a bare
`ValueError(f"Invalid config in {file}: …")` — losing the name a second time.
This is exactly why the three checks above live in `load_config`'s own code,
after the try/except, where `yaml_path`, `raw`, and the constructed `app` are
all still in scope to build the message.

### Named resolver errors
- `backend/src/composition/config.py::UnknownSignalError` (inherits `ValueError`)
- `backend/src/composition/config.py::UnknownComponentError` (inherits `ValueError`)
- `backend/src/composition/config.py::UnknownAppError` (inherits `ValueError`,
  STORY-146 — raised by `locations_for`/`freshness_for` on an unknown `app_id`)

All three follow the codebase convention (`ProposalNotFoundError(ValueError)`).
None is a raw `KeyError` leak — resolvers always raise the named type.

### Config aggregate (`backend/src/composition/config.py::Config`)
`Config(apps: list[AppConfig])` is the runtime aggregate built by `load_config`.
At `__init__` it builds five O(1) dict indexes:
- `_signal_to_component: dict[str, str]` (signal_key → component_id)
- `_component_to_thresholds: dict[str, AntiFlapThresholds]` (component_id → thresholds)
- `_signal_key_to_signal: dict[str, SignalConfig]` (signal_key → SignalConfig)
- `_app_id_to_locations: dict[str, dict[str, LocationConfig]]` (STORY-146 AC6)
- `_app_id_to_freshness: dict[str, FreshnessConfig]` (STORY-146 AC6)

### Fail-fast loader (`backend/src/composition/config.py::load_config`)
```python
def load_config(config_dir: str | Path) -> Config
```
Reads every `*.yaml` in `config_dir`, validates each file into an `AppConfig`
(intra-app invariants), runs the three STORY-146 named-error checks described
above, then enforces **global uniqueness** of `signal_key` and `component.id`
across all files. Raises a clear, descriptive error (naming the offending
file/component/monitor/alias/field) on any violation. An empty directory
returns an empty `Config` (no error). Empty apps (zero signals) are valid.

Fail-fast error cases (all raise with a descriptive message at `load_config` time):
- Malformed YAML (`yaml.YAMLError` re-raised as `ValueError` with filename).
- Missing required field (pydantic `ValidationError` re-raised with context).
- Duplicate `signal_key` within an app.
- Duplicate `component.id` within an app.
- Duplicate `signal_key` or `component.id` across apps.
- Non-positive threshold field.
- A raw top-level `signals:` key (`FlatSignalsRejectedError`).
- A monitor's `expected_locations` naming an undeclared alias
  (`UndeclaredLocationAliasError`).
- A non-positive `freshness.stale_after_cycles`/`reentry_cycles`
  (`InvalidFreshnessError`).
- The same `app.id` declared in two files (`DuplicateAppIdError`).
- A component's `group` not slug-safe after normalization, or `description`
  over 80 characters (`InvalidComponentFieldError`, STORY-147 AC1).

### In-memory resolvers
Six methods on `Config`:

```python
def component_for_signal(self, signal_key: str) -> str
```
Returns the `component_id` that `signal_key` feeds. Raises `UnknownSignalError`
on an unknown key.

```python
def thresholds_for(self, component_id: str) -> AntiFlapThresholds
```
Returns the app's `AntiFlapThresholds` (or the §10 defaults when the app
omitted the `thresholds` block). Raises `UnknownComponentError` on an unknown id.

```python
def signal(self, signal_key: str) -> SignalConfig
```
Returns the full `SignalConfig` for `signal_key`. Raises `UnknownSignalError`
on an unknown key.

```python
def locations_for(self, app_id: str) -> dict[str, LocationConfig]
```
Returns the declared `locations:` map for `app_id` (STORY-146 AC6), per-app —
no global merge, matching the `thresholds_for` precedent. Raises
`UnknownAppError` on an unknown `app_id`.

```python
def freshness_for(self, app_id: str) -> FreshnessConfig
```
Returns the `FreshnessConfig` for `app_id` (STORY-146 AC4/AC6), per-app — no
global merge. Raises `UnknownAppError` on an unknown `app_id`.

```python
def statuspage_mapping(self) -> dict[str, str]
```
Returns `{component_id: statuspage_component_id}` for every component (across
all apps) that declares one; components without a `statuspage_component_id`
are skipped. The live publish chain feeds this to `StatuspagePublisher` as its
`component_mapping`.

### Seven surviving readers of `app.signals` (STORY-146 AC7)
`AppConfig.signals` stays the read API — unchanged expressions, verified by
grep against the story diff, not by line number (this story's own additions
shift every other line in the file):

- `backend/src/composition/config.py::Config.__init__` — `for sig in app.signals:`
- `backend/src/composition/config.py::load_config` — `for sig in app.signals:`
  (global signal_key uniqueness check)
- `backend/src/composition/config.py::AppConfig::_validate_uniqueness_and_thresholds` —
  `for sig in self.signals:` (duplicate signal_key check — NOT the deleted
  referential check, which was a separate loop over the same list)
- `backend/src/composition/run.py:136` — `for signal in app.signals:`
- `backend/src/composition/seed_dynamo.py:76` — `for sig in app.signals:`
  (re-keyed from line 60 by STORY-147's component-seeding block gaining 16
  lines above this loop — see History)
- `backend/src/composition/vendor_health.py:106` — `for signal in app.signals:`
- `scripts/seed_topology.py:48` — `sum(len(app.signals) for app in config.apps)`

`run.py` is unchanged by this story (verified — not in its diff) even though
it is one of these seven readers.

### Composition-zone placement (dossier §4)
`backend/src/composition/config.py` lives in the composition zone.  It imports
`AntiFlapThresholds` from `src.core.services.pipeline` (composition → core is
allowed).  Core never imports from `src.composition` (enforced by the
`core-independence` import-linter contract).  On the core↔composition axis this placement is
governed by `core-independence` alone — though `adapters-edge-only` and `api-outward-independence`
also forbid their own zones from importing `src.composition`, so `config.py` is fenced from three
directions, not one. STORY-206 (sprint-69) added a ninth contract, unrelated to `config.py`; all
nine stay KEPT.

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
- `locations:`/`expected_locations` declaration (STORY-146 AC3) is consumed by
  nothing yet — the completeness-denominator consumer is a separate future
  story (STORY-152). `freshness:` (AC4) is likewise loaded/validated/exposed
  only; the cycle→seconds multiplication is STORY-151/152.

## History
- sprint-43 (STORY-078, unrelated story — mechanical staleness sweep only): this article's
  `code_refs` include `pyproject.toml`, which changed only in the `core-internal-layering`
  import-linter contract (added the `src.core.queries` layer — the CQRS-lite move, see
  [[architecture-boundary]]). Nothing about the config layer / `config/apps` loading changed.
  No Facts changed. verified_sha = 6859f17.
- sprint-16: created (STORY-040a — config layer bootstrap: models + loader +
  resolvers + sample config/apps/sockshop.yaml). verified_sha = 9b60fac.
- sprint-17: updated (STORY-016a — config layer updated to support `interval_seconds` for signal cadences). verified_sha = b062132.
- sprint-18: updated (STORY-040 — config is loaded fail-fast in `create_app` and stored in `app.state.seed_config` for database seeding at lifespan startup). verified_sha = 19eefc8.
- sprint-20: updated (STORY-016 — `ComponentConfig.statuspage_component_id` + `Config.statuspage_mapping()` for the live publish chain; sample config is now `config/apps/httpcheck.yaml` (sockshop dropped)). verified_sha = d9c2a77.
- sprint-22: re-verified (STORY-016c). No config-layer change; the only `pyproject.toml` edit was a ruff
  `.agents/` exclude unrelated to the config loader/resolvers. verified_sha = ed19084.
- sprint-25: re-verified (STORY-015a). No config-layer change; the only `pyproject.toml` edit was adding
  `"frontend"` to the ruff exclude for the new SPA, unrelated to the config loader/resolvers.
  verified_sha = 08d91e7.
- sprint-28: re-verified (STORY-042). No config-layer change; the only `pyproject.toml` edit was
  adding `uvicorn[standard]` to the dev extras. The new `composition/asgi.py` entrypoint reads the
  same `config_dir` (default `config/apps`) via `create_app()`/`load_config` — no change to the
  loader/resolvers this article describes. verified_sha = 6303247.
- sprint-30: re-verified (STORY-044). No config-layer change; `SignalConfig.interval_seconds`
  already existed (STORY-016a) and is unchanged — STORY-044 only made `seed_topology` persist it to
  the new `signals.interval_seconds` column (see [[migrations-and-db]]). The only `pyproject.toml`
  edit was adding `"src.api.v1.topology"` to the `api-feature-independence` import-linter contract,
  unrelated to the config loader/resolvers. verified_sha = 280c1e3.
- sprint-31: re-verified (STORY-048, a TEMPORARY feature — see [[sample-mode]]). No config-layer
  change; the only `pyproject.toml` edit was adding `"src.api.v1.sample_mode"` to the
  `api-feature-independence` import-linter contract, unrelated to the config loader/resolvers.
  verified_sha = 0ea652e.
- sprint-36: re-verified (STORY-043, mechanical staleness sweep only). No config-layer change; the
  only `pyproject.toml` edit was adding `python-dotenv` to `[project.dependencies]` (a
  `.env`-loading defect fix at the two process entrypoints — see [[dev-setup-and-dod]] and
  [[ingest-service-and-pull-loop]]), unrelated to the config loader/resolvers. verified_sha =
  6a33edb.
- sprint-46 (STORY-082): Re-verified after pyproject.toml changes. verified_sha -> abd8609.
- sprint-62 (STORY-146): nested-authoring rewrite — `monitors:` nested under
  `components[]` (no `component_id` field; structural ownership),
  `AppConfig.signals` now DERIVED via a `mode="before"` validator
  (`FlatSignalsRejectedError` on flat authoring at both the raw-YAML and
  direct-construction levels), the referential-integrity check DELETED
  (structurally redundant), two new per-app blocks (`locations:`,
  `freshness:`) with two new resolvers (`locations_for`/`freshness_for`) and
  two new models (`LocationConfig`, `FreshnessConfig`), and a
  `ConfigError(ValueError)` hierarchy for authoring errors that must survive
  outside pydantic validators. `config/apps/httpcheck.yaml` migrated
  (nesting only — no `locations:`, per AC8). verified_sha -> d004da7.
- sprint-62 quality rework (STORY-146 F1-F4 + two also-fixed items): dead dict branches
  deleted from the derive mechanism and the helpers inlined (F1); `MonitorConfig`'s `> 0`
  invariant now has rejected-shape tests (F2 — it had none, while THIS ARTICLE already
  asserted the invariant as verified Fact); a happy-path test added for `expected_locations`
  alias resolution (F3 — previously the only non-empty `expected_locations` in the suite was
  the FAILING case, so an implementation rejecting every alias would have stayed green);
  `DuplicateAppIdError` added (F4); and the duplicated interval validator replaced by the
  shared `PositiveIntervalSeconds` type. verified_sha -> 81bf71a.
- sprint-63 (STORY-181): the sweep flagged `pyproject.toml`. The only change there was a
  comment-only fix to an unrelated vendor-subpackage note (`adapters-independence` contract
  comment) — this article cites `pyproject.toml` for dependency/config concerns, not that
  comment. No Fact changed; re-verified only. verified_sha -> b272c32.
- sprint-68 (STORY-215, citation fix, `verified_sha` bumped `b272c32` -> `d24f59b`): the
  "Seven surviving readers of `app.signals`" Fact cited `scripts/seed_topology.py:44`;
  STORY-215 AC4 (`b887883`) removed a line from that file, shifting the real line to
  `:47`, and a later fix-round comment edit shifted it again to `:48` — corrected here to
  `:48`, in both this article and `config.py`'s own docstring. This was invisible to the
  mechanical staleness sweep because `scripts/seed_topology.py` (like `run.py`,
  `seed_dynamo.py`, and `vendor_health.py`, the other three files in that same Fact) is
  **not** in this article's `code_refs` above — only `config.py` is, so the sweep's
  git-diff-since-`verified_sha` check has nothing to compare `seed_topology.py` against.
  Caught by a manual citation-shape sweep, not the tool. `git diff b272c32..HEAD` across
  every `code_refs` file confirms `config.py` was the only one that changed since
  `b272c32`, and its sole change is this same docstring line — self-authored and directly
  verified (`sum(len(app.signals) for app in config.apps)` really is at `:48` in
  `scripts/seed_topology.py` at HEAD), not a Fact re-read blind, so `verified_sha` moves
  to `d24f59b` (this fix's own commit). Two adjacent citations in the same Fact —
  `backend/src/composition/seed_dynamo.py:56` (real line: `60`) and
  `backend/src/composition/vendor_health.py:97` (real line: `106`) — are ALSO stale, but
  predate sprint-68 (drifted under STORY-204/STORY-205, before this sprint started, and
  untouched by any sprint-68 commit) and are left as pre-existing
  findings, not fixed here.
- sprint-69 (STORY-206, verified_sha bumped `d24f59b` -> `a192e17`): `pyproject.toml` (a
  `code_ref`) gained a ninth `lint-imports` contract, `inbound-adapters-dont-persist` (ZR-1's
  guard — see [[zone-rules]]), unrelated to `config.py`. The "Composition-zone placement" Fact's
  "eight existing contracts all stay KEPT" is corrected to nine; no other Fact touches contract
  count or `config.py` behaviour.
- sprint-69 (STORY-206 rework, quality review MINOR): "No new contract was added by this story"
  was ambiguous once STORY-206 was named two words later — a reader could not tell whether "this
  story" meant STORY-206 or the article's own subject. Reworded to state the Fact directly (this
  placement is governed by `core-independence` alone) rather than via a story reference. The same
  rework also fixed the maintenance-note referent and attribution above `pyproject.toml`'s
  `inbound-adapters-dont-persist` contract (a `code_ref` of this article) — comment-only, no
  contract structure changed. verified_sha bumped `a192e17` -> `c34e193` (the `pyproject.toml`
  comment-fix commit) to reflect that `code_ref` moving; the sweep would otherwise flag this
  article STALE against it.
- sprint-69 (STORY-206, QM-5 fix / wiki sweep at resume 2026-08-12): the sweep flagged this
  article STALE a third time — `pyproject.toml` (a `code_ref`) moved at `13bbb07`. The change there
  is a comment-only rewrite of the `[tool.importlinter]` header (module-form invocation + a
  `sys.path` warning — see [[architecture-boundary]]); no dependency, no `[project]` table and no
  contract structure was altered, and this article's Facts touch none of it. This article cites
  `pyproject.toml` for dependency/config concerns and for the contract governing composition-zone
  placement; both are unchanged. Re-verified only. verified_sha bumped `c34e193` -> `13bbb07`.
- sprint-70 (STORY-219, citation fix): the "Seven surviving readers of `app.signals`" Fact's two
  remaining known-real drifts (flagged at this story's filing, deliberately not fixed by STORY-215's
  round so it would not be half-done) are corrected: `backend/src/composition/seed_dynamo.py:56` ->
  `:60` and `backend/src/composition/vendor_health.py:97` -> `:106` (both drifted under STORY-204/
  STORY-205, before sprint 68 opened). **Both citations reported OK before this fix and report OK
  after it** — `tools/citation_sweep.py`'s line-count-only check (no excerpt anchor at either site)
  only verifies the cited file is long enough to contain the line, and 56/97 were already within
  `seed_dynamo.py`'s 72 lines / `vendor_health.py`'s 142 lines — so this fix moves
  `tools/citation_gate.py`'s enforced-failure count for this article by **zero** (STORY-219's own
  AC7: fixing a wrong-but-in-range line cannot lower a baseline that never counted it as a failure).
  The two lines are now the REAL loop lines (`for sig in app.signals:` / `for signal in
  app.signals:`) rather than a stale approximation of them. This article's one genuine citation
  failure, `` `dispatch.py:44` `` (a bare filename, unrelated to either fix), is untouched and stays
  advisory-only under STORY-219's enforcement (it carries no `/`, so it is never ratcheted). Every
  other Fact was re-read against `backend/src/composition/config.py`; none has moved since `13bbb07`.
- sprint-73 (STORY-147): `ComponentConfig` gains two optional fields, `group` and
  `description` — `group` free-text, normalized to a lowercase slug by the model's own
  `field_validator` (`ComponentConfig::_normalize_group_case`); `description` capped at 80
  characters. A fifth `ConfigError` subclass, `InvalidComponentFieldError`, joins the
  STORY-146 four, checked in `load_config` for the same reason the other four are (a
  pydantic validator cannot raise a subclass that survives the caller). Neither field
  reaches Statuspage — `statuspage_mapping()` and the publish payload
  (`backend/src/adapters/outbound/statuspage/__init__.py:54`) are unaffected, pinned by a new
  regression test. **Re-keyed one "Seven surviving readers" citation while here**:
  `backend/src/composition/seed_dynamo.py`'s component-seeding `update_item` call grew by
  16 lines (the new `group`/`description` `ExpressionAttributeNames`/`Values` entries),
  shifting `for sig in app.signals:` from line 60 to line 76 — corrected above. No other
  Fact in this article changed; `AppConfig`/`Config`/`load_config`'s existing behaviour for
  every pre-existing field is untouched (proven by the full pre-existing `test_config.py`
  suite passing unmodified).
