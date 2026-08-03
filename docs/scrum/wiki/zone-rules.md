---
title: Zone-intent rule catalogue — the boundary rules the eight contracts cannot see
code_refs: [backend/src/adapters/inbound/dynatrace/adapter.py, backend/src/core/services/ingest_service.py, backend/src/core/domain/signal.py, backend/src/core/ports/status_publisher.py, backend/src/adapters/outbound/statuspage/__init__.py, backend/src/adapters/inbound/dynatrace/health_mapping.py, tools/demo_engine/assumed_failure_codes.py, backend/src/core/domain/publication.py, backend/src/core/domain/component.py, backend/src/core/ports/component_repository.py, backend/src/core/ports/observation_repository.py, backend/src/core/ports/__init__.py, backend/src/core/ports/signal_ingest.py, tools/demo_loop_gate/harness.py, tools/demo_loop_gate/env_matrix.py, backend/src/composition/settings.py, backend/src/composition/run.py, backend/src/composition/app.py, backend/tests/test_zone_layout.py, backend/src/api/v1/health/controller.py, backend/src/api/v1/decisions/__init__.py, backend/src/adapters/persistence/dynamo_observation_repository.py, backend/src/core/ports/proposal_repository.py, backend/src/adapters/persistence/dynamo_proposal_repository.py, backend/src/core/services/approval.py, backend/src/core/domain/proposal.py, backend/tests/test_approval.py, backend/src/core/ports/maintenance_repository.py, backend/src/adapters/persistence/dynamo_maintenance_repository.py, backend/src/adapters/persistence/dynamo_component_repository.py, backend/src/core/ports/signal_repository.py, backend/src/adapters/persistence/dynamo_signal_repository.py, backend/src/composition/seed_dynamo.py, backend/src/adapters/persistence/topology_keys.py, backend/tests/test_topology_keys.py, backend/src/composition/vendor_health.py, backend/src/adapters/inbound/dynatrace/query.py, tools/demo_loop_gate/failure_path_reality_gate.py, backend/tests/test_dynamo_maintenance_repository.py]
verified_sha: 96f9048
verified_sprint: sprint-68
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
- **A genuine, adjudicated violation (not merely illustrative). STORY-202 (sprint-67)
  fixed the SEVEN env-var-NAME collisions this rule originally found in this same
  file; this VALUE-shaped pair is the one it deliberately left, filed to STORY-203.**
  `tools/demo_loop_gate/harness.py:753-757` (line numbers as of `1dc1c73`,
  STORY-202's own edits having displaced this pre-existing collision without
  retiring it — re-keyed, not removed, per `test_zr3_duplicate_declarations.py`'s
  `_ADJUDICATED`) hardcodes the literal table-name values `"uptime-observations"`
  (line 754) and `"uptime-control"` (line 757) a second time — duplicating
  `backend/src/composition/settings.py:21-22`'s
  `Settings.dynamo_observations_table`/`dynamo_control_table` defaults — even though
  `tools/demo_loop_gate/harness.py:61` already imports `src.composition.config` (a
  SIBLING composition module) for an unrelated reason. This is exactly why "no import
  edge between the declaring modules" is the WRONG exemption criterion: an import edge
  to a DIFFERENT symbol in the same zone does not mean the colliding value was
  actually obtained from `src` — it would have falsely CLEARED a real duplicate. This
  is a genuine ZR-3 finding, now filed solely to STORY-203 (not fixed here — C1:
  nothing is fixed inline in 194/195/196).
- **A second compliant citation, added by the STORY-202 fix — the two files import
  DIFFERENT SUBSETS of the seven, not both all seven.**
  `tools/demo_loop_gate/env_matrix.py:17-25` imports all SEVEN —
  `CONFIG_DIR_VAR`/`AWS_REGION_VAR`/`DYNAMO_OBSERVATIONS_TABLE_VAR`/
  `DYNAMO_CONTROL_TABLE_VAR`/`DYNAMO_ENDPOINT_URL_VAR`/`STATUSPAGE_PAGE_ID_VAR`/
  `STATUSPAGE_API_KEY_VAR` — because it sets all seven as child-env dict keys.
  `tools/demo_loop_gate/harness.py:62-67` imports only the FOUR it actually
  re-types as a dict key at its six AC8 sites (line numbers as of `1210374`:
  `:546`, `:615`, `:743`, `:749`, `:750`, `:751` — NOT the story's own AC8
  numbers, `:540`/`:609`/`:736`/`:742`/`:743`/`:744`, which were the PRE-edit
  numbers AC8 itself warned would shift) — `CONFIG_DIR_VAR`,
  `DYNAMO_CONTROL_TABLE_VAR`, `DYNAMO_ENDPOINT_URL_VAR`,
  `DYNAMO_OBSERVATIONS_TABLE_VAR` — because
  `harness.py` never re-types `AWS_REGION`/`STATUSPAGE_PAGE_ID`/`STATUSPAGE_API_KEY`
  as a literal dict key anywhere (verified: `grep -n
  '"AWS_REGION"\|"STATUSPAGE_PAGE_ID"\|"STATUSPAGE_API_KEY"' tools/demo_loop_gate/harness.py`
  returns zero hits), so there is nothing for it to import for those three. Both
  files use whichever subset they need as their env-dict keys, rather than
  re-declaring any of the seven env-var NAMES a second time — the same
  reuse-not-rederive shape as the `assumed_failure_codes.py` citation above,
  closing the collision this rule's Coverage verdict's own measurement (below)
  found before STORY-202 landed. **Four is the complete, correct count for
  `harness.py`, not an undercount** — an earlier draft of this sentence claimed
  both files import all seven, which was false at HEAD; corrected in the
  STORY-202 fix round.
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
  adjudicated `harness.py`/`settings.py` violation below is neither —
  `backend/src/composition/settings.py:21-22`
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
  (`tools/demo_loop_gate/harness.py:525` and `tools/demo_loop_gate/harness.py:586`,
  line numbers as of `0d39de7` post-STORY-202, setting `config_dir=` explicitly on
  BOTH child envs) is today's only guard against the operational half, and it is
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

#### ZR-6 — a core-owned port expresses every parameter and return in domain types; a primitive standing in for a domain type that already exists is a boundary finding

