"""Meta-test for API zone layout and import contract compliance.

Cites: Proposal (2026-07-10) §3.4 G4, §6.2, §10 Phase 1.
"""

import ast
import importlib
import tomllib
from pathlib import Path

import pytest
import src.api.v1


def discover_features(v1_dir: Path) -> set[str]:
    """Derive the API feature set from the package directories in v1.

    Excludes any directories starting with an underscore (e.g. _shared).
    Cites: Proposal (2026-07-10) §6.2, §10 Phase 1.
    """
    return {
        d.name for d in v1_dir.iterdir() if d.is_dir() and not d.name.startswith("_")
    }


#: ZR-4 (docs/scrum/wiki/zone-rules.md): the five files an api/v1 feature
#: divides into.
_FIVE_FILE_SHAPE = {
    "__init__.py",
    "controller.py",
    "models.py",
    "validation.py",
    "service.py",
}

#: ZR-4's one documented exception. `health` ships only `__init__.py` +
#: `controller.py` -- its own docstring
#: (backend/src/api/v1/health/controller.py) says why: a static liveness
#: stub with nothing to model, validate, or orchestrate, kept only to give
#: the `api-feature-independence` import-linter contract a second feature so
#: the contract is non-vacuous. This is a literal enumeration, never a
#: "fewer than five is fine" rule -- that would let silent drift through.
_FIVE_FILE_SHAPE_EXCEPTIONS = {"health"}


def assert_feature_five_file_shape(feature: str, feature_dir: Path) -> None:
    """Assert `feature_dir`'s Python-module set equals exactly the five-file
    shape (ZR-4), set equality rather than a superset check.

    Compares `*.py` files only. `__pycache__/` (and any other non-`.py`
    entry) exists in every feature directory on any machine that has already
    run the suite, so an unfiltered directory-entry comparison would be RED
    on a developer machine and GREEN in a clean CI checkout -- a guard whose
    colour depends on whether the suite has run before is worse than no
    guard.

    Cites: docs/scrum/wiki/zone-rules.md ZR-4.
    """
    actual_files = {p.name for p in feature_dir.iterdir() if p.suffix == ".py"}
    assert actual_files == _FIVE_FILE_SHAPE, (
        f"Feature '{feature}' does not match the five-file shape (ZR-4). "
        f"Expected: {_FIVE_FILE_SHAPE}, Actual: {actual_files}. "
        f"Difference: {_FIVE_FILE_SHAPE.symmetric_difference(actual_files)}"
    )


def assert_features_match(
    contract_features: set[str], filesystem_features: set[str]
) -> None:
    """Assert set equality between the contract list and filesystem features.

    Cites: Proposal (2026-07-10) §3.4 G4, §10 Phase 1.
    """
    if contract_features != filesystem_features:
        raise AssertionError(
            f"API zone layout mismatch. Contract features: {contract_features}, "
            f"Filesystem features: {filesystem_features}. "
            f"Difference: {contract_features.symmetric_difference(filesystem_features)}"
        )


def test_discover_features_excludes_underscores(tmp_path: Path) -> None:
    """Verify that underscore-prefixed directories are explicitly excluded.

    Cites: Proposal (2026-07-10) §6.2, §10 Phase 1.
    """
    (tmp_path / "decisions").mkdir()
    (tmp_path / "_shared").mkdir()
    (tmp_path / "health").mkdir()
    (tmp_path / "_another_private").mkdir()

    features = discover_features(tmp_path)
    assert features == {"decisions", "health"}
    assert "_shared" not in features
    assert "_another_private" not in features


def test_assert_features_match_validation() -> None:
    """Unit test for the assertion helper to prove it raises AssertionError on mismatch.

    Cites: Proposal (2026-07-10) §10 Phase 1 (Step 2: prove the guard).
    """
    # Mismatch scenarios
    with pytest.raises(AssertionError) as exc_info:
        assert_features_match({"health", "decisions"}, {"health"})
    assert "decisions" in str(exc_info.value)

    with pytest.raises(AssertionError) as exc_info:
        assert_features_match({"health"}, {"health", "decisions"})
    assert "decisions" in str(exc_info.value)

    # Match scenario should not raise
    assert_features_match({"health", "decisions"}, {"health", "decisions"})


