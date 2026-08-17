"""Tests for the composition-zone config layer (STORY-040a).

Covers the config models (Phase B), the fail-fast loader (Phase C),
and the in-memory resolvers (Phase D).

Spec refs: dossier §7 (Option C / D6 — per-app YAML config ownership),
§10 (anti-flap thresholds; defaults major=5/partial=3/degraded=2/recovery=2),
§4 (config loading is a composition concern, never core).
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
from src.composition.config import (
    AppConfig,
    ComponentConfig,
    Config,
    DuplicateAppIdError,
    FlatSignalsRejectedError,
    InvalidComponentFieldError,
    InvalidFreshnessError,
    MonitorConfig,
    SignalConfig,
    UndeclaredLocationAliasError,
    UnknownAppError,
    UnknownComponentError,
    UnknownSignalError,
    load_config,
)
from src.core.services.pipeline import AntiFlapThresholds

# ---------------------------------------------------------------------------
# Phase B — config model construction and validation
# ---------------------------------------------------------------------------

_VALID_COMPONENTS = [
    ComponentConfig(
        id="checkout",
        name="Checkout",
        monitors=[
            MonitorConfig(
                signal_key="checkout-http",
                native_id="SYNTHETIC_TEST-ABC",
                name="Checkout HTTP",
                interval_seconds=60,
            )
        ],
    ),
    ComponentConfig(
        id="catalogue",
        name="Catalogue",
        monitors=[
            MonitorConfig(
                signal_key="catalogue-http",
                native_id="SYNTHETIC_TEST-DEF",
                name="Catalogue HTTP",
                interval_seconds=60,
            )
        ],
    ),
]

_DEFAULT_THRESHOLDS = AntiFlapThresholds(major=5, partial=3, degraded=2, recovery=2)


def _valid_app(**overrides) -> AppConfig:
    """Return a minimal valid AppConfig; override individual fields to probe rules.

    STORY-146: no `signals=` default — `signals` is derived from
    `components[].monitors` (AC2/AC7); pass `components=` to vary the
    monitors under test.
    """
    defaults = dict(
        id="sockshop",
        name="Sock Shop",
        monitor_provider="dynatrace",
        components=list(_VALID_COMPONENTS),
        thresholds=_DEFAULT_THRESHOLDS,
    )
    defaults.update(overrides)
    return AppConfig(**defaults)


class TestAppConfigHappyPath:
    def test_valid_app_config_constructs(self):
        app = _valid_app()
        assert app.id == "sockshop"
        assert app.name == "Sock Shop"
        assert app.monitor_provider == "dynatrace"
        assert len(app.components) == 2
        assert len(app.signals) == 2
        assert app.thresholds == _DEFAULT_THRESHOLDS

    def test_frozen(self):
        app = _valid_app()
        with pytest.raises(ValueError):
            app.id = "changed"  # type: ignore[misc]

    def test_thresholds_default_to_section_10_values(self):
        """When thresholds is omitted the §10 defaults (5/3/2/2) apply."""
        app = AppConfig(
            id="sockshop",
            name="Sock Shop",
            monitor_provider="dynatrace",
            components=list(_VALID_COMPONENTS),
        )
        assert app.thresholds == AntiFlapThresholds(
            major=5, partial=3, degraded=2, recovery=2
        )

    def test_app_with_no_signals_is_valid(self):
        """An app may declare components with zero monitors — zero derived
        signals (edge case — tested per working agreements)."""
        app = AppConfig(
            id="empty-app",
            name="Empty App",
            monitor_provider="dynatrace",
            components=[
                ComponentConfig(id="checkout", name="Checkout"),
                ComponentConfig(id="catalogue", name="Catalogue"),
            ],
        )
        assert app.signals == []


class TestAppConfigValidationRejects:
    # STORY-146 AC2: the referential-integrity check this class used to test
    # (`test_signal_referencing_undeclared_component_raises` — a
    # `signal.component_id` referencing an undeclared component) is DELETED
    # along with `AppConfig._validate_referential_and_uniqueness`'s check #1.
    # It loses nothing: `signals` is no longer author-settable at all (a
    # monitor's `component_id` is now structural — AC1), so a bogus reference
    # is no longer expressible in the first place. See
    # `TestFlatSignalsRejected` for the compensating check.

    def test_duplicate_signal_key_within_app_raises(self):
        dup_component = ComponentConfig(
            id="checkout-dup-source",
            name="Checkout Duplicate Source",
            monitors=[
                MonitorConfig(
                    signal_key="checkout-http",  # duplicate
                    native_id="SYNTHETIC_TEST-DUP",
                    name="Dup Signal",
                    interval_seconds=60,
                )
            ],
        )
        with pytest.raises(ValueError, match="signal_key"):
            _valid_app(components=[*_VALID_COMPONENTS, dup_component])

    def test_duplicate_component_id_within_app_raises(self):
        dup = ComponentConfig(id="checkout", name="Checkout Copy")  # duplicate id
        with pytest.raises(ValueError, match="component.*id"):
            _valid_app(components=[*_VALID_COMPONENTS, dup])

    def test_non_positive_major_threshold_raises(self):
        bad_thresholds = AntiFlapThresholds(major=0, partial=3, degraded=2, recovery=2)
        with pytest.raises(ValueError, match="positive"):
            _valid_app(thresholds=bad_thresholds)

    def test_missing_required_field_raises(self):
        with pytest.raises((ValueError, TypeError)):
            AppConfig(  # type: ignore[call-arg]
                name="No ID",
                monitor_provider="dynatrace",
                components=[],
            )


# ---------------------------------------------------------------------------
# Phase C — loader + fail-fast validation
# ---------------------------------------------------------------------------


@pytest.fixture()
def tmp_config_dir(tmp_path: Path) -> Path:
    """A tmp directory wired as a config/apps/ directory."""
    apps_dir = tmp_path / "apps"
    apps_dir.mkdir()
    return apps_dir


def _write_yaml(directory: Path, filename: str, content: str) -> Path:
    path = directory / filename
    path.write_text(textwrap.dedent(content), encoding="utf-8")
    return path


SOCKSHOP_YAML = """\
app:
  id: sockshop
  name: Sock Shop
  monitor_provider: dynatrace
