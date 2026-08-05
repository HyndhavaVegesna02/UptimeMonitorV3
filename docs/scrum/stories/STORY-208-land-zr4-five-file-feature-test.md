---
id: STORY-208
title: Land ZR-4's guard — extend test_zone_layout to assert the five-file api feature SHAPE
type: chore
points: 1
status: draft
filed: 2026-07-31
refined: 2026-08-05
sprint: 69
---

> **REFINED at sprint-69 planning (2026-08-05).** AC lifted from `docs/scrum/wiki/zone-rules.md`
> ZR-4's Coverage verdict and re-verified against HEAD. PROPOSAL until the PO approves the sprint.
> **Estimate confirmed at 1** — the smallest of the four deferred guards.

## Context

Filed during sprint 66. **Authoritative detail:** `docs/scrum/wiki/zone-rules.md` ZR-4
(`:392-427`); STORY-196 §8 verified all ten features.

`backend/tests/test_zone_layout.py::test_zone_layout_agreements` today asserts feature-SET equality
against the `api-feature-independence` contract, and router registration — but **not the five-file
SHAPE**, which is why ZR-4 exists.

## Re-verification at HEAD (2026-08-05, planning)

`ls backend/src/api/v1/*/` — **ten features**, unchanged since the audit:

- **Nine at exactly five files** (`__init__.py`, `controller.py`, `models.py`, `validation.py`,
  `service.py`): `approvals`, `availability`, `components`, `decisions`, `history`, `maintenance`,
  `publications`, `sample_mode`, `topology`.
- **One documented exception:** `health` — `__init__.py` + `controller.py` only, whose own docstring
  says it exists to give `api-feature-independence` a second feature so the contract is non-vacuous.
- `_shared/` is not a feature and is already excluded by `discover_features`'s underscore rule
  (`test_discover_features_excludes_underscores`, `test_zone_layout.py:41`).

`test_zone_layout_agreements` is at `test_zone_layout.py:126` (the catalogue cites `:125-173`; a
one-line drift, corrected here).

**One HEAD fact the audit sketch does not mention, and it decides AC2:** every feature directory
contains a `__pycache__/` directory on any machine that has run the suite. A naive "the file set
equals exactly the five" assertion is RED on arrival on a developer machine and green in a clean
CI checkout — a guard that depends on whether tests have been run before is worse than no guard.

## Acceptance Criteria

- [ ] **AC1 — the shape is asserted.** `test_zone_layout.py` gains an assertion that, for each
      feature returned by `discover_features(v1_dir)` except an enumerated exception set, the
      feature's Python-module set equals **exactly**
      `{"__init__.py", "controller.py", "models.py", "validation.py", "service.py"}` — set equality,
      not a superset check, so a sixth file is a failure too.
- [ ] **AC2 — directory noise is excluded by a stated rule, not by luck.** The comparison is over
      `*.py` files only; `__pycache__/` and any other non-`.py` entry is excluded explicitly, with a
      comment saying why (it exists on any machine that has run the suite; a guard whose colour
      depends on that is not a guard). Proven by running the assertion in a tree where
      `__pycache__/` is present.
- [ ] **AC3 — the exception set is enumerated by name, with its reason cited.** Exactly one entry,
      `health`, with a comment citing `backend/src/api/v1/health/controller.py`'s own docstring as
      the documented reason. The set is a literal in the test — never a "fewer than five is fine"
      rule, which would let silent drift through.
- [ ] **AC4 — shown RED twice, in both directions (A9).** (a) Rename
      **`backend/src/api/v1/approvals/validation.py`** → the test fails naming the feature and the
      missing file. (b) Add a sixth file (`helpers.py`) to a conforming feature → the test fails
      naming the extra file. Both reverted; `git diff` empty after each; both invocations recorded
      verbatim in the board's `reality_gate` block. (b) is the one that proves set equality rather
      than a subset check.
      **Use the named target, not `models.py`** — corrected at plan verification: every feature's
      `models.py` has two importers (`controller.py`, `service.py`) and `test_zone_layout.py:12`
      does `import src.api.v1`, whose `__init__.py` imports all ten routers, so renaming it yields a
      `ModuleNotFoundError` **collection error** across much of the suite. The shape guard would
      never execute, and the recorded "red" would not be the guard firing. Five `validation.py`
      files have **zero importers** (`approvals`, `components`, `publications`, `sample_mode`,
      `topology`) — verified — and produce a clean guard-level red with the suite intact.
- [ ] **AC5 — the existing assertions survive.** Feature-SET equality against the
      `api-feature-independence` contract and router registration still pass unchanged; this story
      extends `test_zone_layout.py`, it does not rewrite it.
- [ ] **AC6 — runs inside the existing gate.** Collected by the existing `python -m pytest`
      command. No ninth DoD command.
- [ ] **AC7 — the catalogue row flips honestly, in a shape STORY-216 can parse.** ZR-4's
      adjudication row moves from `GUARDABLE-DEFERRED (STORY-208)` to `ENFORCED-BY` with
      `` `backend/tests/test_zone_layout.py::<test name>` `` as a backtick code span in the
      **Verdict** cell; Detail records both AC4 mutations. `verified_sha` bumped in the same commit
      (A18 / C3).
- [ ] **AC8 — non-vacuity floor.** The test asserts `discover_features` returned a non-empty set
      (the ten known features, which `test_zone_layout_agreements` already cross-checks against the
      `api-feature-independence` contract). An empty iteration must not pass green.

## Not in scope

Changing `health` (the exception is legitimate and documented). Adding files to any feature.
`_shared/`, which is not a feature.