def assert_router_routes_registered(
    feature_name: str, feature_router, openapi_paths: set[str]
) -> None:
    """Assert every route on `feature_router` is registered under
    `openapi_paths` (either trailing-slash form).

    Shared by the real drift check (`test_zone_layout_agreements`) and the
    meta-test that proves the check itself fails on an unmounted router
    (`test_zone_layout_detects_unmounted_router`) — extracted (Sprint 43
    review m4) so the meta-test exercises the SAME code path as the real
    check instead of a separate inline re-implementation that could drift
    out of sync with it and stop catching a real regression.

    Cites: STORY-077 MINOR-1; Sprint 43 review m4.
    """
    for child_route in feature_router.routes:
        prefix = getattr(feature_router, "prefix", "") or ""
        route_path = getattr(child_route, "path", "") or ""
        expected_path = f"/api/v1{prefix}{route_path}".replace("//", "/")
        if expected_path.endswith("/") and len(expected_path) > 1:
            expected_path_alt = expected_path.rstrip("/")
        else:
            expected_path_alt = expected_path + "/"

        assert (expected_path in openapi_paths) or (
            expected_path_alt in openapi_paths
        ), (
            f"Feature router '{feature_name}' route '{expected_path}' is not registered in the FastAPI application"
        )


def test_zone_layout_detects_unmounted_router() -> None:
    """Verify that if a feature's routes are not in openapi_paths, we fail.

    Cites: STORY-077 MINOR-1.
    """
    # Fake openapi paths that lack decisions
    openapi_paths = {"/api/v1/health"}

    # We will check that asserting 'decisions' routes will fail
    import importlib

    feature_module = importlib.import_module("src.api.v1.decisions")
    feature_router = getattr(feature_module, "router", None)
    assert feature_router is not None

    with pytest.raises(AssertionError) as exc_info:
        assert_router_routes_registered("decisions", feature_router, openapi_paths)
    assert "Feature router 'decisions' route" in str(exc_info.value)


def test_zone_layout_agreements() -> None:
    """Assert filesystem matches pyproject.toml contracts and aggregated v1 router.

    Cites: Proposal (2026-07-10) §3.4 G4, §6.2, §10 Phase 1.
    """
    # 1. Locate and parse pyproject.toml
    test_dir = Path(__file__).resolve().parent
    repo_root = test_dir.parents[1]
    pyproject_path = repo_root / "pyproject.toml"

    with open(pyproject_path, "rb") as f:
        config = tomllib.load(f)

    # 2. Extract modules list under 'api-feature-independence' contract
    contracts = config.get("tool", {}).get("importlinter", {}).get("contracts", [])
    api_feature_contract = None
    for contract in contracts:
        if contract.get("name") == "api-feature-independence":
            api_feature_contract = contract
            break

    assert api_feature_contract is not None, (
        "api-feature-independence contract not found in pyproject.toml"
    )
    contract_modules = api_feature_contract.get("modules", [])

    # 3. Derive features from contract modules (e.g. 'src.api.v1.decisions' -> 'decisions')
    contract_features = {m.split(".")[-1] for m in contract_modules}

    # 4. Derive features from filesystem
    v1_dir = Path(src.api.v1.__file__).parent
    filesystem_features = discover_features(v1_dir)

    # 4a. Non-vacuity floor (AC8): an empty iteration must not pass green --
    # every assertion below this point is a no-op over an empty set.
    assert filesystem_features, (
        "discover_features returned no features; the feature-shape and "
        "feature-set guards below would pass vacuously"
    )

    # 5. Assert set equality
    assert_features_match(contract_features, filesystem_features)

    # 6. Assert each feature's router is reachable in the aggregated v1 router
    from src.composition.asgi import app

    openapi_paths = set(app.openapi()["paths"].keys())

    for feature in filesystem_features:
        # Dynamically import the feature module
        feature_module = importlib.import_module(f"src.api.v1.{feature}")
        feature_router = getattr(feature_module, "router", None)
        assert feature_router is not None, f"Feature {feature} does not expose a router"

        # Assert that each route of the feature router is registered under the correct path in OpenAPI
        assert_router_routes_registered(feature, feature_router, openapi_paths)

    # 7. Assert the five-file SHAPE (ZR-4), not just the feature-name SET
    # checked at step 5 -- every feature except the documented `health`
    # exception.
    for feature in filesystem_features:
        if feature in _FIVE_FILE_SHAPE_EXCEPTIONS:
            continue
        assert_feature_five_file_shape(feature, v1_dir / feature)