components:
  - id: checkout
    name: Checkout
    monitors:
      - { signal_key: checkout-http, native_id: SYNTHETIC_TEST-ABC, name: Checkout HTTP, interval_seconds: 60 }
  - id: catalogue
    name: Catalogue
    monitors:
      - { signal_key: catalogue-http, native_id: SYNTHETIC_TEST-DEF, name: Catalogue HTTP, interval_seconds: 60 }
thresholds: { major: 5, partial: 3, degraded: 2, recovery: 2 }
"""


class TestLoadConfigHappyPath:
    def test_loads_sockshop_yaml(self, tmp_config_dir: Path):
        _write_yaml(tmp_config_dir, "sockshop.yaml", SOCKSHOP_YAML)
        cfg = load_config(tmp_config_dir)
        assert len(cfg.apps) == 1
        assert cfg.apps[0].id == "sockshop"

    def test_empty_config_dir_returns_empty_config(self, tmp_config_dir: Path):
        cfg = load_config(tmp_config_dir)
        assert cfg.apps == []

    def test_loads_real_httpcheck_yaml(self):
        """load_config over the real config/apps/ (includes httpcheck.yaml) succeeds."""
        repo_root = Path(__file__).parent.parent.parent
        cfg = load_config(repo_root / "config" / "apps")
        ids = [a.id for a in cfg.apps]
        assert "httpcheck" in ids

    def test_loads_multiple_apps(self, tmp_config_dir: Path):
        _write_yaml(tmp_config_dir, "sockshop.yaml", SOCKSHOP_YAML)
        other_yaml = """\
app:
  id: other-app
  name: Other App
  monitor_provider: dynatrace
components:
  - id: frontend
    name: Frontend
    monitors:
      - { signal_key: frontend-http, native_id: SYNTHETIC_TEST-FE, name: Frontend HTTP, interval_seconds: 60 }
"""
        _write_yaml(tmp_config_dir, "other.yaml", other_yaml)
        cfg = load_config(tmp_config_dir)
        assert len(cfg.apps) == 2


class TestLoadConfigFailFast:
    def test_malformed_yaml_raises(self, tmp_config_dir: Path):
        _write_yaml(tmp_config_dir, "bad.yaml", "app: {id: [unclosed")
        with pytest.raises(ValueError):
            load_config(tmp_config_dir)

    def test_missing_required_field_raises(self, tmp_config_dir: Path):
        _write_yaml(
            tmp_config_dir,
            "bad.yaml",
            """\
app:
  name: No ID
  monitor_provider: dynatrace
components: []
signals: []
""",
        )
        with pytest.raises(ValueError):
            load_config(tmp_config_dir)

    # STORY-146 AC2: `test_signal_referencing_undeclared_component_raises_at_load`
    # is DELETED along with the referential-integrity check it exercised — a
    # flat `signals:` YAML block (which is what carried the bogus
    # `component_id`) is now rejected outright by `TestFlatSignalsRejected`
    # below, before any referential check could even run.

    def test_duplicate_signal_key_across_apps_raises(self, tmp_config_dir: Path):
        _write_yaml(tmp_config_dir, "sockshop.yaml", SOCKSHOP_YAML)
        dup_yaml = """\
app:
  id: another-app
  name: Another App
  monitor_provider: dynatrace
components:
  - id: some-component
    name: Some Component
    monitors:
      - { signal_key: checkout-http, native_id: SYNTHETIC_TEST-DUP, name: Dup, interval_seconds: 60 }
"""
        _write_yaml(tmp_config_dir, "another.yaml", dup_yaml)
        with pytest.raises(ValueError, match="signal_key"):
            load_config(tmp_config_dir)

    def test_duplicate_component_id_across_apps_raises(self, tmp_config_dir: Path):
        _write_yaml(tmp_config_dir, "sockshop.yaml", SOCKSHOP_YAML)
        dup_yaml = """\
app:
  id: another-app
  name: Another App
  monitor_provider: dynatrace
components:
  - { id: checkout, name: Checkout Dup }
