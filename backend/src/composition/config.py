"""Config layer — per-app YAML config models, fail-fast loader, and in-memory resolvers.

Implements dossier §7 Option C / decision D6: config owns the signal→component
mapping, one Git-versioned file per app under ``config/apps/*.yaml``.  The per-app
anti-flap thresholds come from §10 (defaults: major=5 / partial=3 / degraded=2 /
recovery=2).  Loading and resolving config is a *composition-zone* concern (dossier
§4) — this module lives under ``src.composition`` and may import ``src.core`` types
(``AntiFlapThresholds``); the core never imports from here.

Public surface:
- ``ComponentConfig``, ``SignalConfig``, ``AppConfig`` — frozen pydantic models.
- ``Config`` — aggregate of ``AppConfig`` instances with two in-memory resolvers.
- ``load_config(config_dir)`` — reads ``config_dir/*.yaml``, validates, returns ``Config``.
- ``UnknownSignalError`` / ``UnknownComponentError`` — named domain errors raised by resolvers.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any

import yaml
from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator

from src.core.services.pipeline import AntiFlapThresholds

# ---------------------------------------------------------------------------
# Named resolver errors (dossier §7; named, not leaked KeyError)
# ---------------------------------------------------------------------------

_SECTION_10_DEFAULTS = AntiFlapThresholds(major=5, partial=3, degraded=2, recovery=2)


def _require_positive_interval(value: int) -> int:
    """Enforce the ``interval_seconds > 0`` frozen-type invariant (2026-06-26).

    Shared by ``MonitorConfig.interval_seconds`` and
    ``SignalConfig.interval_seconds`` (quality rework, 2026-07-29 — the two
    were previously byte-identical `model_validator(mode="after")` methods,
    one per model) via the ``PositiveIntervalSeconds`` annotated type below.
    """
    if value <= 0:
        raise ValueError(
            f"interval_seconds must be a positive integer (got {value!r}). "
            "See dossier §8 and the 2026-06-26 frozen-type invariant agreement."
        )
    return value


PositiveIntervalSeconds = Annotated[int, AfterValidator(_require_positive_interval)]
"""Shared field type for ``interval_seconds`` on ``MonitorConfig``/``SignalConfig``."""


class UnknownSignalError(ValueError):
    """Raised by ``Config.component_for_signal`` when ``signal_key`` is not registered.

    Inherits from ``ValueError`` (following the codebase convention — see
    ``ProposalNotFoundError``).  Named specifically so callers catch
    ``UnknownSignalError``, never a raw ``KeyError`` leak (dossier §7).
    """


class UnknownComponentError(ValueError):
    """Raised by ``Config.thresholds_for`` when ``component_id`` is not registered.

    Inherits from ``ValueError`` (following the codebase convention — see
    ``ProposalNotFoundError``).  Named specifically so callers catch
    ``UnknownComponentError``, never a raw ``KeyError`` leak (dossier §7).
    """


class UnknownAppError(ValueError):
    """Raised by ``Config.locations_for``/``Config.freshness_for`` when
    ``app_id`` is not registered.

    Follows the ``UnknownSignalError``/``UnknownComponentError`` precedent
    (STORY-146 AC6) — named, never a raw ``KeyError`` leak.
    """


# ---------------------------------------------------------------------------
# Config authoring errors (STORY-146 AC5) — raised by ``load_config`` OUTSIDE
# the generic ``except (TypeError, ValueError)`` block, so the named subclass
# survives to the caller.  Probed (twice, independently): a ``ValueError``
# subclass raised INSIDE a pydantic ``model_validator`` is converted to
# ``pydantic.ValidationError`` in both ``mode="before"`` and ``mode="after"``
# — losing the subclass — so these three classes are only guaranteed to
# survive when raised directly in ``load_config``'s own code, not from a
# validator.  (``FlatSignalsRejectedError`` is ALSO raised from the
# ``mode="before"`` derive validator on direct ``AppConfig(signals=…)``
# construction — AC2b — where it is expected to arrive as a wrapped
# ``ValidationError`` instead; that call site's job is "raise loudly", not
# "preserve the exact class".)
# ---------------------------------------------------------------------------


class ConfigError(ValueError):
    """Base class for config authoring errors surfaced by ``load_config``."""


class FlatSignalsRejectedError(ConfigError):
    """Raised when an app's config authors flat ``signals:`` directly instead
    of nesting monitors under their component (STORY-146 AC2).

    Two raise sites: ``load_config`` (a raw top-level ``signals:`` key in a
    YAML file) and ``AppConfig``'s ``mode="before"`` derive validator (an
    explicitly-supplied non-empty ``signals=`` on direct construction).
    """


class UndeclaredLocationAliasError(ConfigError):
    """Raised when a monitor's ``expected_locations`` names an alias that is
    not declared in the same app's ``locations:`` block (STORY-146 AC3/AC5).
    """


class InvalidFreshnessError(ConfigError):
    """Raised when an app's ``freshness:`` block has a non-positive
    ``stale_after_cycles`` or ``reentry_cycles`` (STORY-146 AC4/AC5).
    """


class DuplicateAppIdError(ConfigError):
    """Raised when two config files declare the same ``app.id`` (STORY-146
    quality rework F4, 2026-07-29).

    ``app.id`` is a ``Config``-level lookup key (``locations_for``/
    ``freshness_for``) as of this story, so a second file silently
    overwriting the first's index entries is a real data-loss hole, not
    just an author typo — the same class of bug the pre-existing
    ``signal_key``/``component.id`` global-uniqueness checks in
    ``load_config`` guard against.
    """


# ---------------------------------------------------------------------------
# Config models (frozen pydantic; model_validator enforces invariants)
# ---------------------------------------------------------------------------


class MonitorConfig(BaseModel):
    """A single monitor nested under its owning component (STORY-146 AC1).

    The word ``monitors`` is deliberate: what an operator configures is a
    monitor; what it produces is a signal.  ``monitors: [ { signal_key: … } ]``
    reads as "this monitor produces this signal" — the actual model, since one
    ``native_id`` is one vendor monitor, fanning out across locations
    (``adapters/inbound/dynatrace/query.py:86``, ``http_normalizer.py:4``).

    A monitor has **no** ``component_id`` field — ownership is structural
    (it is nested inside its parent ``ComponentConfig``).  ``AppConfig``'s
    ``mode="before"`` derive validator stamps the parent component's id onto
    the ``SignalConfig`` it synthesizes from this monitor (STORY-146 AC7).

    Deliberately NOT in scope: a ``kind:`` field.  ``native_kind`` is
    discovered from the vendor's ``event.type`` per row (``dispatch.py:44``);
    a declared field nothing reads would let config lie.
    """

    model_config = ConfigDict(frozen=True)

    signal_key: str
    """Canonical, globally-unique internal key for this monitor's signal."""

    native_id: str
    """Provider-native monitor identifier (e.g. Dynatrace SYNTHETIC_TEST-…)."""

    name: str
    """Human-readable display name."""

    interval_seconds: PositiveIntervalSeconds
    """Expected cadence in seconds (positive int, > 0; dossier §8 / §10 window math)."""

    expected_locations: list[str] = Field(default_factory=list)
    """Aliases (declared in the app's ``locations:`` block, STORY-146 AC3) this
    monitor is expected to report from.  Declaration only in this story —
    *consuming* it in the completeness denominator is a separate story."""


