# API Zone Restructure — Architecture Proposal

- **Date:** 2026-07-10
- **Status:** PROPOSAL — planning artifact only; no code changes authorized
- **Author:** dev team (multi-agent design panel: 2 exploration agents, 3 architect positions, 1 adversarial verifier)
- **Decision owner:** Product Owner
- **Phasing:** deliberately left OPEN — the roadmap in §10 is indicative; actual sprint commitment happens at a future sprint planning ceremony

---

## 1. Executive summary

The PO asked whether the backend's `api/` zone should be reorganized along the lines of
`C:\Hyn\hov-apis-main\src\backend\api` (feature-first folders), treating that repo as inspiration,
not a copy target, while preserving the hexagonal boundaries this project was founded on.

Three architect agents argued competing positions (feature-consolidation / evolve-in-place /
CQRS-lite read split); an adversarial verifier fact-checked their claims against the code and
empirically ran candidate import-linter contracts. The composed recommendation:

**Do not relocate domain logic. The api zone's thinness is correct — but it is currently
*unenforced*, and the zone lacks a home for cross-feature HTTP policy. Fix both now, cheaply;
adopt the read-model split (`core/queries/`) as a *named future destination* behind explicit
triggers.**

Concretely, the "now" package is:

1. Two new import-linter contracts (verified green against today's code) making the api zone's
   thinness and the adapters' edge-only role build failures instead of conventions.
2. A new `api/v1/_shared/` package — the api zone's owned edge infrastructure: one
   exception→HTTP-status registry, one home for read-window policy, a middleware seam for
   STORY-017 (CORS/auth).
3. A ~20-line meta-test closing the only real drift risk in the new-endpoint recipe.
4. A wiki decision table + numbered new-endpoint checklist.

This answers all three PO pains (scaling, anemia, growth-prep) while *strengthening* the original
boundary purpose: nothing moves out of core, composition keeps sole ownership of assembly, and two
previously aspirational boundaries become mechanical.

---

## 2. Context and motivation

### 2.1 PO pains (stated 2026-07-09)

| Pain | Meaning |
| --- | --- |
| Scaling pain | Adding new endpoints must be cheap and obvious — today it touches 4–5 places across 2 zones |
| api zone feels anemic | Much API-adjacent implementation lives outside `api/` (read compute in `core/services`, wiring in `composition/`) |
| Prep for growth | Deployment, auth/CORS (STORY-017), and more endpoints are coming |

### 2.2 Hard constraint (PO, verbatim intent)

> "Do not forget the purpose of why we wanted boundaries in the beginning, during this process."

Operationalized: core stays vendor-free; every dependency arrow points inward; boundaries are
enforced mechanically by `lint-imports` (build failures, not review comments); the schema spine
never FKs into feature tables; no persisted verdicts (`.scrum/definition-of-done.md:52`).

### 2.3 Scope

Planning only. The deliverable is this document. Phasing is decided later at sprint planning.

---

## 3. Current architecture (verified state)

### 3.1 The four zones

```
backend/src/
├── core/          # domain/ (pure data) · ports/ (interfaces) · services/ (logic)
├── adapters/      # inbound/dynatrace · outbound/statuspage · persistence/ (Postgres repos)
├── composition/   # app.py::create_app(), run.py, seed, settings — the only both-sides zone
└── api/           # thin FastAPI surface
```

Zone sizes (measured 2026-07-09): api 1,725 LOC / 50 files · core 2,281 / 30 · adapters 1,756 / 26
· composition 1,908 / 12.

### 3.2 The api zone today

`api/v1/{feature}/` follows the **five-file convention**
(`docs/scrum/wiki/api-five-file-convention.md`, dossier §13) across 10 features
(health, decisions, approvals, components, maintenance, availability, history, publications,
topology, sample_mode):

| File | Role |
| --- | --- |
| `__init__.py` | router re-export only |
| `controller.py` | HTTP routes, params, status codes — no business logic |
| `models.py` | Pydantic DTOs for HTTP in/out — domain types never leak |
| `validation.py` | stdlib-only syntactic checks |
| `service.py` | thin edge orchestration: validate → call core → shape DTO |

`api/dependencies.py` holds `Depends()` providers reading `app.state`. `composition/app.py::create_app()`
(206 lines) wires repos/publisher/clock into `app.state` and mounts the v1 router (its only
api-facing lines are the import + `include_router`, lines 202–204).

Representative read path (`GET /api/v1/availability`):
`controller.py` → `validation.py` → `service.py` (window defaulting, interval resolution) →
`core/services/availability.py::AvailabilityCalculator.compute()` (pure two-grain math) →
`ObservationRepository.in_window` port → `adapters/persistence/observation_repository.py` (SQL).

Representative write path (`POST /api/v1/decisions/{id}`):
`controller.py` → `service.py` → `core/services/approval.py::ApprovalService` (guards, commit-first
publish) → proposal repo + publisher chain.

### 3.3 Enforcement today: 5 import-linter contracts (`pyproject.toml`)

1. `core-independence` — core forbidden from adapters/composition/api/sqlalchemy/httpx
2. `core-internal-layering` — layers: services → ports → domain
3. `adapters-independence` — inbound/outbound/persistence mutually independent
4. `api-feature-independence` — the 10 feature modules mutually independent
5. `src-no-tests`

### 3.4 Verified defects and gaps in the current structure

These were established by the adversarial verifier reading code and running the linter — not taken
from any position paper on faith:

| # | Finding | Evidence |
| --- | --- | --- |
| G1 | **No contract forbids `src.api` → `src.adapters` / `src.composition` / `sqlalchemy`.** The api zone's defining thinness is a convention, not a build failure. | `pyproject.toml:40-80` — none of the 5 contracts constrain api's outward imports |
| G2 | **Exception→HTTP mapping is inconsistent and partially duplicated.** `availability/controller.py` maps `SignalIntervalUnconfiguredError→409` twice (lines 79-80 and 117-118) and 422 twice (67-68, 108-109); `decisions` and `maintenance` do their mapping in the *service* layer instead; six features map nothing. | verifier read of all 10 controllers |
| G3 | **Read-window policy is duplicated across features, and the duplication is contract-forced.** `_DEFAULT_WINDOW_HOURS = 24` + until/since defaulting exists in `availability/service.py:55-83` and again in `history/service.py:16,43-53`. `api-feature-independence` makes sharing it between features illegal; core is the wrong home for HTTP default policy. Availability's docstring claims window defaulting "has ONE home" — already false. | verifier line-level comparison |
| G4 | **New-endpoint recipe touches 4–5 places across 2 zones**: feature dir, `api/v1/__init__.py`, `api/dependencies.py`, `composition/app.py` (app.state + `create_app` kwarg), and the `api-feature-independence` module list. The only unguarded drift risk: forgetting the contract entry. | traced across recent stories |
| G5 | **STORY-017 (CORS/auth) has no landing zone.** Today it could only bloat `composition/app.py` with HTTP policy. | structural |

**Corrected non-findings** (claims made during exploration that verification killed):

- "Endpoint-test gap (publications/maintenance/topology/sample_mode untested)" — **FALSE.** All 10
  features have HTTP-level tests via injected fakes + `TestClient`
  (availability 19, decisions 9, maintenance 8, sample_mode 8, history 7, topology 6,
  publications 5, approvals 4, components 3, health via `test_app.py`).
- "Exception boilerplate copy-pasted in all 10 controllers" — exaggerated; see G2 (4 features,
  inconsistently placed).
- "`core/services/skew.py` is designed against the calculator's cycle model" — **FALSE**; it
  imports only stdlib+pydantic, and is currently consumed nowhere in `src/` (tests only).

---

## 4. Reference codebase: what hov-apis actually teaches

`C:\Hyn\hov-apis-main\src\backend\api` (24,439 LOC, 11 feature dirs): FastAPI multi-app service,
feature-first `controller.py`/`models.py`/`service.py` per API, central router registry
(`core/app_registry.py` AppConfig dict + dynamic `importlib` loading), shared `core/`
(settings/logging/middleware/rate-limiting/exceptions) and `services/` (auth JWT+FGA, cache,
flags), global exception handlers, URL versioning `/v1/*`.

**Adopt (adapted):** the *idea* of a shared api-owned infrastructure home (their `core/` → our
`api/v1/_shared/`); global exception handlers replacing per-endpoint boilerplate; the discipline of
one obvious per-feature layout — which this repo already has, and executes better.

**Reject explicitly:**

| hov-apis pattern | Why rejected here |
| --- | --- |
| Fat `service.py` (up to 3,468 LOC) mixing business logic + direct DynamoDB access | The exact disease the core/ports/adapters split prevents; our new `api-outward-independence` contract makes it a build failure |
| No repository layer | We keep `core/ports` + `adapters/persistence` |
| Cross-feature imports (`bugi→baseami`) | Already forbidden by `api-feature-independence` |
| Dynamic `importlib` router loading | Their lazy imports exist to dodge circular deps we don't have; static imports keep `lint-imports` and IDEs fully sighted |
| Tuple-based `(result, status_code)` error returns | Typed domain exceptions + one mapper instead |

Key insight from the panel: **the current repo is not a primitive ancestor of hov-apis — it is the
matured form of what hov-apis gropes toward**, with machine-enforced versions of the boundaries
hov-apis maintains only by discipline (and visibly fails to).

---

## 5. Approaches considered

Three positions were argued independently, then adversarially verified.

### 5.1 Position A — Feature-consolidation: own the HTTP edge inside `api/`

Move HTTP-edge ownership into api: `api/shared/` with an `ApiContainer` Protocol (api owns the
interface, composition fulfills it), central error registry, middleware seam, `install(app,
container)` entry point, and a static `registry.py` replacing the hand-edited router list.
Explicitly keeps `AvailabilityCalculator` in core.

- **Survived verification:** the enforcement-gap diagnosis (G1) — A found it first; the central
  exception-handler registry; the meta-test idea.
- **Killed by verification:** its factual case was weakest (the "all 10 controllers" claim
  exaggerated; the `skew.py` justification false). Its own `api-internal-layering` contract is
  self-contradictory: `install.py` in `shared/` must import the v1 registry — an upward import the
  contract forbids. The `ApiContainer`/`install()` inversion moves *app assembly* ownership out of
  composition, against dossier §4, and costs ~26 files of churn to enforce what two TOML stanzas
  enforce for free. The registry meta-test guards a drift that has never occurred in 10 features.

### 5.2 Position B — Evolve in place, no relocation

The five-file convention + zone distribution is already right; answer the pains with:
a wiki checklist + decision table; `api/v1/_shared/` (errors, pagination) + a middleware home;
three new contracts (`api-outward-independence`, `adapters-edge-only`,
`api-shared-no-feature-imports`); a coverage meta-test. Crisp revisit triggers for the read-model
split.

- **Survived verification:** every factual claim checked TRUE, including the decisive one — its
  two headline contracts were **empirically run and pass green today** (0 illegal chains, 138
  files, 403 deps). `create_app` shown to be 97% genuine wiring.
- **Weakness held against it:** it re-describes the anemia as intent without curing the one
  measured symptom (`availability/service.py` at 265 LOC — 3.4× the next-largest api file — grew
  real policy in STORY-044), and it had no answer for G3 (the contract-forced `_resolve_window`
  duplication). Both gaps are covered in the composed design.

### 5.3 Position C — CQRS-lite: `core/queries/`

The DoD's "no persisted verdicts / derived on read" makes the read side a domain tenet; give it a
named home. Move `AvailabilityCalculator` + `AvailabilityResult` + `rollup_group` +
`bucket_into_cycles` whole into a new 4th core subpackage `core/queries/`; extend the layers
contract to `[queries, services, ports, domain]` (queries may import services' pure functions such
as `pipeline.collapse`; services may never import queries — making the P4 "pipeline never consults
availability" docstring mechanical). Read-optimized ports only when a measured need appears.

- **Survived verification:** the philosophy and the smoking gun (G3); the port docstring
  (`core/ports/observation_repository.py:9` — "This is the READ side") and calculator docstring
  ("a short-TTL cache could wrap `compute` later") confirm the read side is already a real,
  half-named concept. The suspected self-breaking trap was **empty**: `skew.py` does not use
  `bucket_into_cycles`; the move itself is mechanically clean (~2 import-line updates:
  `composition/orchestrate.py:29`, `api/v1/availability/service.py`).
- **Killed by verification:** C's *feature-classification contracts* fail today in **all five**
  read features via a transitive chain the verifier proved by running the linter:
  `api.v1.availability.service → api.dependencies (line 27) → core.services.approval`. Import-linter
  follows indirect chains, so every feature touching `dependencies.py` inherits its
  `ApprovalService` import. Fixing that means restructuring `dependencies.py` — scope C never
  priced. Those per-feature read/write contracts are rejected; the `core/queries/` move itself is
  deferred, not rejected (§8).

### 5.4 Panel ranking

**B > C > A** — but the recommendation is a composition, not a winner-takes-all.

---

## 6. Recommended design

### 6.1 Principles

1. **Enforce, don't relocate.** The api zone's thinness becomes a build failure; no domain logic
   moves.
2. **The api zone gains the weight it rightfully owns** — cross-feature HTTP policy — and nothing
   else.
3. **Composition keeps sole ownership of assembly** (dossier §4: "the only zone importing both
   sides"). api *defines* HTTP policy; composition *installs* it.
4. **Every new boundary ships with its contract** — nothing rests on convention.

### 6.2 Target structure ("now" phase)

```
backend/src/api/
├── __init__.py                  # unchanged
├── dependencies.py              # unchanged for now (its ApprovalService import moves in the
│                                #   Later phase — see §8)
└── v1/
    ├── __init__.py              # router aggregator — unchanged mechanism, now meta-tested
    ├── _shared/                 # NEW — api-owned edge infrastructure (underscore = not a feature;
    │   │                        #   excluded from the api-feature-independence module list)
    │   ├── __init__.py
    │   ├── errors.py            # ONE exception→HTTP registry, installed as FastAPI exception
    │   │                        #   handlers; body stays {"detail": str(e)} so all existing
    │   │                        #   endpoint tests pass unmodified; controllers lose their
    │   │                        #   try/except ladders; the controller-vs-service mapping
    │   │                        #   inconsistency (G2) ends
    │   ├── windowing.py         # the ONE home for read-window policy: _DEFAULT_WINDOW_HOURS,
    │   │                        #   resolve_window(since, until, now) — ends G3
    │   ├── middleware.py        # empty seam today; STORY-017 CORS/auth middleware is DEFINED
    │   │                        #   here, composition installs it — ends G5
    │   └── pagination.py        # only when first needed — not speculative
    └── {feature}/ × 10          # five-file convention UNCHANGED
```

Changes outside `backend/src/`:

- `pyproject.toml` — contracts 5 → 8 (§6.3)
- `backend/tests/test_zone_layout.py` — NEW ~20-line meta-test: every directory under `api/v1/`
  (except `_shared`) appears in the `api-feature-independence` module list AND in the v1 router
  aggregator (ends G4's drift risk)
- `docs/scrum/wiki/api-five-file-convention.md` — "five files + `_shared`" revision; numbered
  new-endpoint checklist; the decision table (§6.4)
- `composition/app.py` — gains two calls (`install_error_handlers(app)`,
  `install_middleware(app)`); loses nothing; `create_app(*, proposal_repo=None, ...)` fake-injection
  signature frozen

Internal api-zone import direction, mechanically enforced: **features → `_shared` → core** only.

### 6.3 New import-linter contracts

Contracts 1–5 unchanged. Additions (the first two verified green against today's code by the
adversarial agent; the third becomes satisfiable the moment `_shared/` exists):

```toml
# The api zone's thinness becomes a build failure (closes G1)
[[tool.importlinter.contracts]]
name = "api-outward-independence"
type = "forbidden"
source_modules = ["src.api"]
forbidden_modules = ["src.adapters", "src.composition", "sqlalchemy", "psycopg", "httpx"]

# Adapters are edge-only: they implement ports, they never reach up
[[tool.importlinter.contracts]]
name = "adapters-edge-only"
type = "forbidden"
source_modules = ["src.adapters"]
forbidden_modules = ["src.api", "src.composition"]

# Shared edge infra can never reach into a feature
[[tool.importlinter.contracts]]
name = "api-shared-no-feature-imports"
type = "forbidden"
source_modules = ["src.api.v1._shared"]
forbidden_modules = [
    "src.api.v1.decisions", "src.api.v1.health", "src.api.v1.components",
    "src.api.v1.approvals", "src.api.v1.maintenance", "src.api.v1.availability",
    "src.api.v1.history", "src.api.v1.publications", "src.api.v1.topology",
    "src.api.v1.sample_mode",
]
```

### 6.4 The decision table (goes into the wiki)

| You are writing… | It goes in… |
| --- | --- |
| Domain math, business invariants | `core/services` (later: `core/queries` for pure read derivation) |
| A port shape (what core needs from the world) | `core/ports` |
| HTTP shaping for one feature: routes, DTOs, syntactic validation | `api/v1/{feature}` |
| Cross-feature HTTP policy: error mapping, window defaults, middleware, pagination | `api/v1/_shared` |
| Choosing concrete adapters, env, lifespan, assembly | `composition` |
| Vendor I/O (SQL, Dynatrace, Statuspage) | `adapters` |

### 6.5 How this answers each PO pain

| Pain | Answer |
| --- | --- |
| Scaling | New endpoint = feature dir + 2 aggregator lines + 1 contract line + tests, with the meta-test catching the only forgettable step; error mapping and window defaults come free from `_shared` instead of being re-implemented |
| Anemia | The api zone gains an owned, contract-fenced `_shared` edge — legitimate weight (HTTP policy) rather than stolen weight (domain math) |
| Growth-prep | STORY-017 has a landing zone; v2 versioning is already anticipated by the `api/v1/` package layout (v2 = new `api/v2/` package, features opt in file-by-file); deployment work touches composition only |

---

## 7. Trade-offs accepted

| Chose | Over | Because |
| --- | --- | --- |
| Enforcement + `_shared` now | A's container/registry apparatus | Same enforcement outcome at ~1/5 the churn; assembly stays in composition per dossier §4 |
| Deferring `core/queries/` | Doing the split now | The move is ~4 files whenever executed (~6 at trigger time); the split's *contracts* require unpriced `dependencies.py` surgery; at 2,281 core LOC the fourth layer buys little today |
| One central error registry | Per-feature mapping freedom | Uniformity is worth more than per-feature status creativity; a per-router override remains possible if a future endpoint genuinely needs a different mapping |
| Static router aggregation | hov-apis dynamic importlib registry | Keeps lint-imports and IDEs fully sighted; we have no circular deps to dodge |
| `_shared` inside `api/v1/` | A top-level `api/shared/` | Window policy and error bodies are v1-contract-specific; a future v2 gets its own `_shared` and may diverge deliberately |

---

## 8. Deferred: `core/queries/` (CQRS-lite) — named destination, explicit triggers

**Not rejected — recorded.** When a trigger fires, the move is pre-designed:

**Triggers (either):**
1. A cross-repository aggregation endpoint (e.g. a dashboard-grain read joining observations +
   proposals + publications) forcing edge services to duplicate query orchestration.
2. A second transport (CLI, websocket push, scheduled report) wanting the read logic without HTTP.

**The move (pre-scoped):**
- `AvailabilityCalculator`, `AvailabilityResult`, `rollup_group`, `bucket_into_cycles` relocate
  **whole** from `core/services/availability.py` to `core/queries/availability.py`. The
  calculation/windowing carve-up is explicitly rejected — the two-grain math and its window
  semantics share invariants and stay together.
- `core-internal-layering` becomes `layers = ["src.core.queries", "src.core.services",
  "src.core.ports", "src.core.domain"]` — queries may import services' pure functions
  (`pipeline.collapse`); services may never import queries. P4 ("the pipeline never consults
  availability") becomes a build failure.
- Import updates: `composition/orchestrate.py:29` and `api/v1/availability/service.py` (verified
  the only two consumers; `skew.py` confirmed untangled).
- **Mandatory same-story scope:** split `api/dependencies.py` so read features stop transitively
  importing `ApprovalService` (the proven chain: `availability.service → dependencies:27 →
  core.services.approval`). Without this, any read/write fencing is unenforceable.
- Read-optimized ports (e.g. `AvailabilityReadPort.observations_for_signals(keys, since, until)`)
  only after a *measurement story* shows a real read problem (DoD standing rule). Query ports
  return frozen `core/queries` types, never DTOs; verdict math stays in Python, never SQL
  (protecting no-persisted-verdicts); read-side SQL adds joins, never FKs (spine rule untouched).
- C's per-feature read/write contracts (`api-read-features-no-write-model` /
  `api-write-features-no-queries`) remain rejected even then, unless the `dependencies.py` split
  proves them cheap.

---

## 9. Rejected elements (with reasons, so future sprints don't re-litigate)

| Element | Source | Reason |
| --- | --- | --- |
| `ApiContainer` Protocol + `install()` + `FeatureSpec` registry | A | Moves app assembly out of composition (dossier §4 violation); ~26-file churn; own layering contract self-contradictory; drift it guards has never occurred |
| Moving `AvailabilityCalculator` (or any core service) into `api/` | naive reading of the brief | Non-API consumers exist (`orchestrate.py:29`); invariants are dossier §11 business policy; would re-key domain math to one transport — the disease the boundaries exist to prevent |
| A new top-level `read/` zone | C alternative | A zone with import rules identical to core's is core with a longer path and a broken four-zone diagram |
| hov-apis fat services / no repo layer / dynamic imports / tuple errors / cross-feature imports | reference repo | §4 table |
| Full code generator for feature scaffolding | B option | Worth building only past ~15 features; the checklist + meta-test suffice now |

---

## 10. Indicative phased roadmap (sizing to be confirmed at refinement; phasing is the PO's call)

Story-shaped, each independently green on the full DoD, in dependency order:

**Phase 1 — Enforcement (1 story, ~1–2 pt).**
Add `api-outward-independence` + `adapters-edge-only` contracts + `test_zone_layout.py` meta-test.
Zero source moves; verified green today, so the story is contracts + test + wiki touch.
*Risk: near-zero. Value: G1 closed permanently.*

**Phase 2 — `_shared` foundation (1 story, ~2–3 pt).**
Create `api/v1/_shared/` with `errors.py` (registry + `install_error_handlers`), wire into
`create_app`, strip the try/except ladders from `availability`/`history` controllers and the
service-layer mappings from `decisions`/`maintenance`, add the `api-shared-no-feature-imports`
contract. Acceptance anchor: all existing endpoint tests pass unmodified (error body shape frozen).
*Risk: low-medium (behavioral surface: error responses). Value: G2 closed.*

**Phase 3 — Windowing consolidation (1 story, ~1–2 pt).**
`_shared/windowing.py`; `availability/service.py` and `history/service.py` consume it; delete both
private copies. Acceptance anchor: both features' window defaults provably identical (one shared
test).
*Risk: low. Value: G3 closed.*

**Phase 4 — Docs & recipe (can fold into any of the above).**
Wiki convention article revision + checklist + decision table; CLAUDE.md pointer if commands
change (they don't).

**Phase 5 — STORY-017 lands in the seam (existing backlog story, unblocked by Phase 2).**
CORS/auth middleware defined in `_shared/middleware.py`, installed by composition.

**Phase T (trigger-gated, not scheduled) — `core/queries/` move per §8 (~3 pt including the
`dependencies.py` split).**

Sequencing constraint: Phase 1 before Phase 2 (the meta-test must learn to exclude `_shared`
knowingly, not accidentally). Phases 2 and 3 are independent of each other after Phase 1.

---

## 11. Risks and mitigations

| Risk | Likelihood | Mitigation |
| --- | --- | --- |
| Central error registry accidentally globalizes a mapping a future endpoint wants different | Low | Registry supports per-router override; documented in `errors.py` |
| Error-body shape drift breaks endpoint tests or the frontend's error handling | Medium if careless | Phase 2 acceptance anchor: `{"detail": str(e)}` frozen; endpoint tests must pass **unmodified** — any test edit is a red flag in review |
| `_shared` becomes a junk drawer ("common/utils disease") | Medium over time | Contract forbids `_shared`→feature imports; wiki decision table gives admission criteria (cross-feature HTTP policy only); retro watches its growth |
| Contract additions fight a hidden existing import | Very low | Both headline contracts already run green against HEAD (empirically verified) |
| Wiki staleness after restructure | Certain if unmanaged | Standard forward-blast-radius DoD rule: `api-five-file-convention.md` (and any article whose `code_refs` overlap) re-verified in the same story |
| Frontend impact | None | `models.py` DTOs, URLs, and error bodies unchanged; `frontend/src/api/types.ts` mirror untouched |
| Deferral of `core/queries/` quietly becomes never | Medium | §8 names the triggers in this committed document and in the wiki decision table; retro checks the triggers when read endpoints are added |

---

## 12. Impact summary

| Surface | Impact |
| --- | --- |
| DoD gates | Unchanged commands; `lint-imports` goes 5 → 8 contracts |
| Tests | +1 meta-test file; existing endpoint tests must pass unmodified (Phases 2–3 acceptance anchor) |
| Wiki | `api-five-file-convention.md` revised + re-verified; decision table added |
| Frontend | Zero |
| CLAUDE.md | One paragraph in the api-zone description once `_shared` exists |
| Migrations/DB | Zero |
| Deployment plans | Zero (composition untouched structurally) |

---

## Appendix A — Panel provenance

- Exploration (Haiku): current-repo API map; hov-apis reference map. One exploration claim
  (endpoint-test gap) was falsified during verification and is corrected in §3.4.
- Positions (Opus-tier): A feature-consolidation · B evolve-in-place · C CQRS-lite read split.
- Adversarial verification (Opus-tier): fact-check table (11 claims: 7 TRUE, 2 FALSE, 1 exaggerated,
  1 partly), empirical import-linter runs against scratch configs (B's contracts KEPT; C's
  read/write contracts BROKEN today via the `api/dependencies.py:27 → core.services.approval`
  transitive chain; A's internal layering self-contradictory), and the composed synthesis this
  document recommends.