"""
        _write_yaml(tmp_config_dir, "another.yaml", dup_yaml)
        with pytest.raises(ValueError, match="component.*id"):
            load_config(tmp_config_dir)

    def test_duplicate_app_id_across_files_raises(self, tmp_config_dir: Path):
        """Quality rework F4 (2026-07-29): two files both declaring
        `app: {id: same-app}` (with distinct component ids and signal keys,
        so every OTHER global check passes) must be rejected — before this
        check, `load_config` would load both silently and `freshness_for`/
        `locations_for` would return only the SECOND file's values, with the
        first file's discarded with no error."""
        first_yaml = """\
app:
  id: same-app
  name: First File
  monitor_provider: dynatrace
components:
  - id: comp-first
    name: Comp First
    monitors:
      - { signal_key: sig-first, native_id: NATIVE-FIRST, name: First, interval_seconds: 60 }
"""
        second_yaml = """\
app:
  id: same-app
  name: Second File
  monitor_provider: dynatrace
components:
  - id: comp-second
    name: Comp Second
    monitors:
      - { signal_key: sig-second, native_id: NATIVE-SECOND, name: Second, interval_seconds: 60 }
"""
        _write_yaml(tmp_config_dir, "first.yaml", first_yaml)
        _write_yaml(tmp_config_dir, "second.yaml", second_yaml)
        with pytest.raises(DuplicateAppIdError) as exc_info:
            load_config(tmp_config_dir)
        message = str(exc_info.value)
        assert "first.yaml" in message
        assert "second.yaml" in message


# ---------------------------------------------------------------------------
# Phase D — resolvers
# ---------------------------------------------------------------------------


class TestResolvers:
    @pytest.fixture()
    def cfg(self, tmp_config_dir: Path) -> Config:
        _write_yaml(tmp_config_dir, "sockshop.yaml", SOCKSHOP_YAML)
        return load_config(tmp_config_dir)

    def test_component_for_known_signal(self, cfg: Config):
        assert cfg.component_for_signal("checkout-http") == "checkout"
        assert cfg.component_for_signal("catalogue-http") == "catalogue"

    def test_component_for_unknown_signal_raises_named_error(self, cfg: Config):
        with pytest.raises(UnknownSignalError):
            cfg.component_for_signal("nope")

    def test_unknown_signal_error_is_not_key_error(self, cfg: Config):
        # Must be the named error, not a raw KeyError
        with pytest.raises(UnknownSignalError) as exc_info:
            cfg.component_for_signal("ghost")
        assert type(exc_info.value) is not KeyError, (
            "component_for_signal leaked a raw KeyError; must raise UnknownSignalError"
        )

    def test_thresholds_for_known_component(self, cfg: Config):
        t = cfg.thresholds_for("checkout")
        assert t == AntiFlapThresholds(major=5, partial=3, degraded=2, recovery=2)

    def test_thresholds_for_unknown_component_raises_named_error(self, cfg: Config):
        with pytest.raises(UnknownComponentError):
            cfg.thresholds_for("nope")

    def test_unknown_component_error_is_not_key_error(self, cfg: Config):
        with pytest.raises(UnknownComponentError) as exc_info:
            cfg.thresholds_for("ghost")
        assert type(exc_info.value) is not KeyError, (
            "thresholds_for leaked a raw KeyError; must raise UnknownComponentError"
        )

    def test_thresholds_defaults_when_app_omits_thresholds(self, tmp_config_dir: Path):
        """§10 defaults (5/3/2/2) returned when the app YAML omits the thresholds block."""
        yaml_no_thresholds = """\
app:
  id: bare-app
  name: Bare App
  monitor_provider: dynatrace
components:
  - id: frontend
    name: Frontend
    monitors:
      - { signal_key: frontend-http, native_id: SYNTHETIC_TEST-FE, name: Frontend HTTP, interval_seconds: 60 }
"""
        _write_yaml(tmp_config_dir, "bare.yaml", yaml_no_thresholds)
        cfg = load_config(tmp_config_dir)
        t = cfg.thresholds_for("frontend")
        assert t == AntiFlapThresholds(major=5, partial=3, degraded=2, recovery=2)

    def test_empty_config_resolvers_raise_named_errors(self, tmp_config_dir: Path):
        """Both resolvers on an empty Config raise named errors, not KeyError."""
        cfg = load_config(tmp_config_dir)
        with pytest.raises(UnknownSignalError):
            cfg.component_for_signal("anything")
        with pytest.raises(UnknownComponentError):
            cfg.thresholds_for("anything")


# ---------------------------------------------------------------------------
# Phase A2 (STORY-016a) — SignalConfig.interval_seconds
# ---------------------------------------------------------------------------