class ComponentConfig(BaseModel):
    """A single component declared in an app's config file (dossier §7 Option C).

    ``id`` is the stable, globally-unique identifier used by both the pipeline
    resolvers and the dashboard; ``name`` is the human-readable display label.
    ``monitors`` (STORY-146) is the nested-authoring list of ``MonitorConfig``
    entries this component owns; ``AppConfig`` derives its flat ``signals``
    from these at construction time.
    """

    model_config = ConfigDict(frozen=True)

    id: str
    """Stable, globally-unique component identifier."""

    name: str
    """Human-readable display name."""

    statuspage_component_id: str | None = None
    """Statuspage component ID (optional mapping, dossier §6)."""

    monitors: list[MonitorConfig] = Field(default_factory=list)
    """Monitors nested under this component (STORY-146 AC1)."""


class SignalConfig(BaseModel):
    """A single signal (native monitor) declared in an app's config file (dossier §7).

    Maps the three §7 arrows: ``native_id`` (provider key) → ``signal_key``
    (canonical internal key) → ``component_id`` (component this signal feeds).
    ``component_id`` MUST reference a component declared in the same ``AppConfig``;
    this is enforced by ``AppConfig``'s ``model_validator``.
    ``interval_seconds`` is the signal's expected cadence in seconds (positive int,
    frozen-type invariant > 0 — working-agreements.md 2026-06-26); consumed by the
    pipeline orchestrator (dossier §8 step 5) to size the observation window.
    """

    model_config = ConfigDict(frozen=True)

    signal_key: str
    """Canonical, globally-unique internal key for this signal."""

    native_id: str
    """Provider-native monitor identifier (e.g. Dynatrace SYNTHETIC_TEST-…)."""

    name: str
    """Human-readable display name."""

    component_id: str
    """The component this signal feeds; must be a declared component id."""

    interval_seconds: PositiveIntervalSeconds
    """Expected cadence in seconds (positive int, > 0; dossier §8 / §10 window math)."""


