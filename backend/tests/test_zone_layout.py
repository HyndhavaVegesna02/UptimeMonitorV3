"""Meta-test for API zone layout and import contract compliance.

Cites: Proposal (2026-07-10) §3.4 G4, §6.2, §10 Phase 1.
"""

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
    from fastapi.routing import _IncludedRouter
    from src.api.v1 import router as aggregated_router

    # Collect all included router objects from the aggregated router
    included_routers = [
        r.original_router
        for r in aggregated_router.routes
        if isinstance(r, _IncludedRouter)
    ]

    for feature in filesystem_features:
        # Dynamically import the feature module
        feature_module = importlib.import_module(f"src.api.v1.{feature}")
        feature_router = getattr(feature_module, "router", None)
        assert feature_router is not None, f"Feature {feature} does not expose a router"

        # Assert that the feature router is in the set of included routers
        assert any(feature_router is r for r in included_routers), (
            f"Feature router '{feature}' is not included in the aggregated v1 router"
        )