#: All eight OpenAPI operation keys that can legitimately appear under a
#: `paths[path]` mapping (`get`, `put`, `post`, `delete`, `options`, `head`,
#: `patch`, `trace`) -- filters out any future non-method key (FastAPI does
#: not emit one today -- measured zero at STORY-227 refinement -- but the
#: extraction stays defensive rather than assuming that holds forever).
#: STORY-227 fix round: `trace` was missing from an earlier 7-entry version
#: of this set, which would have silently dropped a TRACE route from a table
#: that claims to be an exact (method, path) pin.
_HTTP_METHODS = {
    "get",
    "put",
    "post",
    "delete",
    "patch",
    "options",
    "head",
    "trace",
}


def route_method_path_pairs(openapi_paths: dict) -> set[tuple[str, str]]:
    """Flatten an OpenAPI `paths` mapping to `(METHOD, path)` pairs.

    STORY-227 AC1: a set of paths alone cannot catch a `GET` -> `POST` change
    on a surviving route -- the path is unchanged, only the method moved.
    Pairing method with path closes that gap.
    """
    return {
        (method.upper(), path)
        for path, methods in openapi_paths.items()
        for method in methods
        if method in _HTTP_METHODS
    }


def test_route_method_path_pairs_includes_trace() -> None:
    """Meta-test for the helper itself (STORY-227 fix round): an earlier
    7-entry version of `_HTTP_METHODS` omitted `trace`, one of OpenAPI's
    eight legitimate operation keys, so a TRACE route would have been
    silently dropped from a table that claims to be an exact pin. Proven
    against a synthetic input, before trusting the helper against the real
    app below."""
    synthetic_paths = {"/api/v1/probe": {"trace": {}, "get": {}}}
    assert route_method_path_pairs(synthetic_paths) == {
        ("TRACE", "/api/v1/probe"),
        ("GET", "/api/v1/probe"),
    }


#: STORY-155b AC6 / STORY-227 AC1: the exact (method, path) table left behind
#: once the sample-mode feature's GET/PUT /sample-mode routes are gone -- a
#: pinned SET EQUALITY over (method, path) PAIRS, not just paths, so a
#: `GET` -> `POST` change on a surviving route (e.g. `/api/v1/maintenance`,
#: which legitimately carries both GET and POST) fails here too, not just a
#: route accidentally dropped or renamed by the same diff.
_EXPECTED_ROUTE_TABLE = {
    ("GET", "/api/v1/approvals"),
    ("GET", "/api/v1/availability"),
    ("GET", "/api/v1/availability/component/{component_id}"),
    ("GET", "/api/v1/components"),
    ("POST", "/api/v1/decisions/{proposal_id}"),
    ("GET", "/api/v1/health"),
    ("GET", "/api/v1/history"),
    ("GET", "/api/v1/maintenance"),
    ("POST", "/api/v1/maintenance"),
    ("DELETE", "/api/v1/maintenance/{window_id}"),
    ("GET", "/api/v1/publications"),
    ("GET", "/api/v1/topology"),
}