class TestSignalConfigIntervalSeconds:
    """STORY-016a A2: interval_seconds field on SignalConfig (frozen-type invariant > 0)."""

    def test_signal_config_accepts_positive_interval_seconds(self):
        sig = SignalConfig(
            signal_key="checkout-http",
            native_id="SYNTHETIC_TEST-ABC",
            name="Checkout HTTP",
            component_id="checkout",
            interval_seconds=60,
        )
        assert sig.interval_seconds == 60

    def test_signal_config_zero_interval_raises(self):
        """interval_seconds=0 is non-positive and must be rejected (frozen-type invariant)."""
        with pytest.raises(ValueError, match="interval_seconds"):
            SignalConfig(
                signal_key="checkout-http",
                native_id="SYNTHETIC_TEST-ABC",
                name="Checkout HTTP",
                component_id="checkout",
                interval_seconds=0,
            )

    def test_signal_config_negative_interval_raises(self):
        """interval_seconds=-1 must be rejected (frozen-type invariant > 0)."""
        with pytest.raises(ValueError, match="interval_seconds"):
            SignalConfig(
                signal_key="checkout-http",
                native_id="SYNTHETIC_TEST-ABC",
                name="Checkout HTTP",
                component_id="checkout",
                interval_seconds=-1,
            )

    def test_config_signal_resolver_returns_interval_seconds(
        self, tmp_config_dir: Path
    ):
        """Config.signal(signal_key) returns the SignalConfig with interval_seconds."""
        _write_yaml(tmp_config_dir, "sockshop.yaml", SOCKSHOP_YAML)
        cfg = load_config(tmp_config_dir)
        sig = cfg.signal("checkout-http")
        assert sig.interval_seconds == 60

    def test_config_signal_resolver_unknown_key_raises(self, tmp_config_dir: Path):
        """Config.signal raises UnknownSignalError for an unregistered key."""
        _write_yaml(tmp_config_dir, "sockshop.yaml", SOCKSHOP_YAML)
        cfg = load_config(tmp_config_dir)
        with pytest.raises(UnknownSignalError):
            cfg.signal("does-not-exist")

    def test_real_httpcheck_yaml_has_interval_seconds(self):
        """The real config/apps/httpcheck.yaml has interval_seconds on every signal."""
        repo_root = Path(__file__).parent.parent.parent
        cfg = load_config(repo_root / "config" / "apps")
        httpcheck = next(a for a in cfg.apps if a.id == "httpcheck")
        for sig in httpcheck.signals:
            assert sig.interval_seconds > 0, (
                f"Signal {sig.signal_key!r} missing interval_seconds in httpcheck.yaml"
            )

    def test_config_statuspage_mapping(self):
        """Verify that statuspage_mapping returns a dict of id to statuspage_component_id, skipping None."""
        apps = [
            AppConfig(
                id="app-1",
                name="App 1",
                monitor_provider="dynatrace",
                components=[
                    ComponentConfig(
                        id="comp-1", name="Comp 1", statuspage_component_id="sp-1"
                    ),
                    ComponentConfig(
                        id="comp-2", name="Comp 2", statuspage_component_id=None
                    ),
                ],
            )
        ]
        cfg = Config(apps)
        assert cfg.statuspage_mapping() == {"comp-1": "sp-1"}

    def test_real_httpcheck_yaml_has_statuspage_mapping(self):
        """The real config/apps/httpcheck.yaml maps components to statuspage component IDs."""
        repo_root = Path(__file__).parent.parent.parent
        cfg = load_config(repo_root / "config" / "apps")
        mapping = cfg.statuspage_mapping()
        assert mapping == {"http-check": "xdnywbx77npw"}


# ---------------------------------------------------------------------------
# STORY-146 — nested monitors, declared locations, freshness block
# ---------------------------------------------------------------------------

NESTED_YAML = """\
app:
  id: nested-app
  name: Nested App
  monitor_provider: dynatrace
components:
  - id: web
    name: Web
    monitors:
      - { signal_key: web-http, native_id: NATIVE-WEB, name: Web HTTP, interval_seconds: 60 }
      - { signal_key: web-ping, native_id: NATIVE-WEB-PING, name: Web Ping, interval_seconds: 30 }
  - id: api
    name: API
    monitors:
      - { signal_key: api-http, native_id: NATIVE-API, name: API HTTP, interval_seconds: 45 }
"""


class TestMonitorConfigIntervalSeconds:
    """AC1: MonitorConfig.interval_seconds (frozen-type invariant > 0) — mirrors
    TestSignalConfigIntervalSeconds's zero/negative pair for its twin validator
    (quality rework F2, 2026-07-29)."""

    def test_monitor_config_zero_interval_raises(self):
        """interval_seconds=0 is non-positive and must be rejected (frozen-type invariant)."""
        with pytest.raises(ValueError, match="interval_seconds"):
            MonitorConfig(
                signal_key="checkout-http",
                native_id="SYNTHETIC_TEST-ABC",
                name="Checkout HTTP",
                interval_seconds=0,
            )

    def test_monitor_config_negative_interval_raises(self):
        """interval_seconds=-1 must be rejected (frozen-type invariant > 0)."""
        with pytest.raises(ValueError, match="interval_seconds"):
            MonitorConfig(
                signal_key="checkout-http",
                native_id="SYNTHETIC_TEST-ABC",
                name="Checkout HTTP",
                interval_seconds=-1,
            )


class TestNestedMonitors:
    """AC1: monitors nest under their component; ownership is structural."""

    def test_nested_monitor_resolved_component_id_is_parent(self, tmp_config_dir: Path):
        _write_yaml(tmp_config_dir, "nested.yaml", NESTED_YAML)
        cfg = load_config(tmp_config_dir)
        assert len(cfg.apps) == 1
        app = cfg.apps[0]
        by_key = {sig.signal_key: sig for sig in app.signals}
        assert by_key["web-http"].component_id == "web"
        assert by_key["web-ping"].component_id == "web"
        assert by_key["api-http"].component_id == "api"
        # Every signal's interval_seconds/native_id came from its monitor entry.
        assert by_key["web-http"].native_id == "NATIVE-WEB"
        assert by_key["web-http"].interval_seconds == 60
        assert by_key["api-http"].interval_seconds == 45


