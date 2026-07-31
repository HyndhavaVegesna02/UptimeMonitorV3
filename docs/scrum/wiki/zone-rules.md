---
title: Zone-intent rule catalogue — the boundary rules the eight contracts cannot see
code_refs: [backend/src/adapters/inbound/dynatrace/adapter.py, backend/src/core/services/ingest_service.py, backend/src/core/domain/signal.py, backend/src/core/ports/status_publisher.py, backend/src/adapters/outbound/statuspage/__init__.py, backend/src/adapters/inbound/dynatrace/health_mapping.py, tools/demo_engine/assumed_failure_codes.py, backend/src/core/domain/publication.py, backend/src/core/domain/component.py, backend/src/core/ports/component_repository.py, backend/src/core/ports/observation_repository.py, backend/src/core/ports/__init__.py, backend/src/core/ports/signal_ingest.py, tools/demo_loop_gate/harness.py, backend/src/composition/settings.py, backend/src/composition/run.py, backend/src/composition/app.py, backend/tests/test_zone_layout.py, backend/src/api/v1/health/controller.py, backend/src/api/v1/decisions/__init__.py, backend/src/adapters/persistence/dynamo_observation_repository.py]
verified_sha: c0a4d71
verified_sprint: sprint-66
status: verified
# code_refs deliberately NARROW (STORY-194, sprint-66): scoped to EXACTLY the
# files this article's rules cite as compliant/illustrative/violating examples
# — never whole-zone directories. A whole-zone ref (e.g. "backend/src/core/")
# would mark this article stale on every future sprint that touches ANY file
# in core/adapters/composition/tools, quarantining the yardstick
# STORY-195/196/197 depend on from every future subagent brief. Same
# discipline architecture-boundary.md records in its own frontmatter comment
# (sprint-5 retro amendment). `pyproject.toml` is deliberately NOT a code_ref
# here: it is already a code_ref in 5 articles against the refs-check's
# AMPLIFIER_THRESHOLD of 4, and architecture-boundary.md already owns the
# eight import-linter contracts — this article LINKS to that article for the
# mechanical set instead of re-citing or restating it. Likewise
# `docs/scrum/wiki/api-five-file-convention.md` is referenced by wiki link syntax,
# never as a code_ref (it is docs, and `check_facts` already skips
# `docs/scrum/` paths as cross-references, not code citations).
---

## Purpose

The eight `lint-imports` contracts ([[architecture-boundary]]) check *import direction*
only. STORY-190 showed that an inbound adapter holding and calling a core persistence
port passes all eight while being architecturally wrong — `adapters` legally importing
`core` is exactly what a translation-only adapter does too, so the contracts cannot
distinguish "translates" from "translates and persists." This article catalogues the
zone-*intent* rules that live beyond that mechanical floor: what the PO's 2026-07-30
directive requires, which of the PO's five named areas the contracts already cover
(short section below), and — the actual gap this catalogue exists to name — the rules
`ZR-1..ZR-5` that a future audit (STORY-195, STORY-196) measures the codebase against
and a future guard (STORY-197) mechanises where possible.

## Facts (verified against code)

### Already mechanical — these three areas need no new rule

- **(b) A core service reaching outward** is fully closed by the `core-independence`
  contract (forbidden: `src.core` -> `src.adapters`, `src.composition`, `src.api`,
  `sqlalchemy`, `httpx`, `boto3`). See [[architecture-boundary]] for the citation.
- **(c) An `api` feature importing another feature, or reaching an adapter directly,**
  is fully closed by two contracts together: `api-feature-independence` (the ten
  feature packages may not import one another) and `api-outward-independence`
  (forbidden: `src.api` -> `src.adapters`, `src.composition`, `sqlalchemy`, `psycopg`,
  `httpx`, `boto3`). See [[architecture-boundary]] for both citations.