def test_sample_route_removed_without_disturbing_any_other_route_or_method() -> None:
    """AC6 (STORY-155b) + AC1 (STORY-227): `GET`/`PUT /api/v1/sample-mode` no
    longer exists, and the remaining route table matches EXACTLY on
    (method, path) pairs -- proving no other route, and no other route's
    METHOD, was touched by this removal.

    Renamed from `test_the_removed_sample_route_is_gone_and_no_other_route_changed`
    (STORY-227 AC6): that name was shaped by STORY-155b's own AC5 grep for the
    removed feature's identifier (case-insensitive, zero matches required across
    `backend/`) -- the original draft name spelled that identifier out literally and
    had to be renamed mid-story to avoid matching its own story's grep. This name
    reads for a human while still avoiding that identifier."""
    from src.composition.asgi import app

    openapi_paths = app.openapi()["paths"]
    openapi_path_names = set(openapi_paths.keys())
    openapi_pairs = route_method_path_pairs(openapi_paths)

    assert "/api/v1/sample-mode" not in openapi_path_names
    assert openapi_pairs == _EXPECTED_ROUTE_TABLE, (
        f"route table drifted beyond the sample-mode removal. "
        f"Difference: {openapi_pairs.symmetric_difference(_EXPECTED_ROUTE_TABLE)}"
    )


_REPO_ROOT = Path(__file__).resolve().parents[2]
_SEED_DYNAMO_PATH = _REPO_ROOT / "backend" / "src" / "composition" / "seed_dynamo.py"

_TOPOLOGY_KEY_NAMES = {"pk", "sk"}


def find_hand_built_topology_key_dicts(path: Path) -> list[int]:
    """Line numbers, in source order, of every `{"pk": ..., "sk": ...}`-shaped dict
    literal in `path`.

    ZR-8 Finding 1 (`docs/scrum/wiki/zone-rules.md`): the topology key schema is
    owned by `adapters/persistence/topology_keys.py` alone. A dict literal naming
    either `"pk"` or `"sk"` as a key, anywhere in this file, means it is being
    hand-built again rather than obtained from that module.

    Narrow by construction -- this is a literal-`ast.Dict`-node check, nothing more.
    It CATCHES a plain dict literal (`{"pk": ..., "sk": ...}`), one built inside a
    nested local helper function, and one assembled via a `**` merge
    (`{**other, "pk": ...}`). It is BLIND to every other way the same two-key shape
    can be constructed: `dict(pk=..., sk=...)` (keyword-call form, no `ast.Dict`
    node at all), item-assignment (`key = {}; key["pk"] = ...`), constant-name keys
    (`{_PK: ..., _SK: ...}`, since the key must be a literal string `ast.Constant`),
    and `dict(zip(("pk", "sk"), (...)))`. A pass here means no plain dict literal
    was found -- it does not mean no hand-built key exists.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    violations = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        key_names = {
            key.value
            for key in node.keys
            if isinstance(key, ast.Constant) and isinstance(key.value, str)
        }
        if key_names & _TOPOLOGY_KEY_NAMES:
            violations.append(node.lineno)
    return sorted(violations)


def test_topology_key_guard_detects_and_clears(tmp_path: Path) -> None:
    """Meta-test for the guard itself (STORY-205): prove it actually fires,
    against a throwaway file, before trusting it against the real one below."""
    offender = tmp_path / "offender.py"
    offender.write_text(
        'def f():\n    return {"pk": "TOPOLOGY", "sk": "APP#x"}\n', encoding="utf-8"
    )
    violations = find_hand_built_topology_key_dicts(offender)
    assert violations == [2]

    clean = tmp_path / "clean.py"
    clean.write_text(
        "from src.adapters.persistence.topology_keys import app_item_key\n\n\n"
        "def f():\n    return app_item_key('x')\n",
        encoding="utf-8",
    )
    assert find_hand_built_topology_key_dicts(clean) == []


def test_seed_dynamo_uses_shared_topology_key_schema() -> None:
    """Standing guard (STORY-205, ZR-8 Finding 1, Coverage verdict): asserts
    `composition/seed_dynamo.py` constructs no `pk`/`sk` dict literal of its own
    -- it must obtain the topology key schema from
    `adapters/persistence/topology_keys.py` instead of re-declaring it.
    """
    violations = find_hand_built_topology_key_dicts(_SEED_DYNAMO_PATH)
    assert not violations, (
        "ZR-8 Finding 1 regression: composition/seed_dynamo.py hand-builds a "
        "pk/sk topology key dict at line(s) "
        f"{violations} instead of calling adapters/persistence/topology_keys.py."
    )
