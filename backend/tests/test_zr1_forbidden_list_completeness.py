"""ZR-1 standing guard (STORY-220): makes the completeness of
`inbound-adapters-dont-persist`'s `forbidden_modules` list a TEST, closing the
prose maintenance note STORY-206 left as the only thing keeping that list
honest ("a newly added repository/persistence port module MUST be appended to
this list in the SAME commit that adds it, or it is invisible to this
guard"). A mechanical guard whose completeness rests on a sentence nobody must
read is the defect class sprint-67's MAJOR-1 named (`ZR-6`'s row once claimed
a guard that pinned a different property).

Cites: `docs/scrum/wiki/zone-rules.md` ZR-1 (an inbound adapter is a pure
translation function; it must never hold or call a persistence port) and its
Coverage verdict, which specifies the exact `forbidden_modules` list this
test's discovery rule reproduces -- eight modules as of STORY-155b (was
nine before that story's removal).

**AC1 -- the discovery rule.** Every `*_repository.py` file directly under
`backend/src/core/ports/`, plus the explicitly named `watermark.py`, as
`src.core.ports.<stem>` dotted module names. This is a DECIDABLE rule over
filenames, nothing more.

**AC5 -- the residue, stated rather than hidden.** This guard does not make
the list self-maintaining; it makes forgetting it LOUD. Two shapes stay
invisible to it: (1) a persistence port module named following NEITHER
pattern (`*_repository.py`, `watermark.py`) -- discovery would never see it,
so a contract omission for it would never be flagged either; (2) a module
that IS persistence-shaped by this rule's naming pattern but is not actually
a persistence port (an unlikely false-positive shape, symmetric to (1) --
this test does not inspect module CONTENTS, only filenames). Both are
accepted limits of a decidable, filename-based rule, not oversights: the
alternative (inspecting contents to decide "is this really a persistence
port") is not decidable in the same mechanical sense, and the story that
proposed this test explicitly scoped it to filename discovery.

**AC2 -- non-vacuity floor is direction-free.** See `_NON_VACUITY_FLOOR`'s own
comment: it is >= 5, not ">= 9 at time of writing", because a >= 9 floor would
have gone RED on STORY-155b's LEGITIMATE removal of the sample-mode
repository port module (now landed; the floor stayed direction-free and
did not need touching).

**AC3/AC4 -- shown RED, both directions, recorded in the story/board, not as a
permanent mutation test here** (matching the house convention in
`test_zr3_duplicate_declarations.py` / `test_zr7_pagination_guard.py`: the
mutation is performed once against the real tree, observed, reverted, and the
observation is recorded in prose -- not re-run automatically on every gate,
since doing so would require checking in a broken contract or a stray port
file permanently). Full-suite baseline at this test's own addition: 749
passed, 0 skipped.
- AC3 (disk has an extra module the contract doesn't): temporarily added an
  empty `backend/src/core/ports/zzz_repository.py` without touching
  `pyproject.toml`.
  `test_forbidden_modules_matches_discovered_persistence_ports_exactly` failed,
  naming `src.core.ports.zzz_repository` under "On disk but not in the
  contract"; the full suite reported exactly `1 failed, 748 passed` --
  748 + 1 == 749, so no other test changed state. Reverted; full suite back
  to 749 passed, 0 skipped; `git diff` empty.
- AC4 (contract names a module removed from it, still shown RED via the same
  equality check): temporarily removed `"src.core.ports.watermark"` from
  `inbound-adapters-dont-persist`'s `forbidden_modules` in `pyproject.toml`.
  The same test failed, again naming `src.core.ports.watermark` -- now under
  "On disk but not in the contract" (removing it from `declared` while it
  stays on disk produces the identical shape as AC3's new-file case) -- `1
  failed, 748 passed`. Reverted, `git diff` empty. This is the SET-EQUALITY
  proof: a "contract subset of disk" check alone would never fire on a
  REMOVAL from the contract (disk would still be a superset either way);
  only checking BOTH directions catches it.

**AC6.** This module runs inside the existing `python -m pytest` — no ninth
DoD command.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_PORTS_DIR = _REPO_ROOT / "backend" / "src" / "core" / "ports"
_PYPROJECT_PATH = _REPO_ROOT / "pyproject.toml"
_CONTRACT_NAME = "inbound-adapters-dont-persist"


def _load_contract_forbidden_modules(
    pyproject_path: Path, contract_name: str
) -> list[str]:
    """Parse `pyproject_path` and return the `forbidden_modules` list of the
    `[[tool.importlinter.contracts]]` entry named `contract_name`.

    Raises `AssertionError`, naming `contract_name`, if no contract by that
    name is found -- AC2's non-vacuity floor starts here: a parse that finds
    nothing must go RED, never silently resolve to an empty list a lower-bound
    check would then pass vacuously."""
    with open(pyproject_path, "rb") as f:
        config = tomllib.load(f)
    contracts = config.get("tool", {}).get("importlinter", {}).get("contracts", [])
    for contract in contracts:
        if contract.get("name") == contract_name:
            return contract.get("forbidden_modules", [])
    raise AssertionError(
        f"No import-linter contract named {contract_name!r} found in "
        f"{pyproject_path} -- AC2's non-vacuity floor: the contract must be "
        f"found BY NAME before its completeness can be checked."
    )


def _discover_persistence_port_modules(ports_dir: Path) -> set[str]:
    """AC1's decidable discovery rule: every `*_repository.py` file directly
    under `ports_dir`, plus the explicitly named `watermark.py` -- returned
    as dotted `src.core.ports.<stem>` module names, matching the contract's
    `forbidden_modules` entry format exactly. Anything else (`clock.py`,
    `signal_ingest.py`, `status_publisher.py`, `__init__.py`, or a
    persistence port named otherwise) is invisible to this rule -- AC5's
    residue, restated where the rule itself lives."""
    modules: set[str] = set()
    for path in ports_dir.iterdir():
        if not path.is_file() or path.suffix != ".py":
            continue
        if path.stem.endswith("_repository") or path.stem == "watermark":
            modules.add(f"src.core.ports.{path.stem}")
    return modules


def test_discover_persistence_port_modules_matches_rule_and_ignores_non_matching(
    tmp_path,
) -> None:
    for name in (
        "foo_repository.py",
        "watermark.py",
        "clock.py",
        "signal_ingest.py",
        "status_publisher.py",
        "__init__.py",
    ):
        (tmp_path / name).write_text("", encoding="utf-8")

    discovered = _discover_persistence_port_modules(tmp_path)

    assert discovered == {
        "src.core.ports.foo_repository",
        "src.core.ports.watermark",
    }


def test_discover_persistence_port_modules_empty_dir_returns_empty_set(
    tmp_path,
) -> None:
    """Explicit empty-input behaviour (checklist): an empty directory is a
    valid, non-error input and yields the empty set -- never a leaked
    stdlib exception."""
    assert _discover_persistence_port_modules(tmp_path) == set()


def test_load_contract_forbidden_modules_reads_named_contract(tmp_path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        "[[tool.importlinter.contracts]]\n"
        'name = "some-other-contract"\n'
        "forbidden_modules = []\n\n"
        "[[tool.importlinter.contracts]]\n"
        'name = "inbound-adapters-dont-persist"\n'
        'forbidden_modules = ["src.core.ports.a_repository"]\n',
        encoding="utf-8",
    )
    assert _load_contract_forbidden_modules(
        pyproject, "inbound-adapters-dont-persist"
    ) == ["src.core.ports.a_repository"]


def test_load_contract_forbidden_modules_raises_when_contract_not_found(
    tmp_path,
) -> None:
    """AC2's non-vacuity floor starts here: a contract that cannot be FOUND
    by name must fail loudly, never silently resolve to an empty list that
    would then pass a lower-bound check vacuously."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[[tool.importlinter.contracts]]\nname = "unrelated"\n', encoding="utf-8"
    )
    try:
        _load_contract_forbidden_modules(pyproject, "inbound-adapters-dont-persist")
    except AssertionError as exc:
        assert "inbound-adapters-dont-persist" in str(exc)
    else:
        raise AssertionError(
            "_load_contract_forbidden_modules did not raise when the named "
            "contract is absent -- a missing contract must be loud, not a "
            "silent empty result."
        )


