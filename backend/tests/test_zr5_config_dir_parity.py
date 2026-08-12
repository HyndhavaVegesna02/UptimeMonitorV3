"""ZR-5 standing guard (STORY-209): the two composition roots that can each
build a live, vendor-credentialed publisher -- `composition/run.py::main`
(the loop) and `composition/app.py::create_app` (the API's approve trigger)
-- resolve `CONFIG_DIR` identically.

Cites `docs/scrum/wiki/zone-rules.md` ZR-5's Statement and Coverage verdict,
which this test mechanises verbatim, in two halves:

- **AC1 -- resolution parity.** Both roots route through exactly one shared
  function, `composition/settings.py::load_settings`. Pinning THAT function's
  behaviour pins the shared mechanism both roots depend on:
  `load_settings().config_dir` resolves to whatever `CONFIG_DIR` is set to
  (an arbitrary value, not just the one either root's default config happens
  to point at today), and defaults to `"config/apps"` when unset
  (`composition/settings.py:46`).
- **AC2 -- neither root reads the env var itself.** A source-level (AST)
  walk over `run.py::main` and `app.py::create_app` only (not the whole
  module -- a sibling function reading `CONFIG_DIR` for an unrelated reason
  would not be this guard's business) that fails if either function contains
  a `CONFIG_DIR` string literal or a reference to the `CONFIG_DIR_VAR`
  constant name (the shape a rename to that constant's declaration would
  still be caught under), and asserts both actually call `load_settings()`
  rather than routing around it entirely.

**`create_app(config_dir=...)`'s named-parameter override is explicitly
permitted and is NOT what this guard forbids.** The guard's target is the ENV
VAR read, not the parameter: `config_dir` (lowercase, a local parameter name)
never matches the `CONFIG_DIR` literal or the `CONFIG_DIR_VAR` name this walk
looks for, so a caller passing `config_dir="config/demo"` explicitly --
`backend/tests/test_asgi.py:18` does exactly this, unconditionally, for every
test in that file -- trips nothing here.
`test_create_app_config_dir_parameter_override_is_not_flagged` below proves
this discrimination directly, against the real parameter, rather than just
asserting it in prose.

**AC3 -- BOTH of this guard's limits, stated plainly, not hidden:**

(a) **The operational half -- UNGUARDABLE here, by construction.** The actual
sprint-64 incident was NOT a code disagreement: the loop and the API run as
two SEPARATE OS processes, each reading its OWN environment. Setting
`CONFIG_DIR` in one process's env never propagates to the other's, and no
single-process test -- this module included -- can see across a process
boundary. The only thing that actually covers that half is
`tools/demo_loop_gate/harness.py` setting `config_dir=` explicitly on BOTH
child process environments, which is procedural discipline, not a code
invariant. **A green run of this module must never be read as "the
sprint-64 incident cannot recur" -- it cannot, on its own, prove that.**

(b) **The code-level residue -- undetected by this guard's AC2 half.** ZR-5's
Statement forbids TWO things: neither root may hardcode a different default,
OR read a different env var than the other. The AC2 walk below catches only
the second (a direct env-var read bypassing `load_settings()`). A root
rewritten to hardcode `load_config("config/apps")` -- discarding
`settings.config_dir` entirely while still calling `load_settings()` for its
OTHER fields (`aws_region`, the Dynamo table names, the endpoint URL) -- passes
AC2's walk cleanly, INCLUDING its `load_settings()`-was-called assertion,
because that assertion only checks the call happened, never that its
`config_dir` field was the value actually used. This walk has no way to see
"the RETURNED `config_dir` field was ignored". That half is NOT mechanised by
this guard, and it is not claimed to be, anywhere -- row, docstring, or
commit message.

**Shown RED by mutation (AC4, AC5) -- twice, once per root**, each reverted
immediately, `git diff` empty both times (recorded verbatim in the story
report, not repeated here): changing `app.py::create_app` to read
`os.environ.get("CONFIG_DIR", "config/apps")` directly instead of
`settings.config_dir` fails `test_create_app_does_not_read_config_dir_env_var_directly`
naming `app.py`; the identical change to `run.py::main` fails
`test_run_main_does_not_read_config_dir_env_var_directly` naming `run.py`. A
guard watching only one of the two roots would be the exact asymmetry ZR-5 is
about.
"""

from __future__ import annotations

import ast
from pathlib import Path

from src.composition.settings import CONFIG_DIR_VAR, load_settings

_REPO_ROOT = Path(__file__).resolve().parents[2]
_RUN_PY = _REPO_ROOT / "backend" / "src" / "composition" / "run.py"
_APP_PY = _REPO_ROOT / "backend" / "src" / "composition" / "app.py"