class TestFlatSignalsRejected:
    """AC2: flat `signals:` authoring is rejected at both levels."""

    def test_raw_top_level_signals_key_in_yaml_raises(self, tmp_config_dir: Path):
        flat_yaml = """\
app:
  id: flat-app
  name: Flat App
  monitor_provider: dynatrace
components:
  - { id: comp-a, name: Comp A }
signals:
  - { signal_key: sig-a, native_id: N-A, name: Sig A, component_id: comp-a, interval_seconds: 60 }
"""
        _write_yaml(tmp_config_dir, "flat.yaml", flat_yaml)
        with pytest.raises(FlatSignalsRejectedError):
            load_config(tmp_config_dir)

    def test_explicit_nonempty_signals_on_direct_construction_raises(self):
        """AC2b: the mode="before" derive validator raises rather than
        silently deriving over an explicit non-empty `signals=`. Pydantic
        wraps the raised `FlatSignalsRejectedError` as a `ValidationError`
        (probed, see AC5) — the important thing is that it raises LOUDLY,
        not that the exact subclass survives at this call site."""
        bad_signal = SignalConfig(
            signal_key="orphan-http",
            native_id="SYNTHETIC_TEST-XYZ",
            name="Orphan",
            component_id="does-not-exist",
            interval_seconds=60,
        )
        with pytest.raises(ValueError, match="derived from components"):
            _valid_app(signals=[bad_signal])


class TestDeclaredLocations:
    """AC3: a top-level `locations:` map, alias -> {native_id, label}."""

    def test_locations_map_loads(self, tmp_config_dir: Path):
        yaml_content = """\
app:
  id: loc-app
  name: Loc App
  monitor_provider: dynatrace
components:
  - id: web
    name: Web
    monitors:
      - { signal_key: web-http, native_id: N-WEB, name: Web HTTP, interval_seconds: 60 }
locations:
  loc-a: { native_id: SYNTHETIC_LOCATION-AAA, label: "Location A" }
  loc-b: { native_id: SYNTHETIC_LOCATION-BBB, label: "Location B" }
"""
        _write_yaml(tmp_config_dir, "loc.yaml", yaml_content)
        cfg = load_config(tmp_config_dir)
        app = cfg.apps[0]
        assert set(app.locations.keys()) == {"loc-a", "loc-b"}
        assert app.locations["loc-a"].native_id == "SYNTHETIC_LOCATION-AAA"
        assert app.locations["loc-a"].label == "Location A"

    def test_declared_expected_locations_alias_loads_successfully(
        self, tmp_config_dir: Path
    ):
        """AC3 happy path: a monitor's expected_locations naming a DECLARED
        alias loads successfully and resolves to the alias list unchanged.

        Quality rework F3 (2026-07-29): before this test, the only non-empty
        `expected_locations` anywhere in the suite was the failing `ghost-loc`
        case, so an implementation that rejected every alias (e.g. comparing
        against `set(loc.native_id for loc in app.locations.values())` instead
        of `set(app.locations.keys())`) would have passed all existing tests.
        """
        yaml_content = """\
app:
  id: loc-app
  name: Loc App
  monitor_provider: dynatrace
components:
  - id: web
    name: Web
    monitors:
      - { signal_key: web-http, native_id: N-WEB, name: Web HTTP, interval_seconds: 60, expected_locations: [loc-a] }
locations:
  loc-a: { native_id: SYNTHETIC_LOCATION-AAA, label: "Location A" }
"""
        _write_yaml(tmp_config_dir, "loc.yaml", yaml_content)
        cfg = load_config(tmp_config_dir)
        app = cfg.apps[0]
        mon = app.components[0].monitors[0]
        assert mon.expected_locations == ["loc-a"]

    def test_undeclared_expected_locations_alias_raises(self, tmp_config_dir: Path):
        yaml_content = """\
app:
  id: loc-app
  name: Loc App
  monitor_provider: dynatrace
components:
  - id: web
    name: Web
    monitors:
      - { signal_key: web-http, native_id: N-WEB, name: Web HTTP, interval_seconds: 60, expected_locations: [loc-a, ghost-loc] }
locations:
  loc-a: { native_id: SYNTHETIC_LOCATION-AAA, label: "Location A" }
"""
        _write_yaml(tmp_config_dir, "loc.yaml", yaml_content)
        with pytest.raises(UndeclaredLocationAliasError) as exc_info:
            load_config(tmp_config_dir)
        message = str(exc_info.value)
        assert "web-http" in message
        assert "ghost-loc" in message


