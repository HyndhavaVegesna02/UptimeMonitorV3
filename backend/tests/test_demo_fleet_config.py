"""Tests for the demo fleet config directory (STORY-176 AC3, AC4, AC8).

`config/demo/` is a fictional fleet authored in STORY-146's nested shape —
never `config/apps/`, the LIVE config that must never be loaded alongside a
real Statuspage credential. Three things are proven here, together, because
none of them alone closes the exposure (STORY-176 AC3 History):

- AC3(a): the demo config declares NO `statuspage_component_id` on any
  component, so `Config.statuspage_mapping()` is empty and `build_publisher`
  (with real credentials present) falls through to a `LoggingPublisher`
  delegate — `publish_helper.py:211`.
- AC3(b): `CONFIG_DIR` governs `create_app()` on the API process exactly the
  way `composition/asgi.py` boots it (no `config_dir` argument) — asserted
  IN-PROCESS, never over HTTP (no v1 route exposes the mapping/publisher).
- AC3(c): the demo fleet's component ids are DISJOINT from `config/apps`'s —
  a real set intersection over both LOADED configs, not a hand-picked list —
  because `StatuspagePublisher` keys on the canonical component id
  (`adapters/outbound/statuspage/__init__.py:41-46`), so a collision on the
  API's DEFAULT `CONFIG_DIR` (`config/apps`, `settings.py:32`) would PATCH
  the real page.

AC4/AC8: the fleet's scale (>=12 components, >=40 signals, >=4 locations)
and the STORY-146 "duplicate app.id silently discards a file's
locations/freshness" trap — closed as of STORY-146 quality rework F4
(`config.py` now RAISES `DuplicateAppIdError` on a repeated `app.id` instead
of discarding, `config.py:715-721`) — are both proven by loading the real
three-file directory and reading every declared `locations`/`freshness`
block back per `app.id`.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from src.composition.config import load_config
from src.composition.publish_helper import LoggingPublisher, build_publisher
from tests.fakes import FakeClock, FakeComponentRepository, FakePublicationRepository

_REPO_ROOT = Path(__file__).resolve().parents[2]
DEMO_CONFIG_DIR = _REPO_ROOT / "config" / "demo"
LIVE_CONFIG_DIR = _REPO_ROOT / "config" / "apps"


def _demo_config():
    return load_config(DEMO_CONFIG_DIR)


# --- AC3(a): the demo config's own mapping is empty ------------------------


def test_demo_config_declares_no_statuspage_component_id_anywhere():
    cfg = _demo_config()
    for app in cfg.apps:
        for comp in app.components:
            assert comp.statuspage_component_id is None, (
                f"component {comp.id!r} in app {app.id!r} declares a "
                "statuspage_component_id — the demo fleet must declare NONE "
                "(STORY-176 AC3a)."
            )


def test_demo_config_statuspage_mapping_is_empty():
    cfg = _demo_config()
    assert cfg.statuspage_mapping() == {}


def test_build_publisher_with_demo_mapping_and_real_creds_falls_back_to_logging():
    """AC3(a), second half: even with NON-empty credentials present, the
    empty mapping from the demo config forces `build_publisher` to the
    `LoggingPublisher` fallback — the guard is a property of the config, not
    a promise about wiring (`publish_helper.py:211`)."""
    cfg = _demo_config()
    component_repo = FakeComponentRepository()
    publication_repo = FakePublicationRepository()
    clock = FakeClock(datetime(2026, 7, 30, tzinfo=timezone.utc))

    publisher = build_publisher(
        component_repo=component_repo,
        publication_repo=publication_repo,
        clock=clock,
        statuspage_page_id="REAL-LOOKING-PAGE-ID",
        statuspage_api_token="REAL-LOOKING-API-TOKEN",
        component_mapping=cfg.statuspage_mapping(),
    )

    assert isinstance(publisher._delegate, LoggingPublisher)


# --- AC3(c): demo ids disjoint from the LIVE config/apps ids ---------------


def test_demo_component_ids_are_disjoint_from_config_apps_component_ids():
    """AC3(c): a REAL set intersection over both loaded configs, not a
    hand-picked "known" id list — so this test can never come back empty by
    construction; it fails the moment either directory's ids drift."""
    demo_cfg = _demo_config()
    live_cfg = load_config(LIVE_CONFIG_DIR)

    demo_ids = {comp.id for app in demo_cfg.apps for comp in app.components}
    live_ids = {comp.id for app in live_cfg.apps for comp in app.components}

    assert demo_ids, "the demo fleet must declare at least one component"
    assert live_ids, "config/apps must declare at least one component"
    assert demo_ids & live_ids == set()