# The exact env-var NAME this guard forbids either root from reading
# directly. Kept as a literal here (not imported from settings.py) so the
# check is over the actual string both roots' env would key on -- the
# separate `CONFIG_DIR_VAR` name-reference check below is what catches a
# root that reads the constant by NAME instead of by its literal value.
_ENV_VAR_LITERAL = "CONFIG_DIR"
_ENV_VAR_CONSTANT_NAME = "CONFIG_DIR_VAR"


def _find_function(tree: ast.AST, name: str) -> ast.FunctionDef | ast.AsyncFunctionDef:
    """The first `FunctionDef`/`AsyncFunctionDef` node named `name` anywhere
    in `tree`. Raises loudly (never returns `None`) so a rename of `main` or
    `create_app` breaks this guard's collection, not silently skips it."""
    for node in ast.walk(tree):
        if (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == name
        ):
            return node
    raise AssertionError(f"function {name!r} not found while walking the module")


def _config_dir_env_reads(func_node: ast.AST) -> list[str]:
    """Every AST shape, inside `func_node` only, that reads the `CONFIG_DIR`
    env var directly (AC2): the string literal itself (however it reaches
    `os.environ`), and a reference to the `CONFIG_DIR_VAR` constant name."""
    hits: list[str] = []
    for node in ast.walk(func_node):
        if isinstance(node, ast.Constant) and node.value == _ENV_VAR_LITERAL:
            hits.append(f"literal {node.value!r} at line {node.lineno}")
        elif isinstance(node, ast.Name) and node.id == _ENV_VAR_CONSTANT_NAME:
            hits.append(f"{_ENV_VAR_CONSTANT_NAME} reference at line {node.lineno}")
    return hits


def _calls_load_settings(func_node: ast.AST) -> bool:
    """True if `func_node` contains a call to `load_settings()`, bare or
    attribute-qualified (AC2's "both reach config through load_settings()")."""
    for node in ast.walk(func_node):
        if isinstance(node, ast.Call):
            target = node.func
            if isinstance(target, ast.Name) and target.id == "load_settings":
                return True
            if isinstance(target, ast.Attribute) and target.attr == "load_settings":
                return True
    return False


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


def test_run_main_does_not_read_config_dir_env_var_directly() -> None:
    """AC2 -- `composition/run.py::main` resolves `config_dir` ONLY through
    `load_settings()`, never a parallel env read."""
    tree = ast.parse(_RUN_PY.read_text(encoding="utf-8"), filename=str(_RUN_PY))
    main_node = _find_function(tree, "main")

    hits = _config_dir_env_reads(main_node)
    assert not hits, (
        f"composition/run.py::main reads CONFIG_DIR directly, bypassing "
        f"load_settings(): {hits}"
    )
    assert _calls_load_settings(main_node), (
        "composition/run.py::main must resolve settings via load_settings()"
    )


def test_create_app_does_not_read_config_dir_env_var_directly() -> None:
    """AC2 -- `composition/app.py::create_app` resolves `config_dir` ONLY
    through `load_settings()`, never a parallel env read. Its `config_dir=`
    parameter override is a separate, permitted mechanism -- see
    `test_create_app_config_dir_parameter_override_is_not_flagged` below."""
    tree = ast.parse(_APP_PY.read_text(encoding="utf-8"), filename=str(_APP_PY))
    create_app_node = _find_function(tree, "create_app")

    hits = _config_dir_env_reads(create_app_node)
    assert not hits, (
        f"composition/app.py::create_app reads CONFIG_DIR directly, "
        f"bypassing load_settings(): {hits}"
    )
    assert _calls_load_settings(create_app_node), (
        "composition/app.py::create_app must resolve settings via load_settings()"
    )


def test_create_app_config_dir_parameter_override_is_not_flagged() -> None:
    """AC2's explicit permission, proven rather than merely asserted: the
    `config_dir=` KEYWORD PARAMETER on `create_app` (lowercase, a caller
    override -- `test_asgi.py:18` passes it explicitly) is a different name
    than the `CONFIG_DIR` env var this guard forbids reading directly, and
    must not trip the hit-list `test_create_app_does_not_read_config_dir_env_var_directly`
    asserts on. This test confirms the parameter genuinely exists (so the
    discrimination is real, not vacuous) and that it is not itself a hit."""
    tree = ast.parse(_APP_PY.read_text(encoding="utf-8"), filename=str(_APP_PY))
    create_app_node = _find_function(tree, "create_app")

    param_names = {a.arg for a in create_app_node.args.kwonlyargs}
    assert "config_dir" in param_names, (
        "expected create_app to keep its config_dir= override parameter -- "
        "if this fails, the discrimination this guard relies on no longer "
        "holds and this test itself needs re-deriving"
    )

    hits = _config_dir_env_reads(create_app_node)
    assert not hits, (
        f"the config_dir= parameter must not trip the CONFIG_DIR env-var guard: {hits}"
    )