class TestFreshnessBlock:
    """AC4: a top-level `freshness:` block, cycle counts, no multiplication."""

    def test_freshness_defaults_when_omitted(self, tmp_config_dir: Path):
        yaml_content = """\
app:
  id: bare-fresh-app
  name: Bare Fresh App
  monitor_provider: dynatrace
components:
  - { id: comp-a, name: Comp A }
"""
        _write_yaml(tmp_config_dir, "bare_fresh.yaml", yaml_content)
        cfg = load_config(tmp_config_dir)
        app = cfg.apps[0]
        assert app.freshness.stale_after_cycles == 3
        assert app.freshness.reentry_cycles == 2

    def test_freshness_explicit_values_load_as_plain_counts(self, tmp_config_dir: Path):
        yaml_content = """\
app:
  id: fresh-app
  name: Fresh App
  monitor_provider: dynatrace
components:
  - { id: comp-a, name: Comp A }
freshness: { stale_after_cycles: 5, reentry_cycles: 4 }
"""
        _write_yaml(tmp_config_dir, "fresh.yaml", yaml_content)
        cfg = load_config(tmp_config_dir)
        app = cfg.apps[0]
        # Plain counts — NO multiplication by interval_seconds anywhere here.
        assert app.freshness.stale_after_cycles == 5
        assert app.freshness.reentry_cycles == 4

    def test_zero_stale_after_cycles_raises_invalid_freshness_error(
        self, tmp_config_dir: Path
    ):
        yaml_content = """\
app:
  id: fresh-app
  name: Fresh App
  monitor_provider: dynatrace
components:
  - { id: comp-a, name: Comp A }
freshness: { stale_after_cycles: 0, reentry_cycles: 2 }
"""
        _write_yaml(tmp_config_dir, "fresh.yaml", yaml_content)
        with pytest.raises(InvalidFreshnessError):
            load_config(tmp_config_dir)

    def test_negative_reentry_cycles_raises_invalid_freshness_error(
        self, tmp_config_dir: Path
    ):
        yaml_content = """\
app:
  id: fresh-app
  name: Fresh App
  monitor_provider: dynatrace
components:
  - { id: comp-a, name: Comp A }
freshness: { stale_after_cycles: 3, reentry_cycles: -1 }
"""
        _write_yaml(tmp_config_dir, "fresh.yaml", yaml_content)
        with pytest.raises(InvalidFreshnessError):
            load_config(tmp_config_dir)


class TestLocationsAndFreshnessArePerApp:
    """AC6: locations/freshness are per-app; no global merge."""

    def test_two_apps_with_different_freshness_resolve_independently(
        self, tmp_config_dir: Path
    ):
        app_a_yaml = """\
app:
  id: app-a
  name: App A
  monitor_provider: dynatrace
components:
  - { id: comp-a, name: Comp A }
locations:
  loc-a: { native_id: SYNTHETIC_LOCATION-AAA, label: "Location A" }
freshness: { stale_after_cycles: 5, reentry_cycles: 3 }
"""
        app_b_yaml = """\
app:
  id: app-b
  name: App B
  monitor_provider: dynatrace
components:
  - { id: comp-b, name: Comp B }
locations:
  loc-b: { native_id: SYNTHETIC_LOCATION-BBB, label: "Location B" }
freshness: { stale_after_cycles: 10, reentry_cycles: 1 }
"""
        _write_yaml(tmp_config_dir, "app_a.yaml", app_a_yaml)
        _write_yaml(tmp_config_dir, "app_b.yaml", app_b_yaml)
        cfg = load_config(tmp_config_dir)

        assert cfg.freshness_for("app-a").stale_after_cycles == 5
        assert cfg.freshness_for("app-a").reentry_cycles == 3
        assert cfg.freshness_for("app-b").stale_after_cycles == 10
        assert cfg.freshness_for("app-b").reentry_cycles == 1

        assert set(cfg.locations_for("app-a").keys()) == {"loc-a"}
        assert set(cfg.locations_for("app-b").keys()) == {"loc-b"}
        # No global merge: app-a never sees app-b's alias and vice versa.
        assert "loc-b" not in cfg.locations_for("app-a")
        assert "loc-a" not in cfg.locations_for("app-b")

    def test_unknown_app_id_raises_named_error(self, tmp_config_dir: Path):
        yaml_content = """\
app:
  id: only-app
  name: Only App
  monitor_provider: dynatrace
components:
  - { id: comp-a, name: Comp A }
"""
        _write_yaml(tmp_config_dir, "only.yaml", yaml_content)
        cfg = load_config(tmp_config_dir)
        with pytest.raises(UnknownAppError):
            cfg.locations_for("does-not-exist")
        with pytest.raises(UnknownAppError):
            cfg.freshness_for("does-not-exist")


class TestRealHttpcheckYamlMigratedNestingOnly:
    """AC8: config/apps/httpcheck.yaml is migrated to the nested shape, and
    load_config yields byte-identical downstream values.

    The literals below were captured from the PRE-migration flat file
    (`components:`/`signals:` siblings joined by `component_id`) BEFORE it was
    edited to nest `monitors:` under `components:` — they are not recomputed
    from the new file, per AC8.
    """

    def test_migrated_config_yields_identical_downstream_values(self):
        repo_root = Path(__file__).parent.parent.parent
        cfg = load_config(repo_root / "config" / "apps")
        httpcheck = next(a for a in cfg.apps if a.id == "httpcheck")

        assert len(httpcheck.signals) == 1
        sig = httpcheck.signals[0]
        assert sig.signal_key == "http-check"
        assert sig.native_id == "HTTP_CHECK-38B092E93932C002"
        assert sig.interval_seconds == 120

        assert cfg.component_for_signal("http-check") == "http-check"
        assert cfg.thresholds_for("http-check") == AntiFlapThresholds(
            major=5, partial=3, degraded=2, recovery=2
        )
        assert cfg.statuspage_mapping() == {"http-check": "xdnywbx77npw"}

        # AC8: nesting ONLY — no locations:/expected_locations were added,
        # because real Dynatrace location ids/names cannot be verified while
        # the trial is expired.
        assert httpcheck.locations == {}
        for comp in httpcheck.components:
            for mon in comp.monitors:
                assert mon.expected_locations == []


