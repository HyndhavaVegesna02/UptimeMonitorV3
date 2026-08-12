"""ZR-5 standing guard (STORY-209), part 1/2 -- resolution parity (AC1).

Cites `docs/scrum/wiki/zone-rules.md` ZR-5's Statement: the two composition
roots that can each build a live, vendor-credentialed publisher --
`composition/run.py::main` (the loop) and `composition/app.py::create_app`
(the API's approve trigger) -- must resolve `CONFIG_DIR` identically. Both
route through exactly one shared function, `composition/settings.py::
load_settings`, so pinning THAT function's behaviour pins the shared
mechanism both roots depend on.

This half only: `load_settings().config_dir` resolves to whatever `CONFIG_DIR`
is set to (an arbitrary value, not just the one either root's default config
happens to point at today), and defaults to `"config/apps"` when unset
(`composition/settings.py:46`).

The AC2 source-level (AST) guard -- that NEITHER root reads the `CONFIG_DIR`
env var directly, bypassing this function -- plus the full ZR-5 limits this
guard's docstring must carry (AC3) land in the next commit, in this same
file.
"""

from __future__ import annotations

from src.composition.settings import CONFIG_DIR_VAR, load_settings


def test_load_settings_config_dir_resolves_to_patched_value(monkeypatch) -> None:
    """AC1 -- both roots call this ONE function; pin that it actually honours
    whatever CONFIG_DIR is set to, arbitrarily -- not just the one value
    either root's default config happens to point at today."""
    monkeypatch.setenv(CONFIG_DIR_VAR, "some/arbitrary/config/path")

    settings = load_settings()

    assert settings.config_dir == "some/arbitrary/config/path"


def test_load_settings_config_dir_defaults_to_config_apps_when_unset(
    monkeypatch,
) -> None:
    """AC1 -- with CONFIG_DIR unset, both roots' shared default is
    "config/apps" (`composition/settings.py:46`) -- pinned here so a future
    change to that default is a deliberate, visible edit to this test too."""
    monkeypatch.delenv(CONFIG_DIR_VAR, raising=False)

    settings = load_settings()

    assert settings.config_dir == "config/apps"