- **Statement.** A `core/ports/*` interface speaks canonical vocabulary only (dossier
  P3; see also the "already mechanical" section above and ZR-2's port-signature
  case). Where a domain type already exists for a value a port method takes or
  returns, that method must use it — a bare `str`/`int`/`dict` standing in for an
  existing enum, or for a value that is really always one of a small closed set the
  domain already models, is a boundary finding, not a stylistic nit. This is
  DELIBERATELY NARROWER than "no port may ever take a primitive" (a signal_key,
  actor name, or free-text reason is legitimately a `str` — there is no domain type
  for it to stand in for); the rule bites only where a domain type for the value
  ALREADY EXISTS in the same codebase and the port declines to use it.
- **Source.** Dossier P3 / the PO's concrete rule 3 (`code-boundary-discipline.md:31-32`
  — "a port the core owns must be expressible in domain types — if an interface would
  have to name vendor words..., it does not belong in `core/ports/`"), read together
  with ZR-2's port-signature compliant citation
  (`backend/src/core/ports/status_publisher.py:14-19`,
  `publish(self, change: StatusChange) -> None`), which is the positive shape this
  rule generalizes: a port parameter should be the domain type that already models
  the value, not a primitive standing in for it.
- **The finding this rule adjudicates — FIXED at STORY-200 (sprint-67).**
  `backend/src/core/ports/proposal_repository.py::ProposalRepository.record_approval_event`
  (`action: str`) stood in for `ProposalState` even though `ProposalState` is imported
  in the same file and used correctly, as the domain type, by the sibling method
  thirteen lines above it: `resolve`'s `to_state: ProposalState`. The adapter
  implementing this port,
  `backend/src/adapters/persistence/dynamo_proposal_repository.py::DynamoProposalRepository.record_approval_event`
  (`if action == "approved":`), then compared the resulting bare string against a
  HARDCODED LITERAL rather than an enum member — the exact shape a correct port
  signature would make structurally awkward to get wrong. STORY-195 (sprint-66)
  originally verdicted the adapter-level symptom as an unscored "catalogue gap"
  (`GAP-1`, filed as `STORY-198`) and separately verdicted the PORT file `CLEAN` —
  the quality-review fix round (sprint-66) corrected this: the port signature is the
  root cause, `STORY-198`'s adapter-only fix does not touch it, and it was scored as
  its own `ZR-6` finding, `MAJOR`. **STORY-200 landed the fix**: the port now types
  `action: ProposalState`; `STORY-198` was subsumed rather than landed separately
  (running both would have re-corrupted the same three lines twice — see the story
  file's "Relationship to STORY-198" section).
- **Why the eight `lint-imports` contracts pass it.** Import-linter checks import
  edges between modules, never a method signature's parameter types. `action: str`
  imported nothing at all — there was no edge to check — so this was invisible to
  every one of the eight contracts by construction, exactly like ZR-1/ZR-2's gaps.
  (Unchanged by the fix — worth restating because the SAME invisibility applies to
  any future port-typing regression here.)
- **The narrowing question — RESOLVED at STORY-200, decision (a).**
  `action`'s legal set was a 2-member subset of `ProposalState`'s 5 members (only
  `"approved"`/`"rejected"` are ever passed). The fix story had a real choice: (a)
  widen the port to accept `ProposalState` and accept that 3 of 5 members are
  semantically invalid `action`s, or (b) introduce a narrower 2-member domain type.
  **Decision (a) was taken** — the sibling method `resolve(..., to_state:
  ProposalState)` already speaks `ProposalState` for the same two values, and (b)
  would have bought type precision at the cost of a second declaration of the
  approved/rejected vocabulary (the story file's "design decision" section records
  the full reasoning and an explicit expiry condition: if `action`'s legal set ever
  stops being a subset of `ProposalState`, e.g. a future action with no corresponding
  proposal state, decision (a) expires and (b) becomes correct).
  The "3 invalid members" gap this leaves is closed with a **testable trace, not a
  comment**: `backend/src/core/services/approval.py::ApprovalService._decide` raises
  `backend/src/core/domain/proposal.py::InvalidApprovalActionError` for any
  `to_state` outside `{APPROVED, REJECTED}`, proven by
  `backend/tests/test_approval.py::test_approval_service_decide_rejects_action_outside_approved_or_rejected`.
  This guard is deliberately NEW validation, not reuse of
  `core/domain/proposal.py::is_valid_transition` — that function admits any non-OPEN
  target (`is_valid_transition(OPEN, SUPERSEDED)` is `True`), so it does not
  constrain this narrower set.
- **Coverage verdict.** `GUARDABLE` only partially, and with a real false-positive
  risk: a heuristic AST check (a `core/ports/*` abstract method parameter/return
  annotated as `str`/`int`/`dict`/`bool` where a same-named or clearly-related
  domain `Enum`/`BaseModel` exists in `core/domain/`) would have flagged this
  specific case, but cannot be a clean, zero-false-positive `lint-imports` contract:
  it requires a semantic judgement ("does a domain type already exist for this
  value") that a name-based or type-based heuristic will get wrong on legitimately
  primitive parameters (a `signal_key: str`, a `reason: str | None`, a `limit: int`)
  that have no domain type to stand in for at all and never will. `GUARDABLE` as a
  reviewed lint warning surfaced for human judgement, not as a hard-failing contract —
  this remains true after STORY-200: the fix closed this ONE instance and pinned the
  2-member subset with a real test, but did not add a general port-primitive-leak
  contract, and none is claimed here.

#### ZR-7 — an adapter must satisfy the port contract it implements; silently truncating or narrowing a result set the port promises in full is a boundary violation, not a storage detail

- **Statement.** Where a `core/ports/*` interface's docstring promises a complete
  result set ("all", "every", or a boolean derived from checking the complete set),
  the adapter implementing it must actually return/check the complete set. Reading
  only the first DynamoDB page and silently discarding `LastEvaluatedKey` is not a
  storage-detail simplification when the port's contract is "all" — it is the
  adapter deciding, silently, to narrow what "all" means, which is exactly the shape
  the PO's rule "adapters translate, they don't decide" forbids. This is distinct
  from a port whose contract is explicitly bounded (e.g.
  `PublicationRepository.list_recent(limit: int = 50)`, whose own docstring promises
  only "up to `limit` most-recent" — an adapter honoring a stated limit is not a
  violation of anything).
- **Source.** The port docstrings themselves promise completeness:
  `backend/src/core/ports/maintenance_repository.py:13-19`
  (`list_windows`: "Retrieve all scheduled maintenance windows"),
  `backend/src/core/ports/component_repository.py:18-25`
  (`list_components`: "Retrieve all components from the spine"),
  `backend/src/core/ports/signal_repository.py:18-25`
  (`list_signals`: "Retrieve every seeded signal"),
  `backend/src/core/ports/proposal_repository.py:57-64`
  (`list_open`: "Retrieve all OPEN status proposals... Returns: list[StatusProposal]:
  A list of all open proposals"), and `is_under_maintenance`'s boolean contract
  (`backend/src/core/ports/maintenance_repository.py:34-47`) is a claim about the
  COMPLETE set of windows for a component, not a first-page claim. Also the PO's
  general "adapters translate, they don't decide" principle (the same principle
  ZR-1 draws on for persistence-holding).
- **The finding this rule adjudicates — a real production defect, not a stylistic
  one. FIXED at STORY-199 (sprint-67, landed `460d3ee`).**
  `backend/src/adapters/persistence/dynamo_maintenance_repository.py::is_under_maintenance`
  used to pair an UNBOUNDED key condition (`gsi1pk="MAINT" AND gsi1sk <= <now>#�` —
  every maintenance window ever created, for every component, with no `Limit`) with a
  POST-READ `FilterExpression` narrowing to `component_id`/`ends_at > at`, and discard
  `LastEvaluatedKey` — it never looped. DynamoDB applies `FilterExpression` AFTER the
  1 MB per-page read limit, so once total maintenance-window volume exceeded one
  page, a component that IS under maintenance could silently receive `False` from
  this method — not an error, a wrong answer — which `core/services/decide.py`'s
  suppression logic then silently failed to apply. Four siblings shared the identical
  unpaginated-`query`-against-an-"all"-contract shape:
  `dynamo_maintenance_repository.py::list_windows`,
  `dynamo_component_repository.py::list_components`,
  `dynamo_signal_repository.py::list_signals`,
  `dynamo_proposal_repository.py::list_open`. The correct pattern already existed in
  the SAME directory: `dynamo_observation_repository.py::in_window` (`while True` /
  `ExclusiveStartKey` / `LastEvaluatedKey` loop, with a test-only `self._limit` hook at
  `backend/src/adapters/persistence/dynamo_observation_repository.py:23` that lets a
  test force a small page size without needing a real 1 MB of data) — this was not a
  missing capability, it was an inconsistently-applied one. **All five now carry that
  same loop and the same `self._limit` hook.** `is_under_maintenance` is the one
  boolean-shaped case: it pages until a matching item is found (returning `True`
  immediately, short-circuiting out of the loop) or until `LastEvaluatedKey` is
  exhausted (returning `False`) — it must NEVER terminate on an empty-after-filter
  page, since the `FilterExpression` empties the leading pages while
  `KeyConditionExpression` still matches every window. **The cost is asymmetric, and
  the expensive side is the COMMON one:** the under-maintenance path (the rare one)
  can return early on the first matching page, but the not-under-maintenance path —
  the one every `decide` cycle takes when nothing is under maintenance — can only
  return `False` once `LastEvaluatedKey` is exhausted, i.e. after reading the ENTIRE
  `MAINT` GSI partition. That cost grows with total maintenance-window history
  forever; it is inherent to answering the question correctly with a post-read
  filter, not a defect in this fix. Pinned by
  `test_dynamo_maintenance_repository_is_under_maintenance_paginates_past_forced_page_size`
  (`backend/tests/test_dynamo_maintenance_repository.py`), which seeds five
  other-component windows sorted ahead of the one real match with `_limit=1` and
  asserts `True`. Full detail: [[persistence-adapters]].
- **Why the eight `lint-imports` contracts pass it.** Import-linter checks import
  edges; it has no concept of "did this adapter loop over `LastEvaluatedKey`" or "does
  this docstring's completeness promise hold" — that is runtime pagination behavior
  against a live-shaped dataset, structurally outside anything a static import-graph
  tool can see.
- **Coverage verdict.** `GUARDABLE`, plausibly, but say the false-positive risk
  honestly: a test asserting "every `.query(`/`.scan(` call site in
  `adapters/persistence/` either loops on `LastEvaluatedKey` or is provably bounded
  (a `Limit`/`limit` param whose OWN port docstring promises boundedness, not
  completeness)" would have caught all four siblings above and would not have
  flagged `dynamo_publication_repository.py::list_recent` (bounded by contract) or
  the various `get_item`/single-key `query` calls (structurally a single item, not a
  page-able list). The risk: this needs a definition of "provably bounded" precise
  enough to avoid two failure modes — a false pass on a `Limit=` that is NOT what
  the port's docstring actually promises (e.g. an accidental cap smaller than what
  "all" requires), and a false fail on a query that is genuinely single-item.
  STORY-197 would need to design that definition carefully rather than assume the
  AST shape alone settles it. **The implementable form, decided at the STORY-195
  re-review (2026-07-31) so STORY-197 does not have to rediscover it:** do NOT try to
  mechanise "provably bounded" — resolving adapter method -> port method -> an English
  docstring is not mechanically decidable. Instead assert the hard, decidable half (every
  `.query(`/`.scan(` call site under `adapters/persistence/` loops on `LastEvaluatedKey`)
  and carry a **named exemption list with a reason per entry**, exactly the shape ZR-1's
  contract sketch already uses for its enumerated port modules. That is implementable,
  false-positive-free in this tree, and fails loudly the moment someone adds a sixth
  unpaginated query — which is the property that matters; a fix (STORY-199) can straightforwardly add the same
  pagination loop the observation repository already uses, which is a much smaller
  design question than the guard.

#### ZR-8 — storage and vendor mechanics (a key schema, an item shape, a direct table/SDK call, or query construction) live in exactly ONE adapter; another zone calls that adapter rather than re-implementing them

- **Statement.** A DynamoDB key schema, an item shape, a direct table/SDK call, or
  vendor query-construction logic each belong to exactly ONE adapter
  (`adapters/persistence/*` for storage mechanics, `adapters/inbound/*`/
  `adapters/outbound/*` for vendor-protocol mechanics). A different zone that needs
  that mechanic must CALL the adapter that owns it — never re-derive the schema, the
  item shape, or the query-building logic in its own code. This bites even where
  `lint-imports` legally permits the reach (`composition` importing/reaching
  `adapters`, or calling `boto3` directly, is exactly the wiring privilege the eight
  contracts grant it) — the contracts check import EDGES, never whether a reachable
  capability was reused rather than re-derived.
- **Source.** The PO's "adapters translate, they don't decide" principle, generalized
  from `ZR-1` (an inbound adapter is the SOLE holder of its own translation) to the
  sibling risk this rule names explicitly: a NON-adapter zone re-deriving what an
  adapter already encodes. Motivated by two independently-found instances below, from
  two different failure classes (a persistence key schema; a vendor query builder's
  validation) — not a single anecdote generalized too far.
- **Compliant counter-pattern already in this codebase.**
  `tools/demo_engine/assumed_failure_codes.py:31` imports
  `PROVISIONAL_STATUS_MAPPING` from `backend/src/adapters/inbound/dynatrace/health_mapping.py:35`
  rather than re-declaring it (`ZR-3`'s own compliant reference, one zone-pair over —
  the same reuse-not-rederive discipline, applied here to `composition`/`adapters`
  instead of `tools`/`backend/src`). `backend/src/composition/publish_helper.py:216-222`
  (`build_publisher`) CALLS `StatuspagePublisher`/`make_statuspage_executor()` — the
  adapter that owns the Statuspage HTTP mechanics — rather than building the HTTP
  request itself.
- **Finding 1 — FIXED at STORY-205 (sprint-68).** `composition/seed_dynamo.py` used to
  hand-build the exact `TOPOLOGY`-partition key schema `DynamoComponentRepository` and
  `DynamoSignalRepository` already owned, in THREE places
  (`backend/src/composition/seed_dynamo.py:29-30` — `{"pk": "TOPOLOGY", "sk":
  f"APP#{app.id}"}`; `:43`; `:58-59`) — a THIRD declaration of the same schema, sitting
  on the boot path of BOTH composition roots (`composition/run.py::main`'s topology seed
  call, `composition/app.py::create_app`'s lifespan seed call). This was not a
  theoretical risk: `tools/demo_loop_gate/failure_path_reality_gate.py`'s own docstring
  records the drift already happening once, in a DIFFERENT hand-rolled key site — a
  first version used `pk=COMPONENT#<id>, sk=META` where the repository's real schema is
  `pk=TOPOLOGY, sk=COMPONENT#<id>`, silently writing a phantom item nothing reads and
  costing two full debugging runs before the mismatch was found.
  **The fix (option (b), decided at refinement):** the whole key schema, in BOTH shapes
  it is consumed in — the item-key dict AND the boto3 query condition
  (`Key("pk").eq(...) & Key("sk").begins_with(...)`) — now has exactly ONE declaration,
  `backend/src/adapters/persistence/topology_keys.py` (`app_item_key`,
  `component_item_key`, `signal_item_key`, `component_query_condition`,
  `signal_query_condition`). `DynamoComponentRepository`, `DynamoSignalRepository` AND
  `seed_topology_dynamo` all import from it; `seed_dynamo.py` no longer constructs a
  `pk`/`sk` dict literal anywhere. `tools/demo_loop_gate/failure_path_reality_gate.py`'s
  docstring is repointed to cite the schema module rather than the repository lines
  STORY-199's pagination loops had already displaced. `docs/scrum/wiki/persistence-adapters.md`
  documents the module alongside the two adapters that import it (see [[persistence-adapters]]).
  This fell through the crack between STORY-195 (`adapters/`) and STORY-196
  (`composition/`) auditing disjoint file sets — precisely the failure a two-pass audit
  exists to prevent.
  **Residue, stated rather than quietly closed:** the fix removed the schema
  duplication only. `seed_dynamo.py` still issues its own `boto3` `put_item`/
  `update_item` calls directly — "composition writes to DynamoDB directly" remains
  true, and is a separate, larger question a real topology write port would answer.
  **Expiry condition:** if a core service ever needs to read or write topology, this
  shared-module shape expires and a `TopologyRepository` port (option (a), rejected at
  STORY-205 refinement only because no core service touches this value today) becomes
  correct.
- **Finding 2 — `composition/vendor_health.py::build_vendor_health_query` duplicates a
  DQL query builder without its validation (`GAP-2`, first reported STORY-196).**
  `backend/src/composition/vendor_health.py:40-53` re-implements a fragment of
  `backend/src/adapters/inbound/dynatrace/query.py:52-102`'s (`build_dql_query`)
  query-building, interpolating the SAME trusted `native_id` config value into a DQL
  string literal, WITHOUT reusing `query.py:41-49,79-82`'s `InvalidNativeIdError`
  breaking-character validation. A `native_id` containing a DQL-breaking character
  would raise loudly, by name, the moment `build_dql_query` runs (the ingest path) —
  but `check_vendor_id_health` (`backend/src/composition/vendor_health.py:96-133`) runs
  FIRST, at loop startup, and would instead silently build a malformed query. Full
  mechanism: `docs/scrum/sprints/2026-07-31-sprint-66/audit-api-composition-tools.md` §4.
- **Why the eight `lint-imports` contracts pass both.** `composition` legally
  importing/reaching `adapters` — or, in `seed_dynamo.py`'s case, calling `boto3`
  directly, which `adapters-independence` never restricts for `composition` — is
  EXACTLY the wiring permission the eight contracts grant the composition zone by
  design. The contracts check import edges, not whether a REACHABLE capability was
  actually reused rather than re-derived; a module that hand-builds the same key/query
  a sibling module already encodes imports nothing NEW to trip a contract.
- **Coverage verdict.** `GUARDABLE` only as a reviewed pattern, not a clean
  import-linter contract or a general AST rule: "does this composition-zone code
  re-implement a mechanic an adapter already owns" is a semantic judgement (the same
  class of limitation `ZR-6` states for its own heuristic) — a static check cannot
  distinguish a legitimate NEW capability from a re-derived duplicate of an EXISTING
  one without a maintained, human-curated map of "which adapter owns which mechanic."
  **Finding 1's guard now exists and is `ENFORCED-BY`:**
  `backend/tests/test_zone_layout.py::test_seed_dynamo_uses_shared_topology_key_schema`
  AST-walks `composition/seed_dynamo.py` for any `{"pk": ..., "sk": ...}`-shaped dict
  literal and fails, naming the offending line, if one exists — narrow and per-instance
  (it checks exactly this one file's exact shape), not a general "reused vs re-derived"
  rule; a second file re-implementing a DIFFERENT mechanic would need its own guard, the
  same way this one needed to be purpose-built rather than inherited from anywhere else.
  Finding 2 (`composition/vendor_health.py`) still needs the parallel assertion that it
  calls `adapters/inbound/dynatrace/query.py`'s validation — STORY-204 (its own fix
  story) decides that shape.

## Inference (synthesis, not verified)

The eight contracts plus `ZR-1..ZR-8` together are the audit's yardstick: every
`lint-imports`-legal-but-intent-violating shape the PO named now has either a
contract citation (already mechanical) or a rule id, a verdict, and — where
`GUARDABLE` — a concrete next rung. A finding with no rule id in STORY-195/196 is
either a new rule (amend this catalogue and say so) or an opinion to drop (sprint-66
plan, constraint C5). `ZR-6` and `ZR-7` were both added mid-sprint, from STORY-195's
own quality-review fix round, not from the original STORY-194 planning pass — an
independent audit of STORY-195's footprint found two real, catalogue-worthy shapes
(a port leaking a primitive; four adapters silently truncating a result set their
port promises in full) that STORY-194's five originally-drafted rules did not cover.

ZR-1's narrowed contract, had it existed at STORY-190 planning time, would have
caught that story's tempting-but-architecturally-wrong first draft (an inbound
adapter holding and calling `RejectedObservationRepository` directly) before it ever
reached review — a counterfactual, since that draft never actually shipped (the real
`ingest_service.py` code holds and calls the port instead), not a verified fact about
code that exists.

## Adjudication — every rule's final verdict (STORY-197, AC6)

**This table is authoritative.** Each rule carries exactly one verdict. `ENFORCED-BY` means a guard
exists, runs inside the existing eight DoD commands, and has been **shown RED** (C3/A9) — never
merely "is green". `GUARDABLE-DEFERRED` means the guard is specified in the rule above and a named
story will land it. `UNGUARDABLE` states the reason no mechanical rung can hold it.

| Rule | Verdict | Detail |
| --- | --- | --- |
| ZR-1 | `GUARDABLE-DEFERRED (STORY-206)` | Contract fully specified above (9 enumerated repository/watermark port modules, excluding the `signal_ingest` front door). Tree is CLEAN, so it must be proven RED by the mutation ZR-1 names, not by a live violation. |
| ZR-2 | `GUARDABLE-DEFERRED (STORY-207)` | AST walk specified above, with its residue stated (string annotations, dynamically built identifiers). Tree is CLEAN — mutation proof required. |
| ZR-3 | `ENFORCED-BY backend/tests/test_zr3_duplicate_declarations.py` | Promotes the committed `tools/zr3_duplicate_sweep.py` to a standing test. **Shown RED** by injecting a new duplicate of `Settings.dynamo_observations_table`'s default into a non-excluded `tools/` module. Green today only via a per-entry adjudication list; every unfixed entry names its fix story. |
| ZR-4 | `GUARDABLE-DEFERRED (STORY-208)` | An extension to `backend/tests/test_zone_layout.py`, which today asserts feature-SET equality but not the five-file SHAPE. `health` is the one enumerated exception. |
| ZR-5 | `GUARDABLE-DEFERRED (STORY-209)` for the code-level half; the operational half is `UNGUARDABLE` | A parity test can assert both roots resolve `CONFIG_DIR` only through `load_settings()`. It **cannot** guard the failure that actually caused the sprint-64 incident: the loop and the API are separate OS processes, each reading its own environment, and no single-process test sees across a process boundary. That half stays runbook discipline. |
| ZR-6 | `FIXED (STORY-200, sprint-67) — NO STANDING GUARD` | The one live violation this rule adjudicated is fixed: the port now types `record_approval_event`'s `action: ProposalState` (decision (a), not a narrower type — see the rule text above), and `ApprovalService._decide` raises `InvalidApprovalActionError` for any `to_state` outside `{APPROVED, REJECTED}`, closing the "3 invalid members" gap `is_valid_transition` does not cover — proven by `test_approval.py::test_approval_service_decide_rejects_action_outside_approved_or_rejected`. **That test pins the 2-member SUBSET GUARD, not the port's TYPE.** Mutation-checked: reverting the entire fix (port back to `action: str`, fake back to `str`, adapter back to `if action == "approved":`) leaves the full suite at 696 passed, identical to HEAD — nothing detects a ZR-6 regression. This is honest, not a gap left carelessly: ZR-6's own Coverage verdict (above) already states the general "port primitive stands in for an existing domain type" rule is `GUARDABLE` only as a reviewed lint warning, never a hard-failing contract, and this row now agrees with it instead of contradicting it. A future story could re-widen this port back to `str` with a fully green gate. |
| ZR-7 | `ENFORCED-BY backend/tests/test_zr7_pagination_guard.py` | Two tests. **Shown RED twice** at STORY-197, and again at STORY-199 (sprint-67): removing `list_components`'s `LastEvaluatedKey` loop (the recorded mutation proof) trips the unexempted-violation check, and its removal also fails that method's own AC2 pagination test. STORY-199 landed all five fixes (including `is_under_maintenance`) and removed the five matching exemptions (`460d3ee`); `_EXEMPTIONS` now holds exactly ONE entry — `dynamo_publication_repository.py:53`, `PERMANENT`, for `list_recent`'s stated `Limit=limit` bound. |
| ZR-8 | Finding 1: `ENFORCED-BY backend/tests/test_zone_layout.py::test_seed_dynamo_uses_shared_topology_key_schema` (STORY-205, sprint-68). Finding 2: `GUARDABLE-DEFERRED (STORY-204)` | **Finding 1 fixed and guarded.** `seed_dynamo.py` now obtains the topology key schema (both shapes: item-key dict and boto3 query condition) from `adapters/persistence/topology_keys.py`, the single module `DynamoComponentRepository`/`DynamoSignalRepository` also import — a THIRD declaration removed, not relocated. **Shown RED twice**: against the real pre-fix file (three hand-built sites, at `seed_dynamo.py:28/43/57` as they stood then) before the wiring landed, and again by deliberately re-introducing one hand-built key post-fix and watching the guard name that exact line; both reverted, `git diff` empty. The guard is SHAPE-narrow (this one file, this one dict shape) per its own Coverage verdict — it says nothing about Finding 2. **Finding 2 remains live**, blocked behind STORY-204 (`vendor_health.py` duplicating the DQL builder without its validation). |

**Why only two rules were mechanised (AC5's stopping rule, stated as a result).** ZR-3 and ZR-7 were
chosen because they are the two highest-severity rules with a **live violation to prove the guard RED
against** — ZR-7's five findings include a production defect that silently disables maintenance
suppression, and ZR-3's six include a credential-safety drift risk. Every other rule is either clean
(ZR-1, ZR-2, ZR-4 — provable only by mutation, so cheaper to land alongside its own story), has no
standing guard by design (ZR-5's operational half is `UNGUARDABLE` — no single-process test sees
across the two-OS-process boundary that actually caused the incident), or has no standing guard
because none was ever built for it: **ZR-6's one live instance was fixed at STORY-200 (sprint-67)
without a mechanised guard** — its adjudication row above records this plainly rather than claiming
one exists. **ZR-8's Finding 1 was fixed and given a mechanised guard at STORY-205 (sprint-68)**,
after this paragraph's own "why only two" count was written — a guard did not exist at STORY-197
landing time, which is what this paragraph explains, and does not retroactively change; Finding 2
remains live, still blocked behind STORY-204.

### A recorded limitation of `tools/citation_sweep.py`, so nobody "fixes" a correct citation

Run against this article, the sweep reports **11 failures, all of them false**, verified
line-by-line by direct read at STORY-197 acceptance and re-counted at review:

- Two cite `code-boundary-discipline.md`, a **memory file outside the repo** — correctly absent, not
  a broken citation.
- **Three are self-inflicted by this very section**, which quotes three of the real failures by
  bare filename for readability; the sweep's regex matches those mentions as fresh citations and
  they fail as "file does not exist". The count was written as 8 BEFORE this section existed and
  was not re-run afterwards — caught at spec review, and a fair hit under the same C2 rule this
  sprint applied to everyone else: a recorded count must be re-derived AFTER the prose that
  changes it.
- Six fail the **content-anchor** check while the cited lines are exactly right, because the anchor
  the sweep extracts is either a symbol NAME defined elsewhere in the file (`in_window`,
  `build_publisher`, `IngestService.ingest_observations`) or a multi-line construct rendered on one
  line in prose (`seed_dynamo.py:29-30`'s key dict, `run.py:182-184`'s three statements,
  `status_publisher.py:14-19`'s class-plus-signature).

The line-count half of the sweep is sound and the anchor half is a useful heuristic, but **an anchor
failure is a prompt to read the line, never evidence the citation is wrong.** A future story that
"fixes" these would be corrupting correct citations to satisfy a heuristic.

## History

- sprint-68 (STORY-205, sha bump): re-stamped `verified_sha` to `96f9048`. The commit
  that landed the Finding 1 rewrite (`e8768e8`) also touched
  `tools/demo_loop_gate/failure_path_reality_gate.py` (a `code_ref`) in the SAME
  commit, so the sha it could truthfully record (its own parent) was already stale
  the moment it landed — the same self-reference gap this article's own History
  shows STORY-197/199/202 hitting and re-stamping in a follow-up commit each time.
  No content changed here.
- sprint-68 (STORY-205): **Fixed and guarded ZR-8 Finding 1.** `composition/seed_dynamo.py`
  no longer hand-builds the `TOPOLOGY` partition's key schema; it now imports
  `app_item_key`/`component_item_key`/`signal_item_key` from the new
  `backend/src/adapters/persistence/topology_keys.py`, the single module
  `DynamoComponentRepository` and `DynamoSignalRepository` also import for both key
  shapes (item-key dict and boto3 query condition). Added the standing guard
  `backend/tests/test_zone_layout.py::test_seed_dynamo_uses_shared_topology_key_schema`,
  shown RED twice (against the real pre-fix file, and again by a deliberate
  re-introduction post-fix; both reverted). Behavioural drift proof (AC2): the existing
  round-trip test `test_dynamo_seed.py::test_seed_topology_dynamo` is unchanged and,
  unmutated, was already green both before and after — it is evidence only alongside
  two recorded mutations: pre-fix, changing `DynamoComponentRepository`'s own inline
  `"COMPONENT#"` literal alone reddened it (seed and repository diverged); post-fix,
  changing the SAME prefix in `topology_keys.py` (the module both now import) left it
  green — seed_dynamo.py followed automatically, proving the duplication is gone rather
  than relocated. That same post-fix mutation reddened
  `test_dynamo_adapters.py:17,82`'s hand-built seed helpers, as expected (they bypass
  the shared module by design, to test the repositories in isolation) — recorded, not
  "fixed" into silence. Rewrote the Finding 1 paragraph, its Coverage verdict, the
  adjudication table row and the "why only two rules were mechanised" paragraph to
  past/mixed tense; repointed the two already-stale citations
  (`dynamo_component_repository.py`/`dynamo_signal_repository.py` line numbers STORY-199's
  pagination loops had displaced) and `failure_path_reality_gate.py`'s docstring to the
  new schema module. `docs/scrum/wiki/persistence-adapters.md` updated in step (see
  [[persistence-adapters]]). Finding 2 (`vendor_health.py`) is untouched, still
  `GUARDABLE-DEFERRED (STORY-204)`. verified_sha -> a5a2d68.
- sprint-67 (STORY-202 quality-review fix round): **MAJOR — the six `harness.py`
  AC8 site line numbers in the Fact below were the story's own PRE-edit AC8
  numbers** (`:540`/`:609`/`:736`/`:742`/`:743`/`:744`), copied forward despite
  AC8's own warning that this story's edits would shift them. Re-derived against
  HEAD by directly opening each line: `:546`
  (`f"env CONFIG_DIR={api_env[CONFIG_DIR_VAR]!r}"`), `:615`
  (`f"CONFIG_DIR={loop_env[CONFIG_DIR_VAR]!r}"`), `:743`
  (`result["config_dir_api"] = api_env[CONFIG_DIR_VAR]`), `:749`
  (`result["dynamo_endpoint_url"] = api_env[DYNAMO_ENDPOINT_URL_VAR]`), `:750`
  (`result["observations_table"] = api_env[DYNAMO_OBSERVATIONS_TABLE_VAR]`),
  `:751` (`result["control_table"] = api_env[DYNAMO_CONTROL_TABLE_VAR]`).
  Corrected in the Fact above, qualified "line numbers as of `1210374`" per this
  article's existing convention. `backend/tests/test_zr3_duplicate_declarations.py`'s
  `failure_path_reality_gate.py:149` adjudication reason (a separate file, not
  this article, but the same review round) also carried a stale cross-reference
  to `env_matrix.py:39` five lines after the same module's own docstring
  documented that collision re-keyed to `:49` — corrected there too.
  verified_sha -> `1a70f45`.
- sprint-67 (STORY-202 fix round): **the false "both files import all seven" claim
  corrected** (see the Fact above and the entry below) — measured at HEAD:
  `env_matrix.py` imports all seven, `harness.py` imports only the four it
  actually re-types as a dict key. Also landed AC4's two-sided mutation proof
  (rename `CONFIG_DIR_VAR`'s VALUE both at the pre-STORY-202 commit `6f872c3`
  and at HEAD, in an isolated `git worktree` for the pre-fix half, restored and
  `git diff` confirmed empty for the post-fix half): pre-fix, `env_matrix.py`'s
  hardcoded `"CONFIG_DIR"` literal and the renamed `settings.py` DISAGREE — the
  harness's `config/demo` value never reaches `load_settings()`, which silently
  falls back to the `config/apps` default; at HEAD, after the identical rename,
  both sides agree because they read the one shared `CONFIG_DIR_VAR` symbol. And
  re-derived AC9's collision count directly (`python tools/zr3_duplicate_sweep.py`
  at HEAD): **13**, matching the 15-minus-the-two-retired-`env_matrix.py`-entries
  arithmetic this rule's own Coverage verdict predicted — no discrepancy to
  report this time (contrast the earlier "101, not 105" measurement above).
  verified_sha -> `3c0cdeb`.
- sprint-67 (STORY-202): fixed the seven env-var-NAME collisions ZR-3's own
  measurement found in `tools/demo_loop_gate/env_matrix.py` (5) and
  `tools/demo_loop_gate/harness.py` (6, of which 2 — the Statuspage credential
  keys — were the pre-existing adjudicated violations; the other 4 arose ONLY
  because this story's own fix (promoting `settings.py`'s five function-body
  literals to module constants) made them newly-declared shape-i values, per
  `test_zr3_duplicate_declarations.py`'s own module docstring). `env_matrix.py`
  imports all SEVEN constants (it sets all seven as child-env dict keys);
  `harness.py` imports only the FOUR it actually re-types as a dict key
  (`CONFIG_DIR_VAR`, `DYNAMO_CONTROL_TABLE_VAR`, `DYNAMO_ENDPOINT_URL_VAR`,
  `DYNAMO_OBSERVATIONS_TABLE_VAR`) — it never re-types `AWS_REGION`/
  `STATUSPAGE_PAGE_ID`/`STATUSPAGE_API_KEY` as a literal dict key anywhere, so
  there is nothing there for it to import. Both from
  `backend/src/composition/settings.py` rather than re-declaring the key
  names. (An earlier draft of this History entry and the Fact above both said
  "both files import all seven" — false at HEAD; corrected in the STORY-202
  fix round.) `_ADJUDICATED`'s two `env_matrix.py`
  `MUST-IMPORT-FROM-SRC` entries (`:75`, `:77`) were REMOVED (fixed, not
  displaced); five entries STORY-202's own edits displaced without retiring were
  RE-KEYED with their reason text preserved (`env_matrix.py` `:39`->`:49`;
  `harness.py` `:747`->`:754`, `:750`->`:757`, `:903`->`:910`, `:964`->`:971`).
  Sweep count: 15 -> 13 (the two retired entries); the remaining 4
  `MUST-IMPORT-FROM-SRC` entries are now filed solely to STORY-203 (VALUE
  duplication, not key-NAME duplication — the distinction STORY-202's own scope
  turned on). verified_sha -> `1dc1c73`.
- sprint-67 (STORY-199 fix round, quality review): **FACT CORRECTION, not a bare
  re-stamp.** The ZR-7 finding paragraph stated the hot-path cost backwards: it read
  that `is_under_maintenance` "never scan[s] the rest of the GSI partition on the
  common not-under-maintenance path". That is inverted — early-return-on-match only
  ever saves work on the (rare) under-maintenance path; the not-under-maintenance path
  (the common one, the one `decide` takes every cycle) is the one that reads the
  ENTIRE `MAINT` partition, because `False` is returned only once `LastEvaluatedKey`
  is exhausted. Corrected to state the true, asymmetric cost — the common path is the
  expensive one and it grows with maintenance-window history forever. The
  implementation is unchanged and correct; only this Fact's description of its cost
  was wrong. Also fixed the ZR-7 adjudication row, which named `is_under_maintenance`
  as the method used for the recorded mutation proof when the History entry (and the
  actual evidence) both say `list_components`. verified_sha -> fe8df72.
- sprint-67 (STORY-200 fix round, quality review): **MAJOR — the ZR-6 adjudication row claimed
  mechanical enforcement that does not exist.** It read `ENFORCED-BY
  backend/tests/test_approval.py::test_approval_service_decide_rejects_action_outside_approved_or_rejected`
  and closed "only this one, now-fixed instance is pinned" — disproved by mutation: reverting the
  ENTIRE ZR-6 fix (port back to `action: str`, fake back to `str`, adapter back to `if action ==
  "approved":`) leaves the full suite at 696 passed, IDENTICAL to HEAD. The named test pins the new
  2-member `{APPROVED, REJECTED}` SUBSET guard; it detects nothing about the port's TYPE. Corrected
  to `FIXED (STORY-200, sprint-67) — NO STANDING GUARD`, stating plainly that the instance is fixed,
  the subset is pinned by that one test, and the port-typing regression itself is unguarded — a
  future story could re-widen the port back to `str` with a fully green gate. Also fixed the
  contradicting "why only two rules were mechanised" paragraph nine lines below the table, which
  still listed ZR-6 as present-tense "blocked behind a fix or a design decision" in the same commit
  that (incorrectly) marked it `ENFORCED-BY`. verified_sha -> 013f344.
- sprint-67 (STORY-200): landed the ZR-6 fix. `record_approval_event`'s port
  signature now types `action: ProposalState` (decision (a), the sibling method's
  type — not a narrower type; the story file's "design decision" section records
  the full reasoning and an explicit expiry condition). The adapter,
  `DynamoProposalRepository.record_approval_event`, now compares by enum identity
  (`action is ProposalState.APPROVED`), with `.value` used explicitly at both write
  sites (the `sk` f-string and the `"action"` item attribute) — `ProposalState` is
  `class ProposalState(str, Enum)`, a str MIXIN not `StrEnum`, so on Python 3.13 an
  f-string over the bare member renders `"ProposalState.APPROVED"`, not
  `"approved"`; omitting `.value` at the `sk` site was confirmed to corrupt every
  approval event's sort key (reproduced as an actual test failure before the fix,
  not just reasoned about). The "3 invalid members" gap is closed with
  `ApprovalService._decide` raising `InvalidApprovalActionError` for any `to_state`
  outside `{APPROVED, REJECTED}` — deliberately NEW validation, since
  `is_valid_transition` admits any non-OPEN target and does not constrain this
  narrower set. Mutation-proven: changing `ProposalState.APPROVED`'s value (not
  its name) trips
  `test_dynamo_proposal_repository.py::test_dynamo_proposal_repository_record_approval_event`
  (the event item becomes unreadable at its expected sort key); restored, `git diff`
  empty. `STORY-198` was subsumed rather than landed separately (both would have
  edited the same three lines twice). verified_sha -> d469d2c.
