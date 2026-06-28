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
    def test_signal_referencing_undeclared_component_raises(self):
        bad_signal = SignalConfig(
            signal_key="orphan-http",
            native_id="SYNTHETIC_TEST-XYZ",
            name="Orphan",
            component_id="does-not-exist",
            interval_seconds=60,
        )
        with pytest.raises(ValueError, match="component_id"):
            _valid_app(signals=[bad_signal])

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

    def test_signal_referencing_undeclared_component_raises_at_load(
        self, tmp_config_dir: Path
    ):
        _write_yaml(
            tmp_config_dir,
            "bad.yaml",
            """\
app:
  id: bad-app
  name: Bad App
  monitor_provider: dynatrace
components:
  - { id: checkout, name: Checkout }
signals:
  - { signal_key: orphan-http, native_id: SYNTHETIC_TEST-X, name: Orphan, component_id: does-not-exist, interval_seconds: 60 }
""",
        )
        with pytest.raises(Exception, match="component_id"):
            load_config(tmp_config_dir)

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