class LocationConfig(BaseModel):
    """A declared probe location alias (STORY-146 AC3).

    ``native_id`` matches the vendor's opaque
    ``dt.entity.synthetic_location`` value (e.g.
    ``SYNTHETIC_LOCATION-000000000000005C``); ``label`` is the
    operator-facing display name.  Declared once per app, keyed by a short,
    non-cloud-provider alias (e.g. ``loc-a``, ``mumbai``, ``dublin`` —
    deliberately NOT an AWS region name, so no reader mistakes a probe
    location for an AWS deployment region).
    """

    model_config = ConfigDict(frozen=True)

    native_id: str
    """The vendor's opaque location entity id."""

    label: str
    """Operator-facing display name for this location."""


class FreshnessConfig(BaseModel):
    """Per-app freshness thresholds for the component rollup (STORY-146 AC4).

    Both fields are CYCLE COUNTS, not seconds — each is multiplied by the
    owning monitor's own ``interval_seconds`` at the point of use
    (STORY-151/152 consume this; this story only loads, validates, and
    exposes the counts).

    Carries plain ``int`` fields with NO pydantic validator, deliberately —
    do NOT follow the ``PositiveIntervalSeconds`` (module-level
    ``_require_positive_interval``, shared by ``SignalConfig.interval_seconds``
    / ``MonitorConfig.interval_seconds``) precedent here. Positivity is
    checked in ``load_config`` (``InvalidFreshnessError``, AC5) instead,
    because a validator cannot raise a named error that survives to the
    caller (probed twice, independently — see the AC5 module comment above).
    """

    model_config = ConfigDict(frozen=True)

    stale_after_cycles: int = 3
    """Consecutive missed cycles before a signal is considered stale."""

    reentry_cycles: int = 2
    """Consecutive fresh cycles required before a stale signal re-enters."""