def test_disjointness_check_actually_catches_a_collision(tmp_path):
    """Reality check on the check itself (2026-07-29 retro A1: a check that
    can never fail is not a check): a config declaring the SAME component id
    as `config/apps` (`http-check`) IS caught by the intersection above."""
    colliding_yaml = """\
app:
  id: collision-app
  name: Collision App
  monitor_provider: dynatrace
components:
  - id: http-check
    name: Colliding HTTP Check
    monitors:
      - { signal_key: collision-http, native_id: HTTP_CHECK-COLLISION, name: Collision, interval_seconds: 30 }
"""
    (tmp_path / "collision.yaml").write_text(colliding_yaml, encoding="utf-8")

    colliding_cfg = load_config(tmp_path)
    live_cfg = load_config(LIVE_CONFIG_DIR)

    colliding_ids = {comp.id for app in colliding_cfg.apps for comp in app.components}
    live_ids = {comp.id for app in live_cfg.apps for comp in app.components}

    assert colliding_ids & live_ids == {"http-check"}


# --- AC3(b): in-process, exactly what the API boots (no config_dir arg) ----

# sprint-63 fix round, quality finding S2: this is the CONFIG_DIR-governs-
# create_app half of the publish-safety proof -- the one test in this story
# that must never silently vanish. It was previously Docker-gated via the
# `dynamo_local` fixture (session-scoped, SKIPS the whole test when Docker is
# unavailable and no DYNAMO_ENDPOINT_URL is set), even though `create_app()`
# makes no actual DynamoDB I/O before any assertion here runs: `make_dynamo_
# resource` (`composition/dynamo.py`) is a bare `boto3.resource(...)` call,
# and `.Table(name)` (used by the Dynamo*Repository constructors) is lazy --
# neither opens a connection. A literal, deliberately-unreachable endpoint
# URL is therefore sufficient and lets this test run with NO Docker
# dependency at all.
_NO_IO_DYNAMO_ENDPOINT_URL = "http://127.0.0.1:1"


def test_create_app_with_demo_config_dir_yields_empty_mapping_and_logging_delegate(
    monkeypatch,
):
    """AC3(b): `CONFIG_DIR=config/demo` governs `create_app()` with NO
    `config_dir` argument — precisely how `composition/asgi.py` boots the
    real API process (`asgi.py` calls `create_app()` bare). No v1 route
    exposes the runtime mapping/publisher/config (14 routes enumerated at
    planning), so this is asserted in-process, never over HTTP. Un-gated from
    Docker (S2 above): `DYNAMO_ENDPOINT_URL` is a literal, unreachable URL --
    no I/O occurs before the assertions below run."""
    from src.composition.app import create_app
    from src.composition.publish_helper import StatusWritebackPublisher

    monkeypatch.setenv("DYNAMO_ENDPOINT_URL", _NO_IO_DYNAMO_ENDPOINT_URL)
    monkeypatch.setenv("CONFIG_DIR", str(DEMO_CONFIG_DIR))
    # Fake-but-present credentials — proves the guard holds even WITH
    # credentials, matching the real repo-root `.env` exposure this AC exists
    # to close.
    monkeypatch.setenv("STATUSPAGE_PAGE_ID", "REAL-LOOKING-PAGE-ID")
    monkeypatch.setenv("STATUSPAGE_API_KEY", "REAL-LOOKING-API-TOKEN")

    app = create_app()

    assert app.state.seed_config is not None
    assert app.state.seed_config.statuspage_mapping() == {}
    assert isinstance(app.state.publisher, StatusWritebackPublisher)
    assert isinstance(app.state.publisher._delegate, LoggingPublisher)


