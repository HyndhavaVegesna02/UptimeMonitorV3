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
    FlatSignalsRejectedError,
    SignalConfig,
    UnknownComponentError,
    UnknownSignalError,
    load_config,
)
from src.core.services.pipeline import AntiFlapThresholds

# ---------------------------------------------------------------------------
# Phase B — config model construction and validation
# ---------------------------------------------------------------------------

_VALID_COMPONENTS = [
    ComponentConfig(id="checkout", name="Checkout"),
    ComponentConfig(id="catalogue", name="Catalogue"),
]

_VALID_SIGNALS = [
    SignalConfig(
        signal_key="checkout-http",
        native_id="SYNTHETIC_TEST-ABC",
        name="Checkout HTTP",
        component_id="checkout",
        interval_seconds=60,
    ),
    SignalConfig(
        signal_key="catalogue-http",
        native_id="SYNTHETIC_TEST-DEF",
        name="Catalogue HTTP",
        component_id="catalogue",
        interval_seconds=60,
    ),
]

_DEFAULT_THRESHOLDS = AntiFlapThresholds(major=5, partial=3, degraded=2, recovery=2)


def _valid_app(**overrides) -> AppConfig:
    """Return a minimal valid AppConfig; override individual fields to probe rules."""
    defaults = dict(
        id="sockshop",
        name="Sock Shop",
        monitor_provider="dynatrace",
        components=list(_VALID_COMPONENTS),
        signals=list(_VALID_SIGNALS),
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
            signals=list(_VALID_SIGNALS),
        )
        assert app.thresholds == AntiFlapThresholds(
            major=5, partial=3, degraded=2, recovery=2
        )

    def test_app_with_no_signals_is_valid(self):
        """An app may declare zero signals (edge case — tested per working agreements)."""
        app = AppConfig(
            id="empty-app",
            name="Empty App",
            monitor_provider="dynatrace",
            components=list(_VALID_COMPONENTS),
            signals=[],
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
        dup = SignalConfig(
            signal_key="checkout-http",  # duplicate
            native_id="SYNTHETIC_TEST-DUP",
            name="Dup Signal",
            component_id="checkout",
            interval_seconds=60,
        )
        with pytest.raises(ValueError, match="signal_key"):
            _valid_app(signals=[*_VALID_SIGNALS, dup])

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
                signals=[],
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
  - { id: checkout, name: Checkout }
  - { id: catalogue, name: Catalogue }
signals:
  - { signal_key: checkout-http, native_id: SYNTHETIC_TEST-ABC, name: Checkout HTTP, component_id: checkout, interval_seconds: 60 }
  - { signal_key: catalogue-http, native_id: SYNTHETIC_TEST-DEF, name: Catalogue HTTP, component_id: catalogue, interval_seconds: 60 }
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
  - { id: frontend, name: Frontend }
signals:
  - { signal_key: frontend-http, native_id: SYNTHETIC_TEST-FE, name: Frontend HTTP, component_id: frontend, interval_seconds: 60 }
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
  - { id: some-component, name: Some Component }
signals:
  - { signal_key: checkout-http, native_id: SYNTHETIC_TEST-DUP, name: Dup, component_id: some-component, interval_seconds: 60 }
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
signals: []
"""
        _write_yaml(tmp_config_dir, "another.yaml", dup_yaml)
        with pytest.raises(ValueError, match="component.*id"):
            load_config(tmp_config_dir)


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
  - { id: frontend, name: Frontend }
signals:
  - { signal_key: frontend-http, native_id: SYNTHETIC_TEST-FE, name: Frontend HTTP, component_id: frontend, interval_seconds: 60 }
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
                signals=[],
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


class TestNestedMonitors:
    """AC1: monitors nest under their component; ownership is structural."""

    def test_nested_monitor_resolved_component_id_is_parent(
        self, tmp_config_dir: Path
    ):
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
        with pytest.raises(ValueError):
            _valid_app(signals=[bad_signal])