class AppConfig(BaseModel):
    """Per-app config: components, signals, and anti-flap thresholds (dossier §7/§10).

    Frozen.  ``model_validator`` enforces three referential/uniqueness invariants:
    (1) every ``signal.component_id`` references a declared component;
    (2) no duplicate ``signal_key`` within the app;
    (3) no duplicate ``component.id`` within the app.
    Threshold positivity is enforced here (validated > 0 on each field).

    Per dossier §4 this model lives in the composition zone — it imports
    ``AntiFlapThresholds`` from core, but core never imports it back.
    """

    model_config = ConfigDict(frozen=True)

    id: str
    """Stable, globally-unique app identifier."""

    name: str
    """Human-readable display name."""

    monitor_provider: str
    """The synthetic-monitor provider key (e.g. ``"dynatrace"``)."""

    components: list[ComponentConfig]
    """Ordered list of components declared in this app's config."""

    signals: list[SignalConfig] = Field(default_factory=list)
    """Ordered list of signals (native monitors), SYNTHESIZED from
    ``components[].monitors`` by ``_derive_signals_from_monitors`` (STORY-146
    AC7) — not authored directly.  Kept as an ``AppConfig`` attribute (not
    replaced by a ``Config``-level accessor) because every existing consumer
    reads ``app.signals`` off an ``AppConfig`` (``run.py:136``,
    ``seed_dynamo.py:56``, ``composition/vendor_health.py:97``,
    ``scripts/seed_topology.py:44``, plus three sites in this module)."""

    thresholds: AntiFlapThresholds = _SECTION_10_DEFAULTS
    """Per-app anti-flap thresholds (dossier §10).  Defaults to 5/3/2/2 when omitted."""

    locations: dict[str, LocationConfig] = Field(default_factory=dict)
    """Declared probe locations, keyed by alias (STORY-146 AC3/AC6). Per-app —
    no global merge; two apps may declare different aliases without conflict."""

    freshness: FreshnessConfig = Field(default_factory=FreshnessConfig)
    """Per-app freshness thresholds (STORY-146 AC4/AC6), defaulting to
    stale_after_cycles=3 / reentry_cycles=2 when omitted."""

    @model_validator(mode="before")
    @classmethod
    def _derive_signals_from_monitors(cls, data: Any) -> Any:
        """Synthesize ``signals`` from ``components[].monitors`` (STORY-146 AC2/AC7).

        Stamps each monitor's parent component id onto the ``SignalConfig``
        dict it derives, which is what keeps every surviving `app.signals`
        reader working unchanged (AC7) without a `component_id` field ever
        being authored on a monitor (AC1 — ownership is structural).

        Rejects an explicitly-supplied non-empty ``signals=`` rather than
        silently deriving over it (AC2b): an unconditional derive would
        silently discard a caller's explicit ``signals=[…]``, which is worse
        than the referential-integrity check this mechanism replaces — a
        bogus ``component_id`` would vanish instead of raising.

        Every call site in this codebase passes already-constructed
        ``ComponentConfig``/``MonitorConfig`` instances (``load_config``
        builds these explicitly before constructing ``AppConfig``, and every
        test constructs them directly) — there is no dict-shaped component or
        monitor entry to handle (2026-07-29, STORY-146 quality rework F1: the
        two defensive dict branches this helper used to fall back to were
        dead across the full 539-test suite; removed rather than kept
        untested — see the story History).
        """
        if not isinstance(data, dict):
            return data

        explicit_signals = data.get("signals")
        if explicit_signals:
            raise FlatSignalsRejectedError(
                "AppConfig.signals is derived from components[].monitors and "
                "can no longer be authored directly (STORY-146 AC2) — got an "
                f"explicit signals={explicit_signals!r}. Nest monitors under "
                "their component (`components[].monitors`) instead."
            )

        derived: list[dict[str, Any]] = []
        for comp in data.get("components") or []:
            for mon in comp.monitors:
                derived.append(
                    {
                        "signal_key": mon.signal_key,
                        "native_id": mon.native_id,
                        "name": mon.name,
                        "interval_seconds": mon.interval_seconds,
                        "component_id": comp.id,
                    }
                )

        data = dict(data)
        data["signals"] = derived
        return data

    @model_validator(mode="after")
    def _validate_uniqueness_and_thresholds(self) -> "AppConfig":
        """Enforce intra-app uniqueness invariants and threshold positivity.

        Three rules (dossier §7 Option C):
        1. No duplicate ``component.id`` within the app.
        2. No duplicate ``signal_key`` within the app.
        3. All threshold fields must be positive integers (dossier §10).

        STORY-146 AC2 DELETES the fourth rule this validator used to enforce —
        "every ``signal.component_id`` references a declared component" — because
        it is now structurally impossible to violate: ``signals`` is derived
        from ``components[].monitors`` (see ``_derive_signals_from_monitors``),
        so every derived signal's ``component_id`` is its parent's id by
        construction. A monitor can no longer author a bogus reference at all.
        """
        component_ids = {c.id for c in self.components}

        # 1. Duplicate component.id
        if len(component_ids) != len(self.components):
            seen: set[str] = set()
            for c in self.components:
                if c.id in seen:
                    raise ValueError(
                        f"Duplicate component id {c.id!r} in app {self.id!r}. "
                        "Each component.id must be unique within an app."
                    )
                seen.add(c.id)

        # 2. Duplicate signal_key
        seen_keys: set[str] = set()
        for sig in self.signals:
            if sig.signal_key in seen_keys:
                raise ValueError(
                    f"Duplicate signal_key {sig.signal_key!r} in app {self.id!r}. "
                    "Each signal_key must be unique within an app."
                )
            seen_keys.add(sig.signal_key)

        # 3. Threshold positivity (dossier §10 — thresholds must be positive ints)
        t = self.thresholds
        for field_name, value in [
            ("major", t.major),
            ("partial", t.partial),
            ("degraded", t.degraded),
            ("recovery", t.recovery),
        ]:
            if value <= 0:
                raise ValueError(
                    f"Threshold field {field_name!r} must be a positive integer "
                    f"(got {value}). See dossier §10."
                )

        return self