- sprint-67 (STORY-199): landed the ZR-7 fix. All five findings (`is_under_maintenance`,
  `list_windows`, `list_components`, `list_signals`, `list_open`) now loop on
  `LastEvaluatedKey`; `is_under_maintenance` short-circuits `True` on first match and
  returns `False` only once `LastEvaluatedKey` is exhausted, never on an
  empty-after-filter page. `test_zr7_pagination_guard.py`'s `_EXEMPTIONS` dropped from
  six entries to one (the `dynamo_publication_repository.py:53` `PERMANENT` entry for
  `list_recent`, unaffected). Mutation-proven: removing `list_components`'s loop trips
  both the guard's unexempted-violation check and its own AC2 pagination test; restored,
  `git diff` empty. verified_sha -> 460d3ee.
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

- sprint-66 (STORY-195 quality-review fix round, 2026-07-31): added `ZR-6` and `ZR-7`,
  neither anticipated at STORY-194 planning. An independent audit of STORY-195's own
  footprint (46 of the 58 files it read) found: (1) STORY-195 had verdicted
  `core/ports/proposal_repository.py` `CLEAN` while separately quoting its own
  `action: str` line as the explanation for an adapter-level "catalogue gap" (`GAP-1`)
  — the port signature leaking a primitive where `ProposalState` already exists and is
  used correctly one method away is the ROOT CAUSE, not the adapter's literal
  comparison, and is now scored as its own `ZR-6` finding (`MAJOR`); (2) a genuine,
  unreported production defect — `dynamo_maintenance_repository.py::is_under_maintenance`
  and four sibling `list_*` methods pair an unbounded DynamoDB `query` with a
  post-read filter/no loop, silently truncating past a 1 MB page against a port
  contract that promises "all" — now `ZR-7` (`MAJOR`). Both rules are `GUARDABLE`
  only partially, with the false-positive risk stated honestly in each rule's own
  Coverage verdict, per the same discipline ZR-1/ZR-2/ZR-3 already established. Full
  detail, the fix stories these findings were filed as, and the re-derivation
  commands are in `docs/scrum/sprints/2026-07-31-sprint-66/audit-core-adapters.md`.
  Also corrected in passing (found by the fix round's strengthened, content-anchor
  citation sweep — see that report §7): the ZR-3 measurement note's bare-filename
  citation for the `settings.py` field defaults (no directory prefix) widened to the
  full repo-relative `backend/src/composition/settings.py:21-22`, matching this
  article's own full-path convention everywhere else.

