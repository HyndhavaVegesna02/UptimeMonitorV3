---
title: The architecture boundary — four zones + the two CI floors
code_refs: [pyproject.toml, backend/src/core/__init__.py, backend/src/adapters/__init__.py, backend/src/composition/__init__.py, backend/src/api/__init__.py, backend/src/core/ports/__init__.py]
verified_sha: 13bbb07
verified_sprint: sprint-69
status: verified
# code_refs narrowed sprint-5 (retro): scoped to the boundary-DEFINING files — the import-linter
# contracts (pyproject.toml), the FK-direction script + SPINE allowlist, and the four zone package
# roots — NOT all of backend/src/. The article describes the BOUNDARY, which changes only when a
# contract or a zone is added/removed; in-zone code additions no longer falsely flag it stale (the
# detailed in-zone facts live in their own articles). See working-agreements.md (sprint-5 amendment).
---

## Facts (verified against code)
- The backend is four zones under `backend/src/`: `core/` (with `queries/`, `services/`,
  `ports/`, `domain/`), `adapters/` (with `inbound/`, `outbound/`, `persistence/`),
  `composition/`, `api/`. Each is an importable package (`__init__.py` present).
- `src` is the importable top-level package; it physically lives at `backend/src` and is
  exposed via `package-dir = {"" = "backend"}` (`pyproject.toml` ("tool.setuptools")). An editable
  install (`pip install -e ".[dev]"`) makes `import src.core` resolve.
  **That editable install is a plain ABSOLUTE path entry, so `src.*` resolves to the MAIN tree
  from any launch directory that does not itself contain a `src/` package** — a git worktree, a
  scratch copy. The installed `.pth` in the venv's `site-packages` contains one line, the absolute
  path of this checkout's `backend/`. The qualifier is load-bearing and was measured, not reasoned:
  absoluteness is NOT what makes resolution launch-directory-independent — `sys.path[0]` is the
  cwd/script directory and precedes the `.pth` entry, so a launch directory that DOES contain a
  `src/` package shadows the main tree (verified: from a scratch `backend/` holding a stub
  `src/__init__.py`, `import src` resolved to the scratch copy). Consequence for any check that must
  analyse a tree OTHER than the main one (a mutation in a scratch copy, a worktree gate run): force
  `PYTHONPATH=<that tree>/backend` and assert the resolved root rather than assume it. Import-linter
  must run from the repo root, and `backend/tests` has no `__init__.py` so pytest's prepend mode
  inserts `backend/tests` — which cannot shadow `src`. Both therefore really do report on the main
  tree unless pinned. Warned about in
  `pyproject.toml` ("tool.importlinter")'s own header comment, and the dev-only provenance helper
  assert_import_root exists to assert the resolved root rather than assume it (see
  [[dev-setup-and-dod]]). This is not theoretical — it produced two wrong answers during
  STORY-206's QM-5 re-verification before the linter run was pinned (sprint-69).