def test_create_app_with_live_config_dir_and_real_looking_creds_selects_real_publisher_type(
    dynamo_local, monkeypatch
):
    """The two-sided proof's UNSAFE side (sprint-63 plan, reality gate 176,
    point 2): `config/apps` DOES declare a `statuspage_component_id`
    (`httpcheck.yaml:8`), so the SAME in-process assertion, pointed at the
    live config dir, must select a REAL `StatuspagePublisher` type — proving
    the guard is a property of the CONFIG, not something that always no-ops.
    Asserts the TYPE only; makes no network call (StatuspagePublisher.publish
    is never invoked)."""
    from src.adapters.outbound.statuspage import StatuspagePublisher
    from src.composition.app import create_app
    from src.composition.publish_helper import (
        BestEffortPublisher,
        RecordingPublisher,
        StatusWritebackPublisher,
    )

    monkeypatch.setenv("DYNAMO_ENDPOINT_URL", dynamo_local.endpoint_url)
    monkeypatch.setenv("CONFIG_DIR", str(LIVE_CONFIG_DIR))
    monkeypatch.setenv("STATUSPAGE_PAGE_ID", "REAL-LOOKING-PAGE-ID")
    monkeypatch.setenv("STATUSPAGE_API_KEY", "REAL-LOOKING-API-TOKEN")

    app = create_app()

    assert app.state.seed_config.statuspage_mapping() != {}
    assert isinstance(app.state.publisher, StatusWritebackPublisher)
    best_effort = app.state.publisher._delegate
    assert isinstance(best_effort, BestEffortPublisher)
    recording = best_effort._delegate
    assert isinstance(recording, RecordingPublisher)
    assert isinstance(recording._delegate, StatuspagePublisher)


# --- AC4/AC8: fleet scale + per-app locations/freshness survival -----------


def test_demo_fleet_scale_meets_ac4_minimums():
    cfg = _demo_config()

    all_components = [comp for app in cfg.apps for comp in app.components]
    all_signals = [sig for app in cfg.apps for sig in app.signals]
    all_location_aliases: set[str] = set()
    for app in cfg.apps:
        all_location_aliases |= set(app.locations.keys())

    assert len(all_components) >= 12
    assert len(all_signals) >= 40
    assert len(all_location_aliases) >= 4


def test_demo_fleet_every_files_locations_and_freshness_survive_loading():
    """AC8 multi-file trap: each demo YAML declares a DISTINCT `app.id`
    (`config.py` now raises `DuplicateAppIdError` on a repeat, STORY-146 F4 —
    so a collision would fail LOADING, not silently discard). This asserts
    the POSITIVE case: every file's own `locations:`/`freshness:` block is
    retrievable, unchanged, via `Config.locations_for`/`freshness_for` keyed
    by that file's `app.id` — nothing merged, dropped, or overwritten."""
    cfg = _demo_config()

    assert len(cfg.apps) == 3
    app_ids = {app.id for app in cfg.apps}
    assert len(app_ids) == 3, "every demo YAML must declare a distinct app.id"

    for app in cfg.apps:
        assert cfg.locations_for(app.id) == app.locations
        assert len(cfg.locations_for(app.id)) >= 4
        assert cfg.freshness_for(app.id) == app.freshness


def test_demo_fleet_monitors_use_short_intervals():
    """AC2(d): demo monitors use short intervals (<= 60s) so a 5-cycle
    anti-flap ladder completes in minutes, not ~25."""
    cfg = _demo_config()
    for app in cfg.apps:
        for sig in app.signals:
            assert sig.interval_seconds <= 60, (
                f"signal {sig.signal_key!r} in app {app.id!r} has "
                f"interval_seconds={sig.interval_seconds}, exceeding the "
                "60s demo ceiling (STORY-176 AC2d)."
            )