- sprint-66 (STORY-196 quality-review fix round, 2026-07-31): added `ZR-8`, from an
  independent audit of STORY-196's own footprint (all 13 `composition/` modules,
  `api/dependencies.py`, six `service.py` files, and the `tools/` boundary crossers)
  that found the audit's biggest miss: `composition/seed_dynamo.py` hand-builds the
  SAME DynamoDB key schema `DynamoComponentRepository`/`DynamoSignalRepository`
  already own — raw `boto3` persistence from the composition zone, a third
  declaration of one schema on the boot path of both composition roots, which had
  already drifted once (`tools/demo_loop_gate/failure_path_reality_gate.py:163-172`'s
  own docstring records it) and which `docs/scrum/wiki/persistence-adapters.md`
  already treats as adapter-adjacent in its own Facts. STORY-196's original report
  had verdicted `seed_dynamo.py` `CLEAN` under a false generalisation ("pure wiring —
  every branch routes to a named core service/query/domain type"), which is untrue of
  `seed_dynamo.py` (routes to `boto3`'s Table API) and of `composition/dynamo.py`
  (routes to `boto3.resource`) alike — the SAME bulk-`CLEAN`-overstatement class
  STORY-196's own report criticises STORY-195 for. `ZR-8` generalizes `GAP-2`
  (`composition/vendor_health.py` duplicating a DQL query builder without its
  validation, STORY-196's original finding) and this new `seed_dynamo.py` finding
  under one statement: storage/vendor mechanics live in exactly one adapter: another
  zone calls it rather than re-implementing it — legal by every one of the eight
  `lint-imports` contracts, since they check import edges, never reuse-vs-rederive.
  Filed as `STORY-205`. Full detail and re-derivation commands:
  `docs/scrum/sprints/2026-07-31-sprint-66/audit-api-composition-tools.md`.