- **Import boundary (dossier §4)** is enforced by import-linter, run via the module form
  `python -c "from importlinter.cli import lint_imports_command; lint_imports_command()"`
  (the `lint-imports` exe shim has been Device-Guard-blocked since 2026-07-12 — same check,
  same contracts, module path instead of the blocked shim), configured in `pyproject.toml`
  ("tool.importlinter") with nine contracts:
  - `core-independence` (forbidden): `src.core` may not import `src.adapters`,
    `src.composition`, `src.api`, `sqlalchemy`, `httpx`, or `boto3` (`pyproject.toml` ("core-independence")).
  - `core-internal-layering` (layers): `src.core.queries` → `src.core.services` →
    `src.core.ports` → `src.core.domain` (`pyproject.toml` ("core-internal-layering")).
  - `adapters-independence` (independence): `src.adapters.{inbound,outbound,persistence}`
    may not import one another (`pyproject.toml` ("adapters-independence")).
  - `api-feature-independence` (independence): `src.api.v1.decisions`, `src.api.v1.health`,
    `src.api.v1.components`, `src.api.v1.approvals`, `src.api.v1.maintenance`,
    `src.api.v1.availability`, `src.api.v1.history`, `src.api.v1.publications`,
    `src.api.v1.topology`, and `src.api.v1.sample_mode` may not import one another
    (`pyproject.toml` ("api-feature-independence")).
  - `api-outward-independence` (forbidden): `src.api` may not import `src.adapters`,
    `src.composition`, `sqlalchemy`, `psycopg`, `httpx`, or `boto3` (`pyproject.toml` ("api-outward-independence")).
  - `adapters-edge-only` (forbidden): `src.adapters` may not import `src.api` or
    `src.composition` (`pyproject.toml` ("adapters-edge-only")).
  - `api-shared-no-feature-imports` (forbidden): `src.api.v1._shared` may not import any of the
    10 feature packages (`pyproject.toml` ("api-shared-no-feature-imports")).
  - `src-no-tests` (forbidden): `src` may not import `tests` (`pyproject.toml` ("src-no-tests")).
  - `inbound-adapters-dont-persist` (forbidden, STORY-206, ZR-1's guard — [[zone-rules]]):
    `src.adapters.inbound` may not import any of the nine repository/watermark ports
    (`src.core.ports.component_repository`, `maintenance_repository`, `observation_repository`,
    `proposal_repository`, `publication_repository`, `rejected_observation_repository`,
    `sample_mode_repository`, `signal_repository`, `watermark`) — deliberately excluding
    `signal_ingest` (the core's documented front door, dossier §6/§8), `clock` and
    `status_publisher` (neither is persistence) (`pyproject.toml` ("inbound-adapters-dont-persist")).
    **An inbound adapter MUST import a port by its exact module**, e.g.
    `from src.core.ports.signal_ingest import SignalIngestPort` — never the package form
    `from src.core.ports import SignalIngestPort`. `backend/src/core/ports/__init__.py`
    re-exports every port, and import-linter follows indirect chains by default, so the
    package-level form transitively imports all nine forbidden modules at once and trips
    this contract even for the front door (verified by mutation, STORY-206 rework).
- `include_external_packages = true` (`pyproject.toml` ("tool.importlinter")) is REQUIRED because the
  forbidden set names external packages (`sqlalchemy`, `httpx`); without it import-linter
  errors out.
- The dossier §4 example names vendor subpackages (`inbound.dynatrace`, `outbound.statuspage`,
  `persistence`) that all exist today (STORY-181, sprint-63: corrected a comment that had said
  "do not exist yet" long after they were created); the contracts use these real
  `inbound/outbound/persistence` packages so they run against real modules, not phantoms
  (comment at `pyproject.toml` ("adapters-independence")).
- **Schema boundary (dossier §9), RETIRED sprint-49 (STORY-087).** Until the DynamoDB
  cutover this was a second mechanical CI floor — `scripts/check_fk_direction.py` read real
  FKs from `information_schema` over `DATABASE_URL` and failed if any spine table referenced
  a feature table (the 11-table `SPINE` allowlist; feature→spine passed, spine→feature was
  the violation). The relational schema, the Alembic tree, and this check were **all deleted**
  at the cutover (see the archived [[migrations-and-db]]). DynamoDB's two-table design
  (observations + control) has no cross-table foreign keys, so the FK-direction concept no
  longer applies; the import boundary below is now the sole standing CI floor.
- As of sprint-1, Zone 1 code lives in `core/domain` and `core/ports`, so
  `core-internal-layering` now actually bites: `core/ports` imports `core/domain` (allowed)
  and not `core/services` — verified KEPT. The Zone 1 types/ports themselves are catalogued in
  [[canonical-types-and-ports]].
- As of sprint-5, `core/services` is populated for the first time (`IngestService`,
  STORY-009), so the FULL layering chain `core.services → core.ports → core.domain` is now
  exercised end-to-end and `core-internal-layering` stays KEPT against real service code.
  `composition/pull_loop.py` (STORY-009) is the first concrete module importing BOTH sides of
  the boundary (`src.core` + `src.adapters`) — the composition zone's defining privilege —
  and `core-independence` stays KEPT (the service imports no adapter/sqlalchemy/httpx). The
  ingest service + loop are catalogued in [[ingest-service-and-pull-loop]]. The FK check is
  live and green since STORY-006 (`10 checked, 0 violations`).

## Inference (synthesis, not verified)
- The import boundary (`lint-imports`) is now the project's whole bet: enforce the
  replaceability boundary in CI so horizontal, zone-by-zone slicing is safe — the boundary is
  policed before the logic inside it is written. (The schema-spine FK-direction check was the
  second floor until sprint-49; it retired with the relational schema at the DynamoDB cutover.)

## History
- sprint-0: created (STORY-001 scaffold + STORY-002 CI contracts).
- sprint-1: re-verified after Zone 1 landed (STORY-004/005); layering contract now bites.
- sprint-4: re-verified after STORY-008 added the first real `adapters.inbound`
  package (`backend/src/adapters/inbound/dynatrace/`). The Facts above were checked
  against the new code and remain true unchanged: `adapters-independence` now bites for
  real (the dynatrace package imports `src.core.domain` only, no other adapter), and
  `lint-imports` stayed `3 kept, 0 broken`. No contract definition or zone-tree Fact
  changed — only the inference about phantom packages (dossier §4's
  `inbound.dynatrace` example) is no longer phantom on the inbound side.
- sprint-4 (fix loop 1): re-verified after extracting the shared
  `_assembly.assemble_observation` helper within `dynatrace/` (no new
  zone/package/contract — purely a within-package move). `lint-imports` stayed
  `3 kept, 0 broken`.
- sprint-5: re-verified after STORY-009 populated `core/services` (`IngestService`) + added
  `composition/pull_loop.py`, and STORY-020 added a named error in `dynatrace/`. No
  zone-tree / contract Fact changed; the full `core.services→ports→domain` layering chain is
  now exercised and `composition` gained its first both-sides importer. `lint-imports` stayed
  `3 kept, 0 broken`; FK-direction `10 checked, 0 violations`. verified_sha → cca043f.
- sprint-9: re-verified after STORY-013 added the FIRST `adapters/outbound/` impl
  (`outbound/statuspage/`) + a second `composition` both-sides importer
  (`composition/publish_helper.py`), and STORY-012 added `core/domain/proposal.py`,
  `core/ports/proposal_repository.py`, and `adapters/persistence/proposal_repository.py`. No
  zone-tree / contract Fact changed — `outbound` is a real package now, `core-independence` +
  `adapters-independence` stayed KEPT (`3 kept, 0 broken`), FK-direction `10 checked, 0 violations`.
  verified_sha → 2d42c60.
- sprint-14: re-verified after adding the 5th contract (`src-no-tests`, forbidden, `src` may not import `tests`) to prevent leaks of fakes/mocks into production. verified_sha → bbc324e.
- sprint-14: `src.api.v1.maintenance` added to the `api-feature-independence` contract (STORY-038) — the maintenance feature is now isolated from all other feature modules. verified_sha → 8e15534.
- sprint-15: `src.api.v1.availability` and `src.api.v1.history` added to the `api-feature-independence` contract (STORY-014c) — availability + history read features are now isolated from all other feature modules. `lint-imports`: 5 kept / 0 broken. verified_sha → 7efe64c.
- sprint-18: re-verified after adding `seed.py` to composition zone and the new database migration to link signals to components. No import-linter contracts violated (`5 kept / 0 broken`); FK check verified 11 foreign keys with 0 violations (stays green since the FK is spine->spine). verified_sha → 19eefc8.
- sprint-19: `src.api.v1.publications` added to the `api-feature-independence` contract (STORY-037) — the publications read feature is isolated from all other feature modules. `lint-imports`: 5 kept / 0 broken. verified_sha → b80552d.
- sprint-20: re-verified (STORY-016). `httpx` moved from a dev extra to a runtime dep and is now
  used by the two adapter HTTP executors — `core-independence` still forbids `core` importing it
  (the forbidden-module Fact is reaffirmed, not changed). No zone/contract change; `lint-imports`
  5 kept / 0 broken, FK 11/0. verified_sha → d9c2a77.
- sprint-22: re-verified (STORY-016c). The only `pyproject.toml` change was `[tool.ruff] exclude =
  [".agents", ".venv"]` — a ruff-scope tweak unrelated to the import-linter contracts or zone structure
  this article describes. 5 contracts kept / 0 broken, FK 11/0, unchanged. verified_sha → ed19084.
- sprint-25: re-verified (STORY-015a). The only `pyproject.toml` change was adding `"frontend"` to
  `[tool.ruff] exclude` (the new Vite/React SPA has no Python; ruff stays scoped to backend). The
  frontend is a separate zone with no import into `backend/src` and no bearing on the five import-linter
  contracts or the FK-direction boundary. 5 contracts kept / 0 broken, FK 11/0, unchanged.
  verified_sha → 08d91e7.
- sprint-28: re-verified (STORY-042). The only `pyproject.toml` change was adding `uvicorn[standard]`
  to the dev extras. STORY-042 also added `backend/src/composition/asgi.py` (an ASGI entrypoint —
  `app = create_app()`); it lives in `composition`, the zone permitted to import both the api surface
  and the wiring, so it introduces no contract break. 5 contracts kept / 0 broken, FK 11/0.
  verified_sha → 6303247.
- sprint-30: `src.api.v1.topology` added to the `api-feature-independence` contract (STORY-044 D3) —
  the new topology feature is isolated from all other feature modules. A new migration
  (`5ed254a8daab_add_signals_interval_seconds`) adds a nullable `signals.interval_seconds` column —
  no FK, so the FK-direction check's SPINE allowlist and violation count are unaffected. 5 contracts
  kept / 0 broken, FK 11/0 unchanged. verified_sha → 280c1e3.
- sprint-31: `src.api.v1.sample_mode` added to the `api-feature-independence` contract (STORY-048
  D3, a TEMPORARY feature — see [[sample-mode]]) — the new sample-mode toggle feature is isolated
  from all other feature modules. A new migration (`09e9aa2cee32_add_sample_mode`) adds a
  dedicated, no-FK, single-row `sample_mode` table — the FK-direction check's SPINE allowlist and
  violation count are unaffected. 5 contracts kept / 0 broken, FK 11/0 unchanged. verified_sha →
  0ea652e.
- sprint-36 (STORY-043, mechanical staleness sweep only): the only `pyproject.toml` edit was
  adding `python-dotenv` to `[project.dependencies]` (a `.env`-loading defect fix at the two
  process entrypoints — see [[dev-setup-and-dod]] and [[ingest-service-and-pull-loop]]) — no
  contract definition, zone-tree, or FK-check change. 5 contracts kept / 0 broken, FK 11/0
  unchanged. verified_sha → 6a33edb.
- sprint-36 (STORY-047, re-verify only): `composition/__init__.py` lost its
  `publish_best_effort` re-export (AC2 folded the free function into
  `BestEffortPublisher` — see [[statuspage-publish]]) — still a plain package
  `__init__.py`, no zone/contract change. 5 contracts kept / 0 broken, FK
  11/0 unchanged. verified_sha → d441468.
- sprint-42 (STORY-074): Added two contracts to `pyproject.toml`: `api-outward-independence`
  and `adapters-edge-only` to mechanically enforce the API zone's thinness and the adapters'
  edge-only roles. Added a new zone layout meta-test (`backend/tests/test_zone_layout.py`).
  `lint-imports`: 7 kept / 0 broken, FK 11/0 unchanged. verified_sha → 257dbda.
- sprint-42 (STORY-075): Added the `api-shared-no-feature-imports` contract to fence the new
  `api/v1/_shared/` package from importing any feature package. `lint-imports`: 8 kept / 0 broken,
  FK 11/0 unchanged. verified_sha → 219af4a.
- sprint-43 (STORY-078): Relocated availability read model whole to a new `core/queries/` subpackage (CQRS-lite). `core-internal-layering` contract updated to: queries → services → ports → domain. verified_sha → 05f640e.
- sprint-46 (STORY-082): Extended core-independence and api-outward-independence contracts in pyproject.toml to forbid boto3 imports, securing DynamoDB boundaries. verified_sha -> abd8609.
- sprint-49 (STORY-087): FK-direction check + the relational spine were deleted at the DynamoDB
  cutover; `code_refs` dropped `scripts/check_fk_direction.py`, the Schema-boundary Facts and the
  Inference were rewritten to reflect the retirement, and the import boundary (`lint-imports`, 8
  contracts kept) is now the sole standing CI floor. verified_sha → 5b4ee36.
- sprint-63 (STORY-181): the sweep flagged `pyproject.toml`. Its "vendor subpackages... do not
  exist yet" comment was corrected — `inbound.dynatrace`, `outbound.statuspage` and `persistence`
  all exist today. The Fact above paraphrasing that comment is corrected to match; no contract
  count or boundary behaviour changed. verified_sha -> b272c32.
- sprint-69 (STORY-206, `d62c69b`): added the ninth contract, `inbound-adapters-dont-persist`
  (ZR-1's guard — see [[zone-rules]]), forbidding `src.adapters.inbound` from importing the nine
  repository/watermark ports. Tree was clean (0 violations) before this story; shown RED by
  mutation (temporarily importing `src.core.ports.observation_repository` into
  `backend/src/adapters/inbound/dynatrace/adapter.py`), reverted, `git diff` empty. Contract count
  moves 8 -> 9; `lint-imports`: 9 kept / 0 broken. verified_sha -> d62c69b.
- sprint-69 (STORY-206 rework, quality review MAJOR-1/3/4, same `d62c69b`): the first pass's
  recorded rationale was FALSE — `from src.core.ports import SignalIngestPort` in the inbound
  adapter (the package form, naming only the front door) still trips
  `inbound-adapters-dont-persist`, because `backend/src/core/ports/__init__.py` re-exports every
  port and import-linter follows indirect chains by default; reproduced (`Contracts: 8 kept, 1
  broken`, all nine forbidden modules named via the `src.core.ports` re-export chain) and the
  exact-module control proved KEPT (`Contracts: 9 kept, 0 broken`), both reverted, `git diff`
  empty. Added the positive constraint (import by exact module, never the package) to the Facts
  above, and corrected the import-boundary command Fact from the blocked `lint-imports` exe shim
  to its module form (Device-Guard-blocked since 2026-07-12 — CLAUDE.md, `.scrum/definition-of-
  done.md` and [[dev-setup-and-dod]] already carried the module form). `verified_sprint`
  corrected sprint-63 -> sprint-69 to match this History entry's sprint (frontmatter/History
  mismatch caught by review). The same rework also fixed the maintenance-note referent and
  attribution above `pyproject.toml`'s `inbound-adapters-dont-persist` contract (a `code_ref` of
  this article) — comment-only, no contract structure changed. verified_sha bumped
  `d62c69b` -> `c34e193` (the `pyproject.toml` comment-fix commit) to reflect that `code_ref`
  moving; the sweep would otherwise flag this article STALE against it. `code_refs` gained
  `backend/src/core/ports/__init__.py` — the new Facts (both the general one and the History
  entry above) cite it as the file whose re-exports cause the package-import form to trip the
  contract, so it defines part of what this article now describes (`yt_wiki.py facts` flagged the
  citation as uncovered; added rather than removed the citation, since it is load-bearing).
- sprint-69 (STORY-206, QM-5 fix / wiki sweep at resume 2026-08-12): the sweep flagged this
  article STALE again — `pyproject.toml` (a `code_ref`) moved a THIRD time, at `13bbb07`, the
  commit replacing ZR-1's false residue (2). The change there is comment-only and touches no
  contract: the header above `[tool.importlinter]` dropped the bare `lint-imports` invocation (the
  same falsehood quality review MAJOR-3 fixed in this article's Facts) for the module form, and
  gained a warning that the editable install is a plain absolute `sys.path` entry. The contract
  count, the nine contract names and `include_external_packages` are unchanged; the Facts above
  already carried the module form, so nothing there needed correcting. NOT re-verified only: the
  editable-install Fact GAINED the resolves-to-the-main-tree consequence, because this article owns
  the `package-dir`/editable-install mechanism and that mechanism has a trap sharp enough to have
  produced two wrong answers inside STORY-206 itself. Evidence read at re-verification, not
  inferred: the venv's installed `.pth` is a single absolute line pointing at this checkout's
  `backend/`. verified_sha bumped `c34e193` -> `13bbb07`.
- sprint-69 (STORY-206, quality re-review round 3 MAJOR): **the Fact that entry just added
  overstated its own evidence, and the entry stamped the overstatement as read.** It asserted
  `src.*` resolves to the main tree "no matter where the interpreter is launched from — a git
  worktree, a scratch copy, anywhere". The reviewer refuted it with one command and the
  orchestrator reproduced it: from a scratch `backend/` containing a stub `src/__init__.py`,
  `import src` resolves to the SCRATCH copy, because `sys.path[0]` is the cwd/script directory and
  precedes the `.pth` entry. The one-line `.pth` — which is what was actually read — establishes
  "plain absolute path entry" and nothing more; `sys.path` ORDER decides the rest, and it decides
  it the other way. Note the correctly-scoped version was already in `pyproject.toml`'s comment
  ("even when this runs from a worktree or a scratch copy"); only this article universalised it.
  Fact narrowed to "from any launch directory that does not itself contain a `src/` package", with
  the measurement recorded inline, and the reason absoluteness is not the operative property stated
  so the claim cannot be re-broadened by someone re-deriving it. The pin-PYTHONPATH consequence is
  unchanged and still correct — it now also records WHY import-linter and pytest are safe in
  practice (repo-root invocation; `backend/tests` has no `__init__.py`, so its prepended path cannot
  shadow `src`). Third instance in this story of an unverified causal inference carried under a
  verification stamp (QM-2, QM-4, ZR-1 residue (2) v1 — and this one was the orchestrator's).
  No `code_ref` moved; verified_sha stays `13bbb07`.
