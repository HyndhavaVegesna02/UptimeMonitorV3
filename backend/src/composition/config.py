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
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, model_validator

from src.core.services.pipeline import AntiFlapThresholds

# ---------------------------------------------------------------------------
# Named resolver errors (dossier §7; named, not leaked KeyError)
# ---------------------------------------------------------------------------

_SECTION_10_DEFAULTS = AntiFlapThresholds(major=5, partial=3, degraded=2, recovery=2)


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


# ---------------------------------------------------------------------------
# Config models (frozen pydantic; model_validator enforces invariants)
# ---------------------------------------------------------------------------


class ComponentConfig(BaseModel):
    """A single component declared in an app's config file (dossier §7 Option C).

    ``id`` is the stable, globally-unique identifier used by both the pipeline
    resolvers and the dashboard; ``name`` is the human-readable display label.
    """

    model_config = ConfigDict(frozen=True)

    id: str
    """Stable, globally-unique component identifier."""

    name: str
    """Human-readable display name."""

    statuspage_component_id: str | None = None
    """Statuspage component ID (optional mapping, dossier §6)."""


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

    interval_seconds: int
    """Expected cadence in seconds (positive int, > 0; dossier §8 / §10 window math)."""

    @model_validator(mode="after")
    def _require_positive_interval(self) -> "SignalConfig":
        """Enforce the interval_seconds > 0 frozen-type invariant (2026-06-26)."""
        if self.interval_seconds <= 0:
            raise ValueError(
                f"interval_seconds must be a positive integer (got {self.interval_seconds!r}). "
                "See dossier §8 and the 2026-06-26 frozen-type invariant agreement."
            )
        return self


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

    signals: list[SignalConfig]
    """Ordered list of signals (native monitors) declared in this app's config."""

    thresholds: AntiFlapThresholds = _SECTION_10_DEFAULTS
    """Per-app anti-flap thresholds (dossier §10).  Defaults to 5/3/2/2 when omitted."""

    @model_validator(mode="after")
    def _validate_referential_and_uniqueness(self) -> "AppConfig":
        """Enforce intra-app referential integrity and uniqueness invariants.

        Three rules (dossier §7 Option C):
        1. Every ``signal.component_id`` must reference a declared component.
        2. No duplicate ``signal_key`` within the app.
        3. No duplicate ``component.id`` within the app.
        4. All threshold fields must be positive integers (dossier §10).
        """
        component_ids = {c.id for c in self.components}

        # 3. Duplicate component.id
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

        # 1. Referential integrity: signal.component_id → declared component
        for sig in self.signals:
            if sig.component_id not in component_ids:
                raise ValueError(
                    f"Signal {sig.signal_key!r} references component_id "
                    f"{sig.component_id!r}, which is not declared in app {self.id!r}. "
                    "Declare the component first."
                )

        # 4. Threshold positivity (dossier §10 — thresholds must be positive ints)
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

        for app in apps:
            for sig in app.signals:
                self._signal_to_component[sig.signal_key] = sig.component_id
                self._signal_key_to_signal[sig.signal_key] = sig
            for comp in app.components:
                self._component_to_thresholds[comp.id] = app.thresholds

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
    - a ``signal.component_id`` referencing no declared component;
    - a duplicate ``signal_key`` or ``component.id`` within an app;
    - a non-positive threshold;
    - a duplicate ``signal_key`` or ``component.id`` ACROSS apps (ids are
      globally stable per dossier §7 Option C).

    An empty ``config_dir`` (no ``*.yaml`` files) returns an empty ``Config``.

    Dossier §7 (Option C / D6) / §10 / §4.
    """
    config_dir = Path(config_dir)
    yaml_files = sorted(config_dir.glob("*.yaml"))

    apps: list[AppConfig] = []
    global_signal_keys: dict[str, str] = {}  # signal_key → filename
    global_component_ids: dict[str, str] = {}  # component_id → filename

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
        # sub-entry construction (components/signals/thresholds) is INSIDE the
        # try too, so a malformed sub-entry also gets the filename-prefixed
        # error rather than a bare pydantic/TypeError.
        app_block: dict[str, Any] = raw.get("app", {})
        try:
            app_kwargs: dict[str, Any] = {
                "id": app_block.get("id"),
                "name": app_block.get("name"),
                "monitor_provider": app_block.get("monitor_provider"),
                "components": [
                    ComponentConfig(**c) for c in (raw.get("components") or [])
                ],
                "signals": [SignalConfig(**s) for s in (raw.get("signals") or [])],
            }
            if "thresholds" in raw and raw["thresholds"] is not None:
                app_kwargs["thresholds"] = AntiFlapThresholds(**raw["thresholds"])
            app = AppConfig(**app_kwargs)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid config in {yaml_path.name}: {exc}") from exc

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

        apps.append(app)

    return Config(apps)