- **The PO's second concrete rule — "only composition may see both sides and decide
  what happens to an adapter's output"** — already holds by construction, as the
  conjunction of three contracts rather than a rule of its own: `core-independence`
  (core cannot see adapters), `adapters-edge-only` (adapters cannot see api or
  composition), and `api-outward-independence` (api cannot see adapters directly).
  Between them, `composition` is the only zone import-linter still permits to import
  CONCRETE modules from both `src.core` and `src.adapters` for the purpose of
  constructing and wiring them together — no fourth contract is needed to say so.
  **Precision note (this is not the pedantically stronger claim "no module outside
  composition ever imports both `src.core` and `src.adapters`"):** every
  `adapters/inbound/dynatrace/*` module already imports `src.core.domain` by design
  (that is an adapter's whole job), and `backend/src/adapters/inbound/dynatrace/adapter.py`
  additionally imports a SIBLING module inside the SAME `src.adapters.inbound.dynatrace`
  package (`dispatch.py`, `query.py`) — trivially "importing both `src.core` and
  something under `src.adapters`," but that is ordinary within-package organization,
  not composition's cross-zone wiring privilege. The claim above is about a module
  holding a concrete class from ONE zone alongside a concrete class from the OTHER for
  the purpose of dependency injection — that shape exists only in `composition/`.

None of the above is restated from [[architecture-boundary]]; that article owns the
eight-contract citations. This article's job is everything below, which the contracts
cannot see.

**A caveat on two Facts below (ZR-1's "0 current violations" and ZR-2's "zero vendor
identifiers anywhere in `core/`):** both are zone-wide NEGATIVES verified over an
entire zone, not over this article's narrow `code_refs`. A future file that breaks
either claim — a new `adapters/inbound/*` module importing a repository port, or a new
`core/` identifier bearing a vendor word — would very likely NOT be one of this
article's `code_refs`, so the mechanical sweep (`yt_wiki.py sweep`) would not detect
the drift and would not mark this article stale. That is a real, accepted gap in the
narrow-refs discipline, not an oversight: the mitigation is procedural, not breadth —
the inline re-derivation commands given inline with each such Fact are cheap to re-run
at any future review, and STORY-197 AC6 already requires re-adjudicating every
catalogue rule against a fresh read before re-stamping `verified_sha`, which is exactly
where a zone-wide regression would be caught.

### The gap — rules the eight contracts do not enforce

#### ZR-1 — an inbound adapter is a pure translation function; it must never hold or call a persistence port

- **Statement.** An inbound adapter (`adapters/inbound/*`) returns canonical values
  only. It must never import, hold, or call a `core/ports` repository/persistence
  interface — persisting a batch (or a quarantined row) is core's job, done by the
  service the adapter's return value is handed to.
- **Source.** PO directive 2026-07-30 (memory `code-boundary-discipline.md:28-29`),
  concrete rule 1: "an inbound adapter is a pure translation function — it returns
  values and persists nothing; vendor vocabulary never leaves it." Also CLAUDE.md's
  "two things to know" preamble, which names this exact shape as the STORY-190
  motivating case.
- **Compliant citation.** `backend/src/adapters/inbound/dynatrace/adapter.py:26`
  (`fetch_observations`) returns `NormalizationOutcome` — a value — and the whole
  `adapters/inbound/dynatrace/` package imports `src.core.domain` only, never
  `src.core.ports` (verified: `grep -n "from src.core" backend/src/adapters/inbound/dynatrace/*.py`
  returns only `domain` imports, zero `ports` imports). Persistence itself happens one
  layer further in, inside core: `backend/src/core/services/ingest_service.py:121`
  (`IngestService.ingest_observations`) calls `self._rejected_repo.save(...)` — the
  injected `RejectedObservationRepository` port is held and called by the CORE service
  that consumes the adapter's return value, never by the adapter itself.
- **Coverage verdict.** `GUARDABLE` — but narrower than "all of `src.core.ports`."
  `backend/src/core/ports/signal_ingest.py:3-8` is the core's FRONT DOOR ("Adapters
  push BATCHES of canonical observations here... the port is idempotent and validating
  BY CONTRACT") — dossier §6/§8 explicitly allows a driving/push adapter to reference
  this port, so a contract forbidding an inbound adapter from importing it at all would
  ban a shape the design documents as legitimate. The guard must therefore enumerate
  the PERSISTENCE/REPOSITORY ports specifically, not the whole package:
  ```
  [[tool.importlinter.contracts]]
  name = "inbound-adapters-dont-persist"
  type = "forbidden"
  source_modules = ["src.adapters.inbound"]
  forbidden_modules = [
      "src.core.ports.component_repository",
      "src.core.ports.maintenance_repository",
      "src.core.ports.observation_repository",
      "src.core.ports.proposal_repository",
      "src.core.ports.publication_repository",
      "src.core.ports.rejected_observation_repository",
      "src.core.ports.sample_mode_repository",
      "src.core.ports.signal_repository",
      "src.core.ports.watermark",
  ]
  # Maintenance note (STORY-197): a newly added repository/persistence port
  # module MUST be appended to this list in the SAME commit that adds it, or
  # it is invisible to this guard. `src.core.ports.signal_ingest` (the front
  # door) and `src.core.ports.clock`/`status_publisher` (not persistence)
  # are deliberately excluded — see the Statement above.
  ```
  Verified 0 current violations. STORY-197 can show this RED by temporarily adding
  (then reverting) e.g. `from src.core.ports.observation_repository import
  ObservationRepository` to `backend/src/adapters/inbound/dynatrace/adapter.py` — even
  only as an unused type annotation, never called — and confirming the contract trips.

#### ZR-2 — inside `core/`, a vendor name is compliant only in three closed prose FORMS, never as an identifier/annotation/signature/dict-key/stored-value — except inside the one field the domain itself designates for vendor identifiers

- **Statement.** Within `core/` (`domain`, `ports`, `services`, `queries`, and the
  package root `core/__init__.py`), a vendor name (the proper name of a third-party
  vendor/product this system integrates with, or a concrete adapter class name derived
  from one) is compliant in exactly THREE closed forms: (1) a `#` comment; (2) a formal
  docstring (module/class/function, the kind `ast.get_docstring` recognizes); (3) a
  bare string-literal statement following a class-level field assignment — the
  "attribute docstring" idiom Pydantic models in this codebase use per-field, e.g.
  `backend/src/core/domain/publication.py:66`. It is compliant in NO other form: not
  as an identifier (including an attribute name), not as a type annotation, not as
  part of a function/method signature, not as a dict key, and not as any other
  stored/returned data value — **except** inside `Provenance`
  (`backend/src/core/domain/signal.py:26-39`), the ONE field the domain itself
  designates: "Where an observation came from — the ONLY home for vendor
  identifiers" (`backend/src/core/domain/signal.py:27`). A vendor word stored as a `Provenance.system` value
  (e.g. `system="dynatrace"`, `backend/src/adapters/inbound/dynatrace/_assembly.py:110`,
  flowing into exactly that field) is therefore compliant BY DESIGN — it is the rule's
  one sanctioned data channel, not an exception carved out of it. This is why the
  earlier draft of this rule (a bare word list with no form distinction and no
  provenance carve-out) failed spec review: an open word list is not decidable, and a
  blanket "never a stored value" ban would have pointed the rule at the domain's own
  sanctioned design.
- **Source.** PO directive 2026-07-30 (memory `code-boundary-discipline.md:28-29`),
  concrete rule 1 — "vendor vocabulary never leaves it" is the general confinement
  principle this rule states — AND concrete rule 3 (`code-boundary-discipline.md:31-32`)
  — "a port the core owns must be expressible in domain types — if an interface would
  have to name vendor words..., it does not belong in `core/ports/`" — the
  port-signature-specific case this rule also covers. Dossier principle P3
  (`uptime-monitor-v3-design.html:421-422`): "The core speaks only canonical
  vocabulary... A port signature must make sense to someone who has never heard of
  Dynatrace... Vendor identifiers live only inside provenance fields, never in logic."
  CLAUDE.md's ~20-occurrence note is the planning-time evidence this rule adjudicates.
- **Compliant citations (prose / attribute-docstring form).**
  `backend/src/core/domain/signal.py:5-6` (docstring prose spanning both lines: "...
  Vendor identifiers live ONLY inside `Provenance`; every other field reads to someone
  who has never heard of Dynatrace"). `backend/src/core/domain/publication.py:66`
  (`"""Whether the Statuspage publish succeeded or failed (STORY-072)."""` — the
  attribute-docstring idiom, a bare string-literal statement following the
  `outcome: PublicationOutcome = PublicationOutcome.SUCCEEDED` field assignment at
  line 65). This form is NOT an AST module/class/function docstring — `ast.get_docstring`
  does not recognize it, since it is neither the first statement of the enclosing
  `ClassDef` nor of a `FunctionDef`/`Module`. A raw AST walk sees only a bare
  `ast.Expr` wrapping an `ast.Constant` here, which is exactly why the guard (this
  rule's coverage verdict, below) must walk wider than `ast.get_docstring` to see this
  form at all, and must then explicitly NOT treat it as a "stored data value" (the
  forbidden form) — it is prose that happens to live in a bare-`Expr` AST shape.
  **Compliant citation (domain-typed port signature, the rule-3-specific case).**
  `backend/src/core/ports/status_publisher.py:14-19`
  (`StatusPublisherPort.publish(self, change: StatusChange) -> None`) — the class
  name, the method name, and the signature all name only `StatusChange`, a domain
  type; no vendor word anywhere in the signature.
- **Provenance carve-out citation.** `backend/src/core/domain/signal.py:26-39`
  (`Provenance`: `system: str`, `native_id: str`, `native_kind: str`) — the sole field
  group the domain designates for vendor identifiers as DATA, as described above.
- **Six previously-unadjudicated citations, settled by this rewrite — all COMPLIANT
  (prose, no identifier/annotation/signature/dict-key/stored-value form) under the
  form-based rule.** `backend/src/core/domain/component.py:17` ("... both the fake and
  `DynamoComponentRepository` raise this identically" — inside `ComponentNotFoundError`'s
  docstring). `backend/src/core/domain/publication.py:35` ("Frozen read model: written
  once by `DynamoPublicationRepository.record`..." — inside `Publication`'s class
  docstring). `backend/src/core/ports/component_repository.py:53` ("The fake and
  `DynamoComponentRepository` raise this identically" — inside `set_status`'s method
  docstring). `backend/src/core/ports/observation_repository.py:5` and
  `backend/src/core/ports/observation_repository.py:7` ("the
  DynamoDB adapter implements this via an `EVT#<event_id>`/`DEDUPE` marker item,
  `backend/src/adapters/persistence/dynamo_observation_repository.py:58-62`" — module docstring
  prose). `backend/src/core/ports/__init__.py:7` ("...or DynamoDB must understand it"
  — module docstring prose). None of the six names DynamoDB or a concrete adapter
  class as an identifier, annotation, signature, or stored value; every one names it
  inside a docstring explaining the boundary. Under this rule they are COMPLIANT, not
  findings — verified this story by re-reading each of the six lines directly.
- **Illustrative citation of a FORBIDDEN form** (compliant only because it is confined
  to its own adapter, never `core/`): `backend/src/adapters/outbound/statuspage/__init__.py:23`
  (`class StatuspagePublisher(StatusPublisherPort)`) — a class name and constructor
  identity (`page_id`, `component_mapping`) bearing vendor vocabulary. The identical
  shape appearing under `core/` is exactly what this rule forbids. Verified this story
  with an AST walk of every `core/` module (`domain`, `ports`, `services`, `queries`,
  and the package root) for `FunctionDef`/`AsyncFunctionDef`/`ClassDef` names and every
  `arg`/`Name` node against the detection seed below: zero matches.
- **Detection seed for the guard (explicitly NON-EXHAUSTIVE — this is a recall aid,
  not the rule's definition; the definition is the FORM distinction above, which is
  closed and decidable independent of any word list):** `Dynatrace`, `Grail`, `DQL`,
  `Statuspage`, `DynamoDB`, plus the class-name families `Dynamo*Repository` and
  `Statuspage*` (case-insensitive substring match). A future vendor integration adds
  its own tokens to this seed; it does not change the rule.
- **Coverage verdict.** `GUARDABLE`, to a stated extent, via a pytest test that parses
  every `core/` module with `ast` and asserts no detection-seed substring appears in:
  (1) `FunctionDef`/`AsyncFunctionDef`/`ClassDef` names; (2) `arg` names (positional,
  keyword-only, or otherwise); (3) `Name` nodes (identifier references, including type
  annotations written as bare names); (4) `ast.Attribute.attr` (attribute names, e.g. a
  hypothetical `.dynatrace_id`); (5) `ast.keyword.arg` (call-keyword names); (6)
  `ast.Constant` string/number values that are NOT the sole value of an `ast.Expr`
  statement (i.e. neither a real docstring nor the attribute-docstring idiom) —
  covering assignment right-hand sides and dict keys/values. This walk covers the
  rule's forbidden forms (identifier, attribute name, annotation/signature via `Name`/
  `Attribute`/`arg` nodes, and stored/dict-key data values) while correctly excluding
  both prose forms as compliant. **Residue this guard still cannot see, stated
  plainly:** a vendor word inside a STRING annotation (e.g. `def f(x: "DynatraceRow")`,
  which parses as an `ast.Constant`, not a `Name`, until something resolves the
  forward reference) and a DYNAMICALLY CONSTRUCTED identifier (e.g.
  `getattr(obj, "dynatrace_" + suffix)`, `globals()[f"..."]`) — neither is visible to
  a static AST walk. `GUARDABLE` to this extent, with this residue: STORY-197 may not
  adjudicate ZR-2 as fully guarded beyond it.

#### ZR-3 — a module-level constant shared across the `tools/` -> `backend/src/` one-way boundary is declared once, in `backend/src/`, and imported by `tools/` — never re-declared

- **Statement.** SCOPE, pinned (see the measurement below for why): a value DECLARED in
  `backend/src/` — in either of TWO declaration shapes, (i) a module-level named constant
  (an UPPER_CASE assignment target) or (ii) a **default on a settings/config field**
  (e.g. `backend/src/composition/settings.py:21-22`) — whose value `tools/` also needs,
  must be obtained by `tools/` importing the symbol or reading the config at runtime.
  `tools/` must never independently re-declare or hardcode a value equal to one of those,
  **whether it does so at module level or inside a function body**. This is about DECLARED
  values in those two shapes, not every literal in the language — see the measurement below.
  **Both shapes are in scope deliberately, and shape (ii) plus the function-body clause are
  what make the adjudicated violation below actually IN scope** (the first draft of this
  rule pinned only shape (i) at module level, which excluded the one real violation it
  simultaneously claimed to adjudicate — corrected by the orchestrator at STORY-194
  acceptance, 2026-07-31).
- **Source.** PO directive 2026-07-30 concrete rule 4: "`tools/` may import `src.*`,
  never the reverse — so a constant shared between them lives in `backend/src/` and
  `tools/` imports it rather than duplicating the literal." CLAUDE.md's "two things to
  know" preamble: "They live in exactly one place — `tools/` derives them, never
  redeclares them."
- **Compliant citation.** `tools/demo_engine/assumed_failure_codes.py:31` imports
  `PROVISIONAL_STATUS_MAPPING` from `backend/src/adapters/inbound/dynatrace/health_mapping.py:35`,
  rather than re-declaring the `("1", "UNHEALTHY")` / `("2", "DEGRADED")` pairs a
  second time.
- **A genuine, adjudicated violation (not merely illustrative).**
  `tools/demo_loop_gate/harness.py:746-750` hardcodes the literal table-name values
  `"uptime-observations"` (line 747) and `"uptime-control"` (line 750) a second time —
  duplicating `backend/src/composition/settings.py:21-22`'s
  `Settings.dynamo_observations_table`/`dynamo_control_table` defaults — even though
  `tools/demo_loop_gate/harness.py:61` already imports `src.composition.config` (a
  SIBLING composition module) for an unrelated reason. This is exactly why "no import
  edge between the declaring modules" is the WRONG exemption criterion: an import edge
  to a DIFFERENT symbol in the same zone does not mean the colliding value was
  actually obtained from `src` — it would have falsely CLEARED a real duplicate. This
  is a genuine ZR-3 finding, left for STORY-196 to report (not fixed here — C1: nothing
  is fixed inline in 194/195/196).
- **Measurement pinning the scope (re-run this story, at HEAD):** a WIDE reading —
  every scalar `ast.Constant` value (`str`/`int`/`float`/`bool`/`None`) anywhere under
  `tools/` compared against anywhere under `backend/src/` — found **101 distinct
  colliding values** (`None`, `0`, `1`, `True`, `'utf-8'`, HTTP path fragments like
  `'/health'`, etc. — noise, not shared intent). The NARROW reading — module-level
  UPPER_CASE constant declarations only, same two trees — found **0 colliding
  values** by this literal-equality test (the `assumed_failure_codes.py`/
  `health_mapping.py` pair above is a real agreement via IMPORT, which a
  literal-value comparison cannot see at all). This wide-101/narrow-0 gap is the reason
  the scope is pinned to declared values rather than every literal.
  **Why that narrow reading returned 0 even though a real duplicate exists — read this
  before building the sweep (orchestrator correction, STORY-194 acceptance 2026-07-31):**
  the narrow measurement counted ONLY shape (i) at module level on BOTH sides, and the
  adjudicated `harness.py`/`settings.py` violation below is neither — `settings.py:21-22`
  is shape (ii) (a field default, not an UPPER_CASE module constant) and the `harness.py`
  side is a literal inside a FUNCTION BODY. So the 0 is an artifact of the first draft's
  too-narrow scope, NOT evidence that the tree is clean. Under the pinned scope as it now
  stands — both declaration shapes, and `tools/`-side literals anywhere including function
  bodies — the sweep MUST find the `harness.py` case. **That is the demonstration STORY-196
  AC3 requires** ("shown capable of finding one" before an empty result elsewhere is
  accepted): if a STORY-196 sweep reports 0 while that case stands, the sweep is wrong, not
  the tree. **Note for the record:** this story's own
  re-measurement gives 101, not the 105 quoted at hand-off; the qualitative
  conclusion (wide reading is unusably noisy, narrow reading needs the
  import-exception rule below to catch anything at all) holds under either count —
  flagged here rather than silently substituted, per instruction to say when a
  number doesn't reproduce.
- **Coverage verdict.** `GUARDABLE` (a pytest test — the "duplicated-declaration
  sweep" STORY-196 builds and must demonstrate capable of finding the `harness.py`
  case above before its own "no duplicates" result elsewhere is accepted; STORY-197
  may promote it to a standing test): collect the `backend/src/` side as BOTH declaration
  shapes — module-level UPPER_CASE constants AND settings/config field defaults — then flag
  any `tools/`-side literal equal to one of those values, wherever that literal appears
  (module level or inside a function body), UNLESS the `tools/` side obtains the value from
  `src` at runtime (an import of the declaring symbol, or a read of the config object,
  resolving to the same declaration) — "some import exists between the two files" is not the
  criterion; "this specific value was obtained from `src`" is. Scoping the `backend/src/`
  side to only module-level UPPER_CASE constants is the mistake that made this rule's own
  adjudicated violation invisible to it; do not re-introduce it. Not guardable by `lint-imports` itself: its
  `root_package` setting is `"src"` (see [[architecture-boundary]] V6), which makes
  it structurally blind to anything
  under `tools/` (no `tools/` module is even a
  candidate `source_modules`/`forbidden_modules` entry for any contract) — that fact
  is folded into this one `GUARDABLE` verdict rather than stated as a second,
  competing verdict.

#### ZR-4 — every `api/v1` feature is exactly five files, with one documented exception

- **Statement.** Each feature package under `api/v1/` divides into exactly the five
  files [[api-five-file-convention]] names (`__init__.py` router re-export,
  `controller.py` HTTP routes, `models.py` DTOs, `validation.py` syntactic checks,
  `service.py` thin orchestration). A feature that is a genuine, documented static
  probe with nothing to model, validate, or orchestrate MAY ship fewer files, but that
  is a NAMED, deliberate exception recorded in its own code — never silent drift.
- **Source.** [[api-five-file-convention]] (verified wiki article, sprint-63) plus
  CLAUDE.md's api zone description: "thin FastAPI HTTP surface (five-file features
  under `api/v1/`)."
- **Compliant citation.** `backend/src/api/v1/decisions/__init__.py:6`
  (`from src.api.v1.decisions.controller import router as router`) — one of the nine
  features carrying the full five-file set; [[api-five-file-convention]] holds the
  per-file citations for the other eight.
- **Checked all ten features this story** (`ls backend/src/api/v1/*/`, excluding
  `_shared/`, which is explicitly not a feature): NINE (`decisions`, `components`,
  `approvals`, `maintenance`, `availability`, `history`, `publications`, `topology`,
  `sample_mode`) are exactly five files. ONE — `health` — is the documented exception:
  `backend/src/api/v1/health/controller.py` ships with only `__init__.py` +
  `controller.py` (2 files; no `models.py`/`validation.py`/`service.py`), because it
  is a static liveness stub with nothing to model, validate, or orchestrate —
  `controller.py`'s own docstring says so explicitly: "gives the
  `api-feature-independence` import-linter contract a second feature so the contract
  is non-vacuous." This is the one legitimate deviation this story found; a NEW
  feature shipping fewer than five files without an equivalent documented reason
  would be a ZR-4 finding.
- **Coverage verdict.** `GUARDABLE` — an extension to
  `backend/tests/test_zone_layout.py:125-173`
  (`test_zone_layout_agreements`), which today asserts feature-SET equality against
  the `api-feature-independence` contract and router registration, but NOT the
  five-file SHAPE. Sketch: for each feature returned by `discover_features(v1_dir)`
  except `health` (or any future feature carrying an equivalent documented
  single-file-shape exception, enumerated by name), assert its file set equals
  exactly `{"__init__.py", "controller.py", "models.py", "validation.py",
  "service.py"}`.

#### ZR-5 — the two composition roots that can each build a live, vendor-credentialed publisher must resolve config identically

- **Statement.** `composition/run.py::main` (the loop) and
  `composition/app.py::create_app` (the API's approve trigger) are the two places a
  live Statuspage-credentialed publisher can be constructed. Wherever their config
  resolution can diverge in a way that changes WHICH publisher gets built —
  `CONFIG_DIR` chief among them, since `Config.statuspage_mapping()` being empty is
  the whole publish guard — they must resolve it through the same mechanism and
  default identically; neither may hardcode a different default or read a different
  env var than the other.
- **Source.** CLAUDE.md's demo-engine section, the sprint-64 `CONFIG_DIR` incident:
  "Setting `CONFIG_DIR` on only one of the two still leaves the OTHER process
  resolving `config/apps` by default... Two composition roots build a live publisher
  from those credentials and BOTH must point at `config/demo`, or neither does."
- **Compliant citation — both sides agree today.**
  `backend/src/composition/run.py:182-184` (`settings = load_settings(); secrets =
  load_live_secrets(); config = load_config(settings.config_dir)`) and
  `backend/src/composition/app.py:97,137` (`settings = load_settings()` at line 97;
  `cfg_dir = config_dir or settings.config_dir` at line 137) — both route through the
  IDENTICAL `backend/src/composition/settings.py::load_settings().config_dir`
  resolution (which reads `CONFIG_DIR`, defaulting to `"config/apps"`), so they agree
  given the same environment.
- **Honest finding — no current code-level divergence exists.** This story found NO
  citation of an actual violation: both roots call the same function today. The
  sprint-64 incident's real failure mode is OPERATIONAL, not a code disagreement — the
  loop and the API run as two SEPARATE OS processes
  (`tools/demo_loop_gate/harness.py` launches both as real subprocesses), each reading
  its OWN environment, so setting `CONFIG_DIR` in one process's env does not
  propagate to the other's. No import-linter contract and no single-process test can
  see across a process boundary; the harness's own env-setting discipline
  (`tools/demo_loop_gate/harness.py:519` and `tools/demo_loop_gate/harness.py:580`,
  setting `config_dir=` explicitly on BOTH child envs) is today's only guard against
  the operational half, and it is
  procedural, not a code invariant.
- **Coverage verdict.** `GUARDABLE`, but only PARTIALLY — for the code-level half
  only. A parity test that patches `CONFIG_DIR` to an arbitrary value and asserts
  `load_settings().config_dir` (the one function both roots call) resolves to it,
  plus a source-level assertion that neither `run.py::main` nor `app.py::create_app`
  reads `os.environ["CONFIG_DIR"]` directly (both must route through
  `load_settings`, never a parallel read), would catch the regression shape "one root
  starts reading/hardcoding independently of the other." It does NOT and CANNOT guard
  the OPERATIONAL half — the OS-process env-propagation risk that actually caused the
  sprint-64 incident — which only an integration harness launching both real
  subprocesses and inspecting each one's actual env can prove, which
  `tools/demo_loop_gate/harness.py` already does. Stated plainly: this rule's
  mechanical coverage is code-level parity only; the operational risk stays a
  documented runbook discipline (CLAUDE.md's demo-engine section), not a thing a unit
  test can guard.

## Inference (synthesis, not verified)

The eight contracts plus `ZR-1..ZR-5` together are the audit's yardstick: every
`lint-imports`-legal-but-intent-violating shape the PO named now has either a
contract citation (already mechanical) or a rule id, a verdict, and — where
`GUARDABLE` — a concrete next rung. A finding with no rule id in STORY-195/196 is
either a new rule (amend this catalogue and say so) or an opinion to drop (sprint-66
plan, constraint C5).

ZR-1's narrowed contract, had it existed at STORY-190 planning time, would have
caught that story's tempting-but-architecturally-wrong first draft (an inbound
adapter holding and calling `RejectedObservationRepository` directly) before it ever
reached review — a counterfactual, since that draft never actually shipped (the real
`ingest_service.py` code holds and calls the port instead), not a verified fact about
code that exists.

## History

- sprint-66 (STORY-194): created. Rules ZR-1..ZR-3 covered the PO's five named areas
  ((a) adapter persistence -> ZR-1; (b) core reaching outward -> already mechanical;
  (c) api reaching another feature/an adapter -> already mechanical; (d) vendor
  vocabulary escaping its adapter -> ZR-2; (e) the `tools/` <-> `backend/src/`
  duplicated constant -> ZR-3).
- sprint-66 (STORY-194 fix round, spec FAIL on AC5 + 5 quality MAJORs + 9 minors):
  ZR-2 rewritten FORM-based (three closed compliant forms, closed forbidden-form set,
  the provenance carve-out, the six previously-unadjudicated citations settled, the
  vendor-word list demoted to an explicitly non-exhaustive guard detection seed).
  ZR-1's contract sketch narrowed to the enumerated persistence/repository port
  modules (excluding the `signal_ingest` front door). ZR-2's guard sketch extended to
  name `Attribute`/`keyword`/`Constant` node coverage and its stated residue. ZR-3
  pinned to module-level UPPER_CASE constants (101-vs-0 measurement recorded, with a
  note that the pre-fix-round figure of 105 did not reproduce), the import-edge
  exemption replaced with a runtime-import exception, and a real violation
  (`tools/demo_loop_gate/harness.py:746-750` vs `backend/src/composition/settings.py:21-22`)
  adjudicated rather than left as an illustration. ZR-4 (five-file convention) and
  ZR-5 (composition-root parity) added for STORY-196 AC4/AC5. Nine minors applied:
  the STORY-190 counterfactual moved to Inference; ZR-3 given one operative verdict;
  the vendor-vocabulary source correctly split across concrete rules 1 and 3; the
  "only composition sees both sides" claim given its precision parenthetical; ZR-2's
  stated scope widened to match its guard's actual scope (`queries`, package root);
  ZR-1's coverage verdict named the RED-proving mutation; the zone-wide-negative
  caveat added; the `signal.py` citation corrected to `:5-6`.

- sprint-66 (STORY-194 acceptance, orchestrator correction 2026-07-31): ZR-3's pinned
  SCOPE was internally inconsistent with its own adjudicated violation. The scope covered
  only shape (i) (module-level UPPER_CASE constants) on both sides, but the violation it
  adjudicates is a function-body literal in `tools/demo_loop_gate/harness.py:746-750`
  duplicating a pydantic FIELD DEFAULT at `backend/src/composition/settings.py:21-22` —
  neither side in scope. That is also why the narrow measurement returned 0 while a real
  duplicate stood. Corrected in three places (Statement, Measurement, Coverage verdict):
  the `backend/src/` side now covers both declaration shapes, and the `tools/` side counts
  literals inside function bodies. Consequence for STORY-196 AC3: the sweep MUST find the
  `harness.py` case, and a sweep reporting 0 while that case stands is a broken sweep, not
  a clean tree. Neither reviewer could have caught this — it emerged from the fix round's
  own scope-pinning.

**AC3 citation-resolution sweep, rebuilt to EXTRACT from the article (not a
hand-typed manifest) — command and full output recorded in the story file's
History**, per the fix round's re-verification requirement.