# ---------------------------------------------------------------------------
# The real guard: run the discovery rule and the loader against THIS repo's
# real backend/src/core/ports/ and pyproject.toml (AC1, AC2, AC6).
# ---------------------------------------------------------------------------

#: AC2, corrected 2026-08-13 at plan verification: DIRECTION-FREE (>= 5), not
#: ">= 9 at time of writing". Nine was the count under AC1's discovery rule
#: before STORY-155b (remove the sample-mode feature, named in CLAUDE.md)
#: deleted its repository port module -- a floor of 9 would have gone RED on
#: that LEGITIMATE removal, which took the correct count to 8. AC1's set
#: EQUALITY (below) is the real guard; this floor exists only so a parse
#: that finds nothing (a broken discovery rule or a moved contract) goes red
#: instead of green.
_NON_VACUITY_FLOOR = 5


def test_forbidden_modules_non_vacuity_floor() -> None:
    """AC2: the contract is found by name (raises otherwise, per
    `_load_contract_forbidden_modules`) and discovery returned a
    plausibly-populated set. See `_NON_VACUITY_FLOOR`'s comment for why the
    floor is direction-free rather than pinned to today's count of 9."""
    forbidden = _load_contract_forbidden_modules(_PYPROJECT_PATH, _CONTRACT_NAME)
    assert len(forbidden) >= _NON_VACUITY_FLOOR, (
        f"{_CONTRACT_NAME}'s forbidden_modules has only {len(forbidden)} "
        f"entries (floor is {_NON_VACUITY_FLOOR}) -- suspiciously low; "
        f"either the contract lost entries or this test's parse is broken."
    )


def test_forbidden_modules_matches_discovered_persistence_ports_exactly() -> None:
    """AC1/AC4: set EQUALITY between `inbound-adapters-dont-persist`'s
    declared `forbidden_modules` and the persistence ports discovered on
    disk under `backend/src/core/ports/` by AC1's decidable rule -- not a
    subset check in either direction. A module present on disk but missing
    from the contract (AC3's shape -- a new port added without updating the
    list) OR a module named in the contract but absent from disk (AC4's
    shape -- a stale/renamed/removed entry) both fail here, NAMING the
    difference rather than merely reporting unequal."""
    declared = set(_load_contract_forbidden_modules(_PYPROJECT_PATH, _CONTRACT_NAME))
    discovered = _discover_persistence_port_modules(_PORTS_DIR)
    assert declared == discovered, (
        f"{_CONTRACT_NAME}'s forbidden_modules and the persistence ports "
        f"discovered on disk under {_PORTS_DIR} have diverged.\n"
        f"On disk but not in the contract (a new port added without "
        f"updating the list): {sorted(discovered - declared)}\n"
        f"In the contract but not on disk (a stale/renamed/removed entry): "
        f"{sorted(declared - discovered)}"
    )