# ---------------------------------------------------------------------------
# Config aggregate + loader
# ---------------------------------------------------------------------------


class Config:
    """Aggregate of all loaded ``AppConfig`` instances, with in-memory resolvers.

    Built by ``load_config``; not directly constructable by callers.
    Builds two dict indexes at construction time for O(1) resolver lookups:

    - ``_signal_to_component``: ``signal_key → component_id``
    - ``_component_to_thresholds``: ``component_id → AntiFlapThresholds``

    These are what STORY-016a (pipeline orchestration) will consume.

    Dossier §7 / §10 / §4.
    """

    def __init__(self, apps: list[AppConfig]) -> None:
        self.apps: list[AppConfig] = apps

        # Build O(1) indexes
        self._signal_to_component: dict[str, str] = {}
        self._component_to_thresholds: dict[str, AntiFlapThresholds] = {}
        self._signal_key_to_signal: dict[str, SignalConfig] = {}
        self._app_id_to_locations: dict[str, dict[str, LocationConfig]] = {}
        self._app_id_to_freshness: dict[str, FreshnessConfig] = {}

        for app in apps:
            for sig in app.signals:
                self._signal_to_component[sig.signal_key] = sig.component_id
                self._signal_key_to_signal[sig.signal_key] = sig
            for comp in app.components:
                self._component_to_thresholds[comp.id] = app.thresholds
            self._app_id_to_locations[app.id] = app.locations
            self._app_id_to_freshness[app.id] = app.freshness

    def component_for_signal(self, signal_key: str) -> str:
        """Return the ``component_id`` that ``signal_key`` feeds (dossier §7).

        Raises ``UnknownSignalError`` (a named domain error, never a raw
        ``KeyError``) when ``signal_key`` is not registered in any loaded app.
        """
        try:
            return self._signal_to_component[signal_key]
        except KeyError:
            raise UnknownSignalError(
                f"Signal key {signal_key!r} is not registered in any loaded app config. "
                "Check config/apps/*.yaml for the correct signal_key."
            ) from None

    def thresholds_for(self, component_id: str) -> AntiFlapThresholds:
        """Return the ``AntiFlapThresholds`` for ``component_id`` (dossier §10).

        Returns the §10 defaults (major=5 / partial=3 / degraded=2 / recovery=2)
        when the app omitted the ``thresholds`` block (the default is baked in at
        ``AppConfig`` construction time, so the index always has a value).

        Raises ``UnknownComponentError`` (named, never a raw ``KeyError``) when
        ``component_id`` is not declared in any loaded app.
        """
        try:
            return self._component_to_thresholds[component_id]
        except KeyError:
            raise UnknownComponentError(
                f"Component id {component_id!r} is not registered in any loaded app config. "
                "Check config/apps/*.yaml for the correct component id."
            ) from None

    def signal(self, signal_key: str) -> SignalConfig:
        """Return the full ``SignalConfig`` for ``signal_key`` (dossier §7 / §8).

        Exposes ``interval_seconds`` (and the other §7 fields) to the pipeline
        orchestrator (dossier §8 step 5) without changing the existing resolver
        signatures. Raises ``UnknownSignalError`` when the key is not registered.
        """
        try:
            return self._signal_key_to_signal[signal_key]
        except KeyError:
            raise UnknownSignalError(
                f"Signal key {signal_key!r} is not registered in any loaded app config. "
                "Check config/apps/*.yaml for the correct signal_key."
            ) from None

    def locations_for(self, app_id: str) -> dict[str, LocationConfig]:
        """Return the declared ``locations:`` map for ``app_id`` (STORY-146 AC6).

        Per-app, no global merge — matches the ``thresholds_for`` precedent.
        Raises ``UnknownAppError`` (named, never a raw ``KeyError``) when
        ``app_id`` is not registered.
        """
        try:
            return self._app_id_to_locations[app_id]
        except KeyError:
            raise UnknownAppError(
                f"App id {app_id!r} is not registered in any loaded app config. "
                "Check config/apps/*.yaml for the correct app id."
            ) from None

    def freshness_for(self, app_id: str) -> FreshnessConfig:
        """Return the ``FreshnessConfig`` for ``app_id`` (STORY-146 AC4/AC6).

        Per-app, no global merge — matches the ``thresholds_for`` precedent.
        Raises ``UnknownAppError`` (named, never a raw ``KeyError``) when
        ``app_id`` is not registered.
        """
        try:
            return self._app_id_to_freshness[app_id]
        except KeyError:
            raise UnknownAppError(
                f"App id {app_id!r} is not registered in any loaded app config. "
                "Check config/apps/*.yaml for the correct app id."
            ) from None

    def statuspage_mapping(self) -> dict[str, str]:
        """Return a mapping of internal component IDs to Statuspage component IDs (dossier §6).

        Only includes components that declare a non-None ``statuspage_component_id``.
        """
        mapping = {}
        for app in self.apps:
            for comp in app.components:
                if comp.statuspage_component_id is not None:
                    mapping[comp.id] = comp.statuspage_component_id
        return mapping