# ---------------------------------------------------------------------------
# STORY-147 — component `group` + `description`
# ---------------------------------------------------------------------------


class TestComponentGroupAndDescription:
    """AC1/AC2: ComponentConfig.group/description — optional, normalized,
    validated OUTSIDE load_config's try/except (see the module-level AC5
    comment in config.py for why a pydantic validator cannot raise a
    subclass that survives to the caller)."""

    def test_group_and_description_default_to_none(self):
        comp = ComponentConfig(id="c1", name="C1")
        assert comp.group is None
        assert comp.description is None

    def test_group_is_lowercased_at_construction(self):
        """AC2: Commerce / COMMERCE / commerce all normalize to commerce —
        at the ComponentConfig construction level (the model owns
        normalization; load_config owns validation, per AC1)."""
        for raw in ("Commerce", "COMMERCE", "commerce"):
            comp = ComponentConfig(id="c1", name="C1", group=raw)
            assert comp.group == "commerce"

    def test_group_normalized_to_lowercase_at_load(self, tmp_config_dir: Path):
        """AC2 at the load_config level: a test asserts all three casings of
        the same word produce one value after loading real YAML."""
        yaml_content = """\
app:
  id: group-app
  name: Group App
  monitor_provider: dynatrace
components:
  - { id: c1, name: C1, group: Commerce }
  - { id: c2, name: C2, group: COMMERCE }
  - { id: c3, name: C3, group: commerce }
"""
        _write_yaml(tmp_config_dir, "group.yaml", yaml_content)
        cfg = load_config(tmp_config_dir)
        groups = {c.id: c.group for c in cfg.apps[0].components}
        assert groups == {"c1": "commerce", "c2": "commerce", "c3": "commerce"}

    def test_description_round_trips_when_valid(self, tmp_config_dir: Path):
        yaml_content = """\
app:
  id: desc-app
  name: Desc App
  monitor_provider: dynatrace
components:
  - { id: c1, name: C1, description: "Cart, payments and order placement" }
"""
        _write_yaml(tmp_config_dir, "desc.yaml", yaml_content)
        cfg = load_config(tmp_config_dir)
        assert (
            cfg.apps[0].components[0].description
            == "Cart, payments and order placement"
        )

    def test_empty_description_normalizes_to_none_at_construction(self):
        """STORY-226 AC3/AC5 — PO ruling 2026-08-16: `description: ""`
        normalizes to `None`, so one representation of "nothing" reaches
        the DTO. At the ComponentConfig construction level (mirrors
        `test_group_is_lowercased_at_construction`)."""
        comp = ComponentConfig(id="c1", name="C1", description="")
        assert comp.description is None

    def test_whitespace_only_description_normalizes_to_none_at_construction(self):
        """AC5: whitespace-only is decided the same way as empty — the rule
        implemented is `None if not v.strip() else v`, which treats
        `"   "` as empty without stripping any NON-empty value."""
        comp = ComponentConfig(id="c1", name="C1", description="   ")
        assert comp.description is None

    def test_non_empty_description_is_left_untouched_by_normalization(self):
        """AC5: the recommended rule (`None if not v.strip() else v`)
        leaves a non-empty value byte-identical — it does NOT strip
        leading/trailing whitespace off a real description, unlike
        `v.strip() or None`. Padding is preserved so the pinned 80-char
        boundary (`test_description_exactly_80_chars_is_valid`) is never
        moved by this normalization."""
        comp = ComponentConfig(id="c1", name="C1", description="  Cart  ")
        assert comp.description == "  Cart  "

    def test_empty_description_normalizes_to_none_at_load(self, tmp_config_dir: Path):
        """AC3: verified THROUGH load_config, not only on the model —
        a component declaring `description: ""` loads successfully and
        yields `description=None`, not `""`."""
        yaml_content = """\
app:
  id: empty-desc-app
  name: Empty Desc App
  monitor_provider: dynatrace
components:
  - { id: c1, name: C1, description: "" }
"""
        _write_yaml(tmp_config_dir, "empty_desc.yaml", yaml_content)
        cfg = load_config(tmp_config_dir)
        assert cfg.apps[0].components[0].description is None

    def test_whitespace_only_description_normalizes_to_none_at_load(
        self, tmp_config_dir: Path
    ):
        """AC3/AC5: `description: "   "` behaves the same as `""` at load."""
        yaml_content = """\
app:
  id: whitespace-desc-app
  name: Whitespace Desc App
  monitor_provider: dynatrace
components:
  - { id: c1, name: C1, description: "   " }
"""
        _write_yaml(tmp_config_dir, "whitespace_desc.yaml", yaml_content)
        cfg = load_config(tmp_config_dir)
        assert cfg.apps[0].components[0].description is None

    def test_group_empty_string_still_raises(self, tmp_config_dir: Path):
        """AC6 regression: `group: ""` stays an error — deliberately.

        The PO's ruling (2026-08-16) was scoped to `description`; `group`
        is a slug identifier used for grouping, and an empty slug is
        meaningless, so an error remains the right signal. This pins the
        current behaviour as a recorded decision, not a gap."""
        yaml_content = """\
app:
  id: empty-group-app
  name: Empty Group App
  monitor_provider: dynatrace
components:
  - { id: comp-a, name: Comp A, group: "" }
"""
        _write_yaml(tmp_config_dir, "empty_group.yaml", yaml_content)
        with pytest.raises(InvalidComponentFieldError) as exc_info:
            load_config(tmp_config_dir)
        assert type(exc_info.value) is InvalidComponentFieldError
        message = str(exc_info.value)
        assert "comp-a" in message
        assert "group" in message

    def test_group_not_slug_safe_after_normalization_raises(self, tmp_config_dir: Path):
        """AC1: a group that fails the slug pattern even after lowercasing
        (spaces/punctuation) raises InvalidComponentFieldError naming the
        component and the field — never a bare ValueError."""
        yaml_content = """\
app:
  id: bad-group-app
  name: Bad Group App
  monitor_provider: dynatrace
components:
  - { id: comp-a, name: Comp A, group: "Not Valid!" }
"""
        _write_yaml(tmp_config_dir, "bad_group.yaml", yaml_content)
        with pytest.raises(InvalidComponentFieldError) as exc_info:
            load_config(tmp_config_dir)
        assert type(exc_info.value) is InvalidComponentFieldError, (
            "load_config must raise the specific InvalidComponentFieldError "
            "class, not a bare ValueError (STORY-147 AC1)"
        )
        message = str(exc_info.value)
        assert "comp-a" in message
        assert "group" in message

    def test_group_error_message_contains_authored_and_normalized_value(
        self, tmp_config_dir: Path
    ):
        """STORY-226 AC1/AC2: the error must name the value the author
        actually typed, not only the normalized one — `comp.group` is
        already lowercased at construction (`field_validator("group",
        mode="after")`) by the time `load_config` raises, so the authored
        string must be carried separately (from `raw`, joined on
        `comp.id`). Given `group: "Not Valid!"`, the message must contain
        BOTH `Not Valid!` (authored) and `not valid!` (normalized).

        Shown RED against current behaviour (2026-08-17): today the
        message quotes only `comp.group`, which is already normalized, so
        this assertion fails before the AC1 fix lands.
        """
        yaml_content = """\
app:
  id: bad-group-app
  name: Bad Group App
  monitor_provider: dynatrace
components:
  - { id: comp-a, name: Comp A, group: "Not Valid!" }
"""
        _write_yaml(tmp_config_dir, "bad_group_authored.yaml", yaml_content)
        with pytest.raises(InvalidComponentFieldError) as exc_info:
            load_config(tmp_config_dir)
        message = str(exc_info.value)
        assert "Not Valid!" in message, (
            f"message must contain the AUTHORED value 'Not Valid!', got: {message!r}"
        )
        assert "not valid!" in message, (
            f"message must contain the NORMALIZED value 'not valid!', got: {message!r}"
        )

    def test_description_over_80_chars_raises_invalid_component_field_error(
        self, tmp_config_dir: Path
    ):
        long_desc = "x" * 81
        yaml_content = f"""\
app:
  id: bad-desc-app
  name: Bad Desc App
  monitor_provider: dynatrace
components:
  - {{ id: comp-a, name: Comp A, description: "{long_desc}" }}
"""
        _write_yaml(tmp_config_dir, "bad_desc.yaml", yaml_content)
        with pytest.raises(InvalidComponentFieldError) as exc_info:
            load_config(tmp_config_dir)
        assert type(exc_info.value) is InvalidComponentFieldError, (
            "load_config must raise the specific InvalidComponentFieldError "
            "class, not a bare ValueError (STORY-147 AC1)"
        )
        message = str(exc_info.value)
        assert "comp-a" in message
        assert "description" in message

    def test_description_exactly_80_chars_is_valid(self, tmp_config_dir: Path):
        """Boundary: 80 chars is the cap, not the first rejected length."""
        desc_80 = "x" * 80
        yaml_content = f"""\
app:
  id: boundary-desc-app
  name: Boundary Desc App
  monitor_provider: dynatrace
components:
  - {{ id: comp-a, name: Comp A, description: "{desc_80}" }}
"""
        _write_yaml(tmp_config_dir, "boundary_desc.yaml", yaml_content)
        cfg = load_config(tmp_config_dir)
        assert cfg.apps[0].components[0].description == desc_80

    def test_invalid_component_field_error_is_config_error(self):
        """InvalidComponentFieldError joins the ConfigError hierarchy
        STORY-146 landed (config.py:97-123), alongside its siblings."""
        from src.composition.config import ConfigError

        assert issubclass(InvalidComponentFieldError, ConfigError)

    def test_statuspage_mapping_unaffected_by_group_and_description(self):
        """AC4: group/description are internal-only operator-cockpit
        metadata — statuspage_mapping() stays exactly
        {component_id: statuspage_component_id}, byte-identical to before
        this story, even when a component declares both new fields."""
        apps = [
            AppConfig(
                id="app-1",
                name="App 1",
                monitor_provider="dynatrace",
                components=[
                    ComponentConfig(
                        id="comp-1",
                        name="Comp 1",
                        statuspage_component_id="sp-1",
                        group="commerce",
                        description="Cart, payments and order placement",
                    ),
                ],
            )
        ]
        cfg = Config(apps)
        assert cfg.statuspage_mapping() == {"comp-1": "sp-1"}
