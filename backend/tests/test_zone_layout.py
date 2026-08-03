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
