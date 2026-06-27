"""Unit tests for the FK-direction CI check's violation logic (STORY-002 AC5).

Tests `find_violations` as a PURE function — no database. The schema boundary
(dossier §9) is direction-only: a feature table referencing the spine inward is
correct; a spine table referencing a feature table outward is the violation.
"""

from check_fk_direction import SPINE, find_violations


def test_spine_to_feature_edge_is_flagged():
    # components is in the SPINE; incidents is a feature table -> outward ref.
    foreign_keys = [("components", "incidents")]
    violations = find_violations(foreign_keys, SPINE)
    assert violations == [("components", "incidents")]


def test_feature_to_spine_edge_is_not_flagged():
    # incidents (feature) referencing components (spine) is inward -> allowed.
    foreign_keys = [("incidents", "components")]
    violations = find_violations(foreign_keys, SPINE)
    assert violations == []


def test_only_the_spine_to_feature_edge_is_flagged_in_a_mixed_set():
    foreign_keys = [
        ("components", "incidents"),  # spine -> feature  : VIOLATION
        ("incidents", "components"),  # feature -> spine  : ok
        ("observations", "signals"),  # spine -> spine    : ok
        ("incidents", "users"),  # feature -> feature: ok (not our concern)
    ]
    violations = find_violations(foreign_keys, SPINE)
    assert violations == [("components", "incidents")]


def test_no_foreign_keys_means_no_violations():
    assert find_violations([], SPINE) == []


def test_spine_allowlist_matches_dossier_section_9():
    assert SPINE == {
        "apps",
        "signals",
        "components",
        "observations",
        "watermarks",
        "rejected_observations",
        "problem_signals",
        "status_proposals",
        "approval_events",
        "publications",
        "maintenance_windows",
    }