def load_config(config_dir: str | Path) -> Config:
    """Read all ``*.yaml`` files in ``config_dir`` and return a validated ``Config``.

    Fail-fast: raises a clear, descriptive error on:
    - malformed YAML (``yaml.YAMLError`` propagates with file context);
    - a missing required field (pydantic ``ValidationError`` with field name);
    - a duplicate ``signal_key`` or ``component.id`` within an app;
    - a non-positive threshold;
    - a duplicate ``signal_key`` or ``component.id`` ACROSS apps (ids are
      globally stable per dossier §7 Option C);
    - a raw top-level ``signals:`` key (``FlatSignalsRejectedError``, STORY-146
      AC2 — monitors are authored nested under ``components[].monitors``);
    - a monitor's ``expected_locations`` naming an undeclared alias
      (``UndeclaredLocationAliasError``, STORY-146 AC3/AC5);
    - a non-positive ``freshness.stale_after_cycles``/``reentry_cycles``
      (``InvalidFreshnessError``, STORY-146 AC4/AC5);
    - a duplicate ``app.id`` ACROSS files (``DuplicateAppIdError``, STORY-146
      quality rework F4, 2026-07-29) — ``app.id`` is a ``Config``-level lookup
      key (``locations_for``/``freshness_for``), so a second file silently
      overwriting the first's index entries would otherwise discard the
      first file's ``locations``/``freshness`` with no error.

    The last four checks run OUTSIDE the ``except (TypeError, ValueError)``
    block below, so their named subclasses (all ``ConfigError``) survive to
    the caller — a pydantic ``model_validator`` cannot do this (probed twice,
    independently: it converts a raised ``ValueError`` subclass to
    ``ValidationError``, losing the subclass), which is why they live here
    instead of on a model.

    An empty ``config_dir`` (no ``*.yaml`` files) returns an empty ``Config``.

    Dossier §7 (Option C / D6) / §10 / §4.
    """
    config_dir = Path(config_dir)
    yaml_files = sorted(config_dir.glob("*.yaml"))

    apps: list[AppConfig] = []
    global_signal_keys: dict[str, str] = {}  # signal_key → filename
    global_component_ids: dict[str, str] = {}  # component_id → filename
    global_app_ids: dict[str, str] = {}  # app.id → filename

    for yaml_path in yaml_files:
        raw: Any
        try:
            raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            raise ValueError(f"Malformed YAML in {yaml_path.name}: {exc}") from exc

        if not isinstance(raw, dict):
            raise ValueError(
                f"Expected a YAML mapping at the top level of {yaml_path.name}, "
                f"got {type(raw).__name__!r}."
            )

        # Build AppConfig — pydantic validates intra-app invariants here. The
        # sub-entry construction (components/thresholds/locations/freshness) is
        # INSIDE the try too, so a malformed sub-entry also gets the
        # filename-prefixed error rather than a bare pydantic/TypeError.
        # NOTE: `signals` is deliberately NOT built from `raw.get("signals")`
        # here — AppConfig derives it from `components[].monitors` (AC2/AC7);
        # a raw top-level `signals:` key is rejected below, outside this try,
        # so `FlatSignalsRejectedError` survives instead of being converted to
        # a bare `ValueError` by the generic `except` clause.
        app_block: dict[str, Any] = raw.get("app", {})
        try:
            app_kwargs: dict[str, Any] = {
                "id": app_block.get("id"),
                "name": app_block.get("name"),
                "monitor_provider": app_block.get("monitor_provider"),
                "components": [
                    ComponentConfig(**c) for c in (raw.get("components") or [])
                ],
            }
            if "thresholds" in raw and raw["thresholds"] is not None:
                app_kwargs["thresholds"] = AntiFlapThresholds(**raw["thresholds"])
            if "locations" in raw and raw["locations"] is not None:
                app_kwargs["locations"] = {
                    alias: LocationConfig(**loc)
                    for alias, loc in raw["locations"].items()
                }
            if "freshness" in raw and raw["freshness"] is not None:
                app_kwargs["freshness"] = FreshnessConfig(**raw["freshness"])
            app = AppConfig(**app_kwargs)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid config in {yaml_path.name}: {exc}") from exc

        # --- STORY-146 AC5: named errors, raised OUTSIDE the try/except above ---

        # AC2(a): a raw top-level `signals:` key is flat authoring — rejected
        # regardless of what load_config did with it (it was never fed to
        # AppConfig above).
        if "signals" in raw:
            raise FlatSignalsRejectedError(
                f"{yaml_path.name} declares a top-level `signals:` key; author "
                "monitors nested under components[].monitors instead "
                "(STORY-146 — see docs/scrum/wiki/config-layer.md)."
            )

        # AC3: every monitor's expected_locations must reference a declared
        # locations alias.
        declared_aliases = set(app.locations.keys())
        for comp in app.components:
            for mon in comp.monitors:
                for alias in mon.expected_locations:
                    if alias not in declared_aliases:
                        raise UndeclaredLocationAliasError(
                            f"{yaml_path.name}: monitor {mon.signal_key!r} "
                            f"(component {comp.id!r}) references "
                            f"expected_locations alias {alias!r}, which is not "
                            f"declared in this app's `locations:` block."
                        )

        # AC4: freshness cycle counts must be positive ints.
        if app.freshness.stale_after_cycles <= 0:
            raise InvalidFreshnessError(
                f"{yaml_path.name}: freshness.stale_after_cycles must be a "
                f"positive integer (got {app.freshness.stale_after_cycles!r})."
            )
        if app.freshness.reentry_cycles <= 0:
            raise InvalidFreshnessError(
                f"{yaml_path.name}: freshness.reentry_cycles must be a "
                f"positive integer (got {app.freshness.reentry_cycles!r})."
            )

        # Global uniqueness checks across apps (dossier §7 — ids are globally stable)
        for sig in app.signals:
            if sig.signal_key in global_signal_keys:
                raise ValueError(
                    f"Duplicate signal_key {sig.signal_key!r} found in "
                    f"{yaml_path.name!r} — already declared in "
                    f"{global_signal_keys[sig.signal_key]!r}. "
                    "signal_key must be globally unique across all apps."
                )
            global_signal_keys[sig.signal_key] = yaml_path.name

        for comp in app.components:
            if comp.id in global_component_ids:
                raise ValueError(
                    f"Duplicate component id {comp.id!r} found in "
                    f"{yaml_path.name!r} — already declared in "
                    f"{global_component_ids[comp.id]!r}. "
                    "component.id must be globally unique across all apps."
                )
            global_component_ids[comp.id] = yaml_path.name

        # Quality rework F4 (2026-07-29): a duplicate app.id across files
        # silently discards the first file's locations_for/freshness_for
        # values (app.id is now a Config-level lookup key) — reject it.
        if app.id in global_app_ids:
            raise DuplicateAppIdError(
                f"Duplicate app id {app.id!r} found in {yaml_path.name!r} — "
                f"already declared in {global_app_ids[app.id]!r}. "
                "app.id must be globally unique across all config files."
            )
        global_app_ids[app.id] = yaml_path.name

        apps.append(app)

    return Config(apps)
