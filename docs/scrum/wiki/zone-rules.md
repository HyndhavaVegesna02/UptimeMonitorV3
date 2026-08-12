---
title: Zone-intent rule catalogue — the boundary rules the nine contracts cannot see
code_refs: [backend/src/adapters/inbound/dynatrace/adapter.py, backend/src/core/services/ingest_service.py, backend/src/core/domain/signal.py, backend/src/core/ports/status_publisher.py, backend/src/adapters/outbound/statuspage/__init__.py, backend/src/adapters/inbound/dynatrace/health_mapping.py, tools/demo_engine/assumed_failure_codes.py, backend/src/core/domain/publication.py, backend/src/core/domain/component.py, backend/src/core/ports/component_repository.py, backend/src/core/ports/observation_repository.py, backend/src/core/ports/__init__.py, backend/src/core/ports/signal_ingest.py, tools/demo_loop_gate/harness.py, tools/demo_loop_gate/env_matrix.py, backend/src/composition/settings.py, backend/src/composition/run.py, backend/src/composition/app.py, backend/tests/test_zone_layout.py, backend/src/api/v1/health/controller.py, backend/src/api/v1/decisions/__init__.py, backend/src/adapters/persistence/dynamo_observation_repository.py, backend/src/core/ports/proposal_repository.py, backend/src/adapters/persistence/dynamo_proposal_repository.py, backend/src/core/services/approval.py, backend/src/core/domain/proposal.py, backend/tests/test_approval.py, backend/src/core/ports/maintenance_repository.py, backend/src/adapters/persistence/dynamo_maintenance_repository.py, backend/src/adapters/persistence/dynamo_component_repository.py, backend/src/core/ports/signal_repository.py, backend/src/adapters/persistence/dynamo_signal_repository.py, backend/src/composition/seed_dynamo.py, backend/src/adapters/persistence/topology_keys.py, backend/tests/test_topology_keys.py, backend/src/composition/vendor_health.py, backend/src/adapters/inbound/dynatrace/query.py, tools/demo_loop_gate/failure_path_reality_gate.py, backend/tests/test_dynamo_maintenance_repository.py, backend/tests/test_vendor_health.py, backend/tests/test_dynatrace_adapter.py, backend/tests/test_zr3_duplicate_declarations.py, backend/tests/demo_loop_gate/test_harness_assertions.py, backend/tests/test_live_secrets.py, backend/tests/test_demo_fleet_config.py, scripts/seed_topology.py, tools/zr3_duplicate_sweep.py]
verified_sha: b8e22d2
verified_sprint: sprint-69
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
# nine import-linter contracts — this article LINKS to that article for the
# mechanical set instead of re-citing or restating it. Likewise
# `docs/scrum/wiki/api-five-file-convention.md` is referenced by wiki link syntax,
# never as a code_ref (it is docs, and `check_facts` already skips
# `docs/scrum/` paths as cross-references, not code citations).
---

## Purpose

The nine `lint-imports` contracts ([[architecture-boundary]]) check *import direction*
only. STORY-190 showed that an inbound adapter holding and calling a core persistence
port passed all eight contracts that existed at the time while being architecturally
wrong — `adapters` legally importing `core` is exactly what a translation-only adapter
does too, so the (then-eight) contracts could not distinguish "translates" from
"translates and persists." **STORY-206 closed exactly this gap** with a ninth contract,
`inbound-adapters-dont-persist` — see ZR-1's adjudication row below; the other rules
this article catalogues remain the sort no `lint-imports` contract sees. This article catalogues the
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
nine-contract citations. This article's job is everything below, which the contracts
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

### The gap — rules the nine contracts do not enforce

**ZR-1 note (STORY-206):** the ninth contract, `inbound-adapters-dont-persist`, now
enforces ZR-1 directly — see its adjudication row below. It is catalogued here
alongside ZR-2..ZR-8 because this section documents the rule's Statement, Source and
citations regardless of enforcement status; the row is the authoritative verdict.

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
  # Maintenance note (STORY-197; this contract landed by STORY-206): a newly
  # added repository/persistence port module MUST be appended to this list in
  # the SAME commit that adds it, or it is invisible to this guard.
  # `src.core.ports.signal_ingest` (the front door) and
  # `src.core.ports.clock`/`status_publisher` (not persistence) are
  # deliberately excluded — see the comment block above the contract.
  ```
  *(The block above mirrors the shipped contract comment. It is a spec
  reproduction, not a live quote — if the two drift, the build config is
  authoritative. This article deliberately cites no build-config path in its
  Facts; see the frontmatter comment for why.)*
  **An inbound adapter must import a port by its exact module — never the package
  form.** `backend/src/core/ports/__init__.py` re-exports every port, including all
  nine forbidden ones, and import-linter follows indirect chains by default, so
  `from src.core.ports import SignalIngestPort` (the package form, naming only the
  front door) still trips this contract on all nine forbidden modules at once —
  proven by mutation (STORY-206 rework: `Contracts: 8 kept, 1 broken`, all nine named
  via the `src.core.ports` re-export chain; reverted). Only
  `from src.core.ports.signal_ingest import SignalIngestPort` (the exact-module form)
  is KEPT (`Contracts: 9 kept, 0 broken`). Do not widen the contract with
  `allow_indirect_imports = true` to permit the package form — that would also blind
  the guard to the package-level form of `ObservationRepository` et al., which is the
  most likely shape of a real violation given 26 sites in this repo already use
  `from src.core.ports import X`.

  Verified 0 current violations. STORY-206 showed this RED by temporarily adding
  (then reverting) e.g. `from src.core.ports.observation_repository import
  ObservationRepository` to `backend/src/adapters/inbound/dynatrace/adapter.py` — even
  only as an unused type annotation, never called — and confirmed the contract tripped.

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
- **Fixed and guarded (STORY-203, sprint-68) — the last four `MUST-IMPORT-FROM-SRC`
  entries this rule adjudicated, zero remain.** `tools/demo_loop_gate/harness.py`'s
  defensive blocklist (`:762-775` at HEAD — a fix-round edit named each assert's failure
  message, widening the span from `:761-768`; STORY-215's own `935cd70` added one more
  import line to `harness.py`'s import block, shifting this span a further +1, from the
  `:761-774` this article previously, and at the time correctly, recorded) now compares
  the RESOLVED table name
  (read from the real `api_env`, unchanged) against
  `Settings.dynamo_observations_table`/`dynamo_control_table` — imported, not
  re-declared — on the blocklist's RIGHT-hand side only; replacing the LEFT-hand
  side (the resolved value) with the same import instead would turn the check into
  a tautology disconnected from the actual environment (demonstrated by mutation:
  `backend/tests/demo_loop_gate/test_harness_assertions.py`'s
  `test_assert_ac1_preconditions_blocklist_does_not_fire_on_fresh_table_names` goes
  RED under that exact mistake). The other two of the four —
  `tools/demo_loop_gate/env_matrix.py:49` and
  `tools/demo_loop_gate/failure_path_reality_gate.py:149` at the pre-fix commits
  (`e9cb8c8`/`691227f`; each fix's own import-block edit shifted the line by +1, to
  `:50`/`:150`) — each hardcoded
  `Settings.aws_region`'s `"us-east-1"` default a second time; both now import
  `Settings` and reference `Settings.aws_region`. `env_matrix.py`'s site shifted a
  further +2 at HEAD, to `:52` (STORY-215's `935cd70` added two more constants,
  `DYNATRACE_API_TOKEN_VAR`/`DYNATRACE_ENV_URL_VAR`, to the same import block);
  `failure_path_reality_gate.py` was untouched by that commit, so its site stays
  `:150` at HEAD. This is exactly why "no import
  edge between the declaring modules" was the WRONG exemption criterion: an import
  edge to a DIFFERENT symbol in the same zone (`harness.py:61` already imported
  `src.composition.config` before this fix) does not mean the colliding value was
  actually obtained from `src` — it would have falsely CLEARED a real duplicate.
  `tools/zr3_duplicate_sweep.py` measured **13 -> 9** colliding pairs across this
  fix; the remaining 9 are all `INDEPENDENT` (see the Measurement below; re-run at
  HEAD for this fix round, still 9).
- **A second compliant citation, added by the STORY-202 fix and widened by STORY-215 —
  the two files import DIFFERENT SUBSETS of the NINE, not both all nine.**
  **Corrected in this fix round (STORY-215 fix round): this Fact previously said SEVEN
  and FOUR — false at its own `verified_sha` (`b887883`), not merely stale by the time
  of this fix round, because `935cd70` (an ancestor of `b887883`) had already promoted
  `DYNATRACE_ENV_URL_VAR`/`DYNATRACE_API_TOKEN_VAR` and added both to `env_matrix.py`
  (one of them to `harness.py`) before this article's `verified_sha` was stamped over
  it.** `backend/src/composition/settings.py` now declares NINE `<NAME>_VAR` env-var-name
  constants: the original seven (`CONFIG_DIR_VAR`, `AWS_REGION_VAR`,
  `DYNAMO_OBSERVATIONS_TABLE_VAR`, `DYNAMO_CONTROL_TABLE_VAR`, `DYNAMO_ENDPOINT_URL_VAR`,
  `STATUSPAGE_PAGE_ID_VAR`, `STATUSPAGE_API_KEY_VAR`) plus `DYNATRACE_ENV_URL_VAR`/
  `DYNATRACE_API_TOKEN_VAR` (STORY-215 AC1).
  `tools/demo_loop_gate/env_matrix.py:17-28` imports all NINE — `AWS_REGION_VAR`,
  `CONFIG_DIR_VAR`, `DYNAMO_CONTROL_TABLE_VAR`, `DYNAMO_ENDPOINT_URL_VAR`,
  `DYNAMO_OBSERVATIONS_TABLE_VAR`, `DYNATRACE_API_TOKEN_VAR`, `DYNATRACE_ENV_URL_VAR`,
  `STATUSPAGE_API_KEY_VAR`, `STATUSPAGE_PAGE_ID_VAR` — because it sets all nine as
  child-env dict keys (`build_child_env`'s body,
  `tools/demo_loop_gate/env_matrix.py:76-90`).
  `tools/demo_loop_gate/harness.py:62-69` imports only the FIVE it actually
  re-types as a dict key, at its SEVEN re-type sites — re-derived directly against
  HEAD for this fix round (not carried forward from any commit message or prior wiki
  text): `:548` (`api_env[CONFIG_DIR_VAR]`, inside the API-launch evidence `print`),
  `:616` (`loop_env[DYNATRACE_ENV_URL_VAR]`, inside the loop-launch evidence `print`),
  `:617` (`loop_env[CONFIG_DIR_VAR]`, the same `print`), `:745`
  (`result["config_dir_api"] = api_env[CONFIG_DIR_VAR]`), `:751`
  (`result["dynamo_endpoint_url"] = api_env[DYNAMO_ENDPOINT_URL_VAR]`), `:752`
  (`result["observations_table"] = api_env[DYNAMO_OBSERVATIONS_TABLE_VAR]`), `:753`
  (`result["control_table"] = api_env[DYNAMO_CONTROL_TABLE_VAR]`) — the five imported
  symbols are `CONFIG_DIR_VAR`, `DYNAMO_CONTROL_TABLE_VAR`, `DYNAMO_ENDPOINT_URL_VAR`,
  `DYNAMO_OBSERVATIONS_TABLE_VAR`, `DYNATRACE_ENV_URL_VAR` — because
  `harness.py` never re-types `AWS_REGION`/`DYNATRACE_API_TOKEN`/`STATUSPAGE_PAGE_ID`/
  `STATUSPAGE_API_KEY` as a literal dict key anywhere (verified: `grep -n
  '"AWS_REGION"\|"DYNATRACE_API_TOKEN"\|"STATUSPAGE_PAGE_ID"\|"STATUSPAGE_API_KEY"'
  tools/demo_loop_gate/harness.py` returns zero hits), so there is nothing for it to
  import for those four. Both
  files use whichever subset they need as their env-dict keys, rather than
  re-declaring any of the nine env-var NAMES a second time — the same
  reuse-not-rederive shape as the `assumed_failure_codes.py` citation above,
  closing the collision this rule's Coverage verdict's own measurement (below)
  found before STORY-202 landed. **Five is the complete, correct count for
  `harness.py` at HEAD, not an undercount.**
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
  `harness.py`/`settings.py` violation (fixed at STORY-203, sprint-68; see above) was
  neither — `backend/src/composition/settings.py:21-22`
  is shape (ii) (a field default, not an UPPER_CASE module constant) and the `harness.py`
  side was a literal inside a FUNCTION BODY. So the 0 is an artifact of the first draft's
  too-narrow scope, NOT evidence that the tree is clean. Under the pinned scope as it now
  stands — both declaration shapes, and `tools/`-side literals anywhere including function
  bodies — the sweep MUST find such a case were one re-introduced. **That is the
  demonstration STORY-196 AC3 requires** ("shown capable of finding one" before an empty
  result elsewhere is accepted); STORY-203 AC6 reconfirmed it by re-introducing the fixed
  `harness.py` duplicate and watching the sweep-backed guard fail, naming that exact line,
  before reverting: if a sweep reports 0 while a real duplicate stands, the sweep is wrong,
  not the tree. **Note for the record:** this story's own
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
- **Why the nine `lint-imports` contracts pass it.** Import-linter checks import
  edges between modules, never a method signature's parameter types. `action: str`
  imported nothing at all — there was no edge to check — so this was invisible to
  every one of the nine contracts by construction, exactly like ZR-2's gap.
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
- **Why the nine `lint-imports` contracts pass it.** Import-linter checks import
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
  `adapters`, or calling `boto3` directly, is exactly the wiring privilege the nine
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
- **Finding 2 — FIXED at STORY-204 (sprint-68).** `composition/vendor_health.py` used to
  re-implement a fragment of `backend/src/adapters/inbound/dynatrace/query.py`'s
  `build_dql_query` query-building in its own `build_vendor_health_query`
  (formerly `backend/src/composition/vendor_health.py:40-53`), interpolating the SAME
  trusted `native_id` config value into a DQL string literal WITHOUT reusing the
  adapter's `InvalidNativeIdError` breaking-character validation (`GAP-2`, first
  reported STORY-196). A `native_id` containing a DQL-breaking character raised
  loudly, by name, the moment `build_dql_query` ran (the ingest path) — but
  `check_vendor_id_health` (`backend/src/composition/vendor_health.py:70-133`) runs
  FIRST, at loop startup, and would instead silently build a malformed query. **The
  fix (option (b), decided at refinement, the same shape as Finding 1's):** the
  builder itself moved into the adapter as `build_vendor_health_dql`
  (`backend/src/adapters/inbound/dynatrace/query.py:139-158`), sharing a new
  `_reject_dql_breaking_native_id` helper (`query.py:63-80`) with `build_dql_query`
  — the SAME validation, not a second copy of it — so a `native_id` misconfiguration
  is rejected identically on both paths. `composition/vendor_health.py` now imports
  and calls the adapter's builder instead of re-deriving it; it no longer builds any
  DQL string itself. The bounded-window constant `HEALTH_CHECK_WINDOW = "2h"` moved
  with the builder (`query.py:136`; made public in the STORY-204 fix round — the only
  private-**name** import across a module AND zone boundary in `backend/src`, under a
  leading-underscore-*symbol* reading; `composition/app.py:224` imports the private *package*
  `src.api.v1._shared.errors` across a zone boundary too, which is a private PACKAGE, not a
  private name). Full mechanism:
  `docs/scrum/sprints/2026-07-31-sprint-66/audit-api-composition-tools.md` §4.
- **Why the nine `lint-imports` contracts pass both.** `composition` legally
  importing/reaching `adapters` — or, in `seed_dynamo.py`'s case, calling `boto3`
  directly, which `adapters-independence` never restricts for `composition` — is
  EXACTLY the wiring permission the nine contracts grant the composition zone by
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
  **Finding 2's fix (STORY-204) took a stronger shape than a parallel assertion would
  have:** rather than only a guard that checks `composition/vendor_health.py` calls the
  adapter's validation, the builder itself moved into the adapter, and a guard also
  polices `composition/vendor_health.py` directly —
  `backend/tests/test_vendor_health.py::test_vendor_health_module_builds_no_dql_string_itself`
  (AC4) is the guard that proves ZR-8's own statement here: it asserts the three literal
  fragments `build_vendor_health_dql` assembles (`"fetch "`, `"| filter "`,
  `"| summarize "`) are absent from `inspect.getsource(vendor_health_module)`.
  **Its limit, proven by mutation, not merely asserted:** it is a literal-substring
  check on source text, not a semantic "did composition build DQL" rule — a re-derived
  builder using a spliced `fetch` constant, `"|filter "` (no space after the pipe), and
  `"\n".join(...)` instead of an f-string passes all three assertions untouched (shown
  on a scratch copy at quality review). That gap is acceptable because the DANGEROUS
  half is caught elsewhere: a re-derived builder that skips
  `_reject_dql_breaking_native_id`'s validation is caught by
  `backend/tests/test_vendor_health.py::test_check_vendor_id_health_rejects_native_id_with_dql_breaking_char`
  (parametrised over all four `_DQL_BREAKING_CHARS`) plus
  `backend/tests/test_dynatrace_adapter.py::test_build_vendor_health_dql_rejects_native_id_with_dql_breaking_char`,
  which pin the actual behaviour rather than the source text and were proven
  discriminating by their own RED run against pre-fix HEAD. Re-declaring
  `_DQL_BREAKING_CHARS` a second time is now structurally harder, not merely
  discouraged, because there is no second builder left to duplicate it into.

## Inference (synthesis, not verified)

The nine contracts plus `ZR-1..ZR-8` together are the audit's yardstick: every
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
| ZR-1 | `ENFORCED-BY inbound-adapters-dont-persist` | A ninth `lint-imports` contract (`pyproject.toml`, STORY-206) forbids `src.adapters.inbound` from importing any of the nine enumerated repository/watermark port modules, excluding the `signal_ingest` front door and `clock`/`status_publisher` (neither is persistence). **Shown RED**: temporarily adding `from src.core.ports.observation_repository import ObservationRepository` (an unused import) to `backend/src/adapters/inbound/dynatrace/adapter.py` tripped the import-boundary DoD command — exit 1, `inbound-adapters-dont-persist` BROKEN, naming the edge `src.adapters.inbound.dynatrace.adapter -> src.core.ports.observation_repository`; reverted, exit 0, `Contracts: 9 kept, 0 broken.`, `git diff` empty. **Residue, stated rather than hidden (two, not one):** (1) the `forbidden_modules` list's completeness — that a newly added persistence/repository port is appended to it in the SAME commit that adds the port — is maintained BY HAND until STORY-220 (sprint 70) lands the completeness test; a new port module added without updating this list is invisible to this guard. (2) **the front-door EXCLUSION binds only in the exact-module form.** `from src.core.ports.signal_ingest import SignalIngestPort` is KEPT; the package form `from src.core.ports import SignalIngestPort` is BROKEN today — not because the package form is forbidden, but because `core/ports/__init__.py` re-exports all nine forbidden modules, so the chain `adapter -> src.core.ports -> src.core.ports.<each>` exists. **That is a FALSE POSITIVE on the front door, and narrowing those re-exports would REMOVE it, not open a hole** — verified by mutation (STORY-206 rework, re-verified by the orchestrator 2026-08-06 in a scratch tree with `PYTHONPATH` pinned): with `__init__.py` narrowed to the three non-persistence ports, the package-form front-door import both imports cleanly and reports `9 kept, 0 broken`; and a forbidden port cannot be reached that way at all, because a name `__init__.py` does not import raises `ImportError` — dead code, not an escape. **The genuinely unguarded shape is a DYNAMIC re-export**: a PEP 562 `__getattr__` / `importlib` indirection in `__init__.py` resolves `ObservationRepository` at runtime while this contract reports `9 kept, 0 broken` — static analysis cannot follow it, so an inbound adapter could hold a repository port with a fully green gate. Nothing here guards that. Two measured qualifiers, so this is not read as more or less than it is: the dynamic hole requires the STATIC re-export of that port to be GONE (today's full `__init__.py` plus the same `__getattr__` still reports `8 kept, 1 broken` — there is something static left to follow); and narrowing is a real cleanup, not a free one, because eleven package-form import statements across `backend/src` and `backend/tests` name a repository symbol and would become `ImportError` (measured at sprint-69: api/dependencies, composition/app, composition/pull_loop, three core services, two api v1 services, tests/fakes, test_core_ports, test_ingest_service). Round-3 quality review reproduced every clause of this residue independently, in a scratch tree with `PYTHONPATH` pinned on the linter invocation itself. |
| ZR-2 | `GUARDABLE-DEFERRED (STORY-207)` | AST walk specified above, with its residue stated (string annotations, dynamically built identifiers). Tree is CLEAN — mutation proof required. |
| ZR-3 | `ENFORCED-BY backend/tests/test_zr3_duplicate_declarations.py` | Promotes the committed `tools/zr3_duplicate_sweep.py` to a standing test. **Shown RED** by injecting a new duplicate of `Settings.dynamo_observations_table`'s default into a non-excluded `tools/` module — reconfirmed by STORY-203 AC6's own re-introduce/revert mutation. **All four `MUST-IMPORT-FROM-SRC` entries this rule adjudicated are fixed as of STORY-203 (sprint-68); zero remain.** Green via a per-entry adjudication list, now entirely `INDEPENDENT` (9 entries) — a future genuine finding is still expected to be filed there, the same way these four were. |
| ZR-4 | `GUARDABLE-DEFERRED (STORY-208)` | An extension to `backend/tests/test_zone_layout.py`, which today asserts feature-SET equality but not the five-file SHAPE. `health` is the one enumerated exception. |
| ZR-5 | `GUARDABLE-DEFERRED (STORY-209)` for the code-level half; the operational half is `UNGUARDABLE` | A parity test can assert both roots resolve `CONFIG_DIR` only through `load_settings()`. It **cannot** guard the failure that actually caused the sprint-64 incident: the loop and the API are separate OS processes, each reading its own environment, and no single-process test sees across a process boundary. That half stays runbook discipline. |
| ZR-6 | `FIXED (STORY-200, sprint-67) — NO STANDING GUARD` | The one live violation this rule adjudicated is fixed: the port now types `record_approval_event`'s `action: ProposalState` (decision (a), not a narrower type — see the rule text above), and `ApprovalService._decide` raises `InvalidApprovalActionError` for any `to_state` outside `{APPROVED, REJECTED}`, closing the "3 invalid members" gap `is_valid_transition` does not cover — proven by `test_approval.py::test_approval_service_decide_rejects_action_outside_approved_or_rejected`. **That test pins the 2-member SUBSET GUARD, not the port's TYPE.** Mutation-checked: reverting the entire fix (port back to `action: str`, fake back to `str`, adapter back to `if action == "approved":`) leaves the full suite at 696 passed, identical to HEAD — nothing detects a ZR-6 regression. This is honest, not a gap left carelessly: ZR-6's own Coverage verdict (above) already states the general "port primitive stands in for an existing domain type" rule is `GUARDABLE` only as a reviewed lint warning, never a hard-failing contract, and this row now agrees with it instead of contradicting it. A future story could re-widen this port back to `str` with a fully green gate. |
| ZR-7 | `ENFORCED-BY backend/tests/test_zr7_pagination_guard.py` | Two tests. **Shown RED twice** at STORY-197, and again at STORY-199 (sprint-67): removing `list_components`'s `LastEvaluatedKey` loop (the recorded mutation proof) trips the unexempted-violation check, and its removal also fails that method's own AC2 pagination test. STORY-199 landed all five fixes (including `is_under_maintenance`) and removed the five matching exemptions (`460d3ee`); `_EXEMPTIONS` now holds exactly ONE entry — `dynamo_publication_repository.py:53`, `PERMANENT`, for `list_recent`'s stated `Limit=limit` bound. |
| ZR-8 | Finding 1: `ENFORCED-BY backend/tests/test_zone_layout.py::test_seed_dynamo_uses_shared_topology_key_schema` (STORY-205, sprint-68). Finding 2: `ENFORCED-BY backend/tests/test_vendor_health.py::test_vendor_health_module_builds_no_dql_string_itself` (AC4 — the guard that proves ZR-8's own statement, no DQL string construction outside the adapter) + `backend/tests/test_vendor_health.py::test_check_vendor_id_health_rejects_native_id_with_dql_breaking_char` + `backend/tests/test_dynatrace_adapter.py::test_build_vendor_health_dql_rejects_native_id_with_dql_breaking_char` (STORY-204, sprint-68) | **Finding 1 fixed and guarded.** `seed_dynamo.py` now obtains the topology key schema (both shapes: item-key dict and boto3 query condition) from `adapters/persistence/topology_keys.py`, the single module `DynamoComponentRepository`/`DynamoSignalRepository` also import — a THIRD declaration removed, not relocated. **Shown RED twice**: against the real pre-fix file (three hand-built sites, at `seed_dynamo.py:28/43/57` as they stood then) before the wiring landed, and again by deliberately re-introducing one hand-built key post-fix and watching the guard name that exact line; both reverted, `git diff` empty. The guard is SHAPE-narrow (this one file, this one dict shape) per its own Coverage verdict — it says nothing about Finding 2. **Finding 2 fixed and guarded.** `build_vendor_health_dql` now lives in `adapters/inbound/dynatrace/query.py`, sharing `_reject_dql_breaking_native_id` with `build_dql_query`; `composition/vendor_health.py` calls it and builds no DQL string of its own. **Shown RED**: the composition-level parametrised test (all four `_DQL_BREAKING_CHARS`) failed against real pre-fix HEAD with `Failed: DID NOT RAISE InvalidNativeIdError` — the probe silently built a malformed query instead of raising, exactly the defect this rule names; reverted to green by the fix, no code left mutated. |

**Why only two rules were mechanised (AC5's stopping rule, stated as a result).** ZR-3 and ZR-7 were
chosen because they are the two highest-severity rules with a **live violation to prove the guard RED
against** — ZR-7's five findings include a production defect that silently disables maintenance
suppression, and ZR-3's six include a credential-safety drift risk. Every other rule is either clean
(ZR-1, ZR-2, ZR-4 — provable only by mutation, so cheaper to land alongside its own story), has no
standing guard by design (ZR-5's operational half is `UNGUARDABLE` — no single-process test sees
across the two-OS-process boundary that actually caused the incident), or has no standing guard
because none was ever built for it: **ZR-6's one live instance was fixed at STORY-200 (sprint-67)
without a mechanised guard** — its adjudication row above records this plainly rather than claiming
one exists. **ZR-8's Finding 1 was fixed and given a mechanised guard at STORY-205 (sprint-68), and Finding 2
followed at STORY-204 (sprint-68)**, both after this paragraph's own "why only two" count was
written — no guard existed for either at STORY-197 landing time, which is what this paragraph
explains, and does not retroactively change. Both of ZR-8's findings are now fixed and guarded; no
live violation remains under this rule.

### A recorded limitation of `tools/citation_sweep.py`, so nobody "fixes" a correct citation

**Re-run for STORY-215's third fix round: 28 failures, all of them false** — one more
than the **27** the second fix round recorded, because that same fix round's own
AC5-vacuity clarification bullet added a further bare-filename mention
(`test_demo_fleet_config.py:219-232`) without re-running this count afterward — the
identical "count must be re-derived AFTER the prose that changes it" lapse this section
calls out against every fix round since STORY-199, now demonstrated against itself a
second time, one fix round later. Up from the **11** this section originally recorded at
STORY-197 acceptance. Categorised by direct read, not assumed from the pattern:

- Two cite `code-boundary-discipline.md`, a **memory file outside the repo** — correctly absent, not
  a broken citation.
- **Twenty-one are self-inflicted bare-filename mentions across this article's own History
  prose** (this section's own examples plus every fix-round bullet that quotes a real
  citation without its directory prefix for readability — `env_matrix.py:39/49`,
  `query.py:63-80/133/136/136-155`, `composition/app.py:224`,
  `dynamo_publication_repository.py:53`, `seed_dynamo.py:29-30`, `run.py:182-184`,
  `status_publisher.py:14-19`, `harness.py:61/615/616/754/761-774`,
  `test_demo_fleet_config.py:174/194/219-232/226-232`, `failure_path_reality_gate.py:149`); the
  sweep's regex matches each bare mention as a fresh citation and fails it as "file does
  not exist" even though the real, full-path citation elsewhere in the article is fine.
- **Five fail the content-anchor check** while the cited lines are exactly right, because the anchor
  the sweep extracts is either a symbol NAME defined elsewhere in the file
  (`IngestService.ingest_observations`, `list_open`, `build_publisher`) or a multi-line
  construct rendered on one line in prose (`run.py:182-184`'s three statements,
  `status_publisher.py:14-19`'s class-plus-signature).

The line-count half of the sweep is sound and the anchor half is a useful heuristic, but **an anchor
failure is a prompt to read the line, never evidence the citation is wrong.** A future story that
"fixes" these would be corrupting correct citations to satisfy a heuristic.

## History

- sprint-68 (STORY-215 third fix round, `verified_sha` bumped `b887883` -> `6ba2558`,
  named Facts re-read): the sweep flagged this article STALE again — `scripts/seed_topology.py`
  changed since `b887883` (the second fix round's comment reword, `7cd1d19`, +1 net line).
  `git diff --stat b887883..8da2f2e` across every file in this article's `code_refs`
  confirms `scripts/seed_topology.py` was the ONLY one that changed — so this article's
  sole affected Fact is the "fifth site" `scripts/seed_topology.py:25` `CONFIG_DIR` bullet
  above. Re-read directly against both the commit it makes a historical claim about and
  HEAD: the pre-fix claims (`os.environ.get("CONFIG_DIR", "config/apps")` at `:25`,
  `load_settings` imported at `:20`, called at `:34`) are frozen citations into `b887883^`
  and still read exactly that at that commit — the comment reword landed after AC4's
  restructure and never touched that earlier commit. The current-state claim ("now calls
  `load_settings()` first and uses `settings.config_dir`") is still true at HEAD too
  (`settings = load_settings()` at `:28`, `config = load_config(settings.config_dir)` at
  `:32`, both one line further down than at `b887883` itself — `:27`/`:31` — because of
  the SAME comment reword). That claim is prose, not a bare line citation, so it needed
  no text edit; only the frozen pre-fix historical citations above (`:25`, `:20`, `:34`,
  into `b887883^`) would have needed correcting had the comment reword touched anything
  before them in that earlier commit, which it didn't. No
  Fact changed; only this one block was re-read, so `verified_sha` moves to `6ba2558`
  (this fix round's own last commit) rather than being bumped blindly over the rest of
  the article.
  Also corrected, in the same commit: the `tools/citation_sweep.py` count section above
  ("A recorded limitation...") still read **27 failures / Twenty bare-filename mentions**
  — stale by one, because the immediately preceding fix round's own AC5-vacuity bullet
  added a further bare-filename mention (`test_demo_fleet_config.py:219-232`) without
  re-running this count afterward. Re-run: **28 failures, Twenty-one bare-filename
  mentions** (2 memory-file + 21 bare-filename + 5 anchor-heuristic = 28); the missing
  citation added to the named list. This is the same "count must be re-derived after the
  prose that changes it" lapse this section already calls out against every fix round
  since STORY-199 — now caught one fix round after it happened, not immediately.
- sprint-68 (STORY-215 second fix round): quality review returned two MAJORs against
  the bullet immediately below (the one written to document C3's third failure),
  both **verified against source before this fix landed**. This is a prose-only
  correction — no code changed, so no RED/GREEN evidence gate applies here; the
  two corrections are inline within that bullet (marked `**Corrected...**`), plus
  a clarifying clause on the AC5-vacuity bullet further down. Summary of what was
  wrong and what is now true, both re-derived against HEAD after the edit:
  (1) that bullet's closing line claimed `verified_sha` changed to "this commit's
  own parent" — `git show c752c14 -- docs/scrum/wiki/zone-rules.md` shows no
  `verified_sha` line touched at all; it is corrected to state plainly that
  `verified_sha` stays `b887883`, unchanged, and why that stamp is still accurate.
  (2) that bullet's shift arithmetic said `935cd70` alone shifted the six stale
  citations by +1; the real shift is +2, cumulative across two stories — STORY-203's
  own `1d43b1b` shifted them +1 first (before STORY-215 touched the file), and
  STORY-203's own wiki commit (`37d20c0`) then stamped `verified_sha` straight onto
  `1d43b1b`, the very commit that had just broken them; `935cd70` added the second
  +1. Corrected to name both stories and both shifts, not STORY-215 alone.
- sprint-68 (STORY-215 fix round): **MAJOR — the `verified_sha` bump in the STORY-215
  landing commit (`7fb87fe`) certified a ZR-3 Fact this same story's own earlier commit
  (`935cd70`) had already made false, and the false Fact was STILL false at the sha the
  bump pointed to (`b887883`), not merely stale by the time it was read.** The "second
  compliant citation" Fact claimed `env_matrix.py` "imports all SEVEN" and `harness.py`
  "imports only the FOUR" it re-types as a dict key, at six named sites. At HEAD (and at
  `b887883`, since `935cd70` is its ancestor): `settings.py` declares NINE `<NAME>_VAR`
  constants (not seven — `935cd70` added `DYNATRACE_ENV_URL_VAR`/`DYNATRACE_API_TOKEN_VAR`
  in the SAME commit), `env_matrix.py` imports all nine, and `harness.py` imports FIVE
  (not four — `DYNATRACE_ENV_URL_VAR`), at SEVEN re-type sites (not six), none of which
  the six OLD cited line numbers (`:546`, `:615`, `:743`, `:749`, `:750`, `:751`) still
  point at, and the true shift is **+2, cumulative across two stories, not the +1 a
  prior version of this very bullet attributed to `935cd70` alone.** Re-derived by
  walking each site through three commits — `1210374` (STORY-202, the numbers as
  originally cited and correct), `1d43b1b` (STORY-203's own harness.py import-block
  edit), and HEAD (`935cd70`, STORY-215's import-block edit):
  `:546`->`:547`->`:548`, `:615`->`:616`->`:617`, `:743`->`:744`->`:745`,
  `:749`->`:750`->`:751`, `:750`->`:751`->`:752`, `:751`->`:752`->`:753` — every site
  shifted +1 at `1d43b1b` and +1 again at `935cd70`. **`1d43b1b` predates STORY-215
  entirely**: `git show 1d43b1b:tools/demo_loop_gate/harness.py | sed -n '546p'`
  prints `f"API (uvicorn) subprocess launched, pid={api_proc.pid}, "` — not the
  CONFIG_DIR re-type site — so these six citations were already false the moment
  STORY-203's `1d43b1b` landed, before STORY-215 touched the file at all. **And
  STORY-203 stamped `verified_sha` over that falseness itself**: its own wiki
  blast-radius commit, `37d20c0`, bumped `verified_sha` straight to `1d43b1b` —
  the very commit whose edit had just shifted these six sites — without noticing
  the untouched "second compliant citation" Fact's six line numbers no longer
  pointed at what they claimed. This is not solely STORY-215's doing: STORY-215's
  `935cd70` added the second +1 on top of a Fact STORY-203 had already broken and
  already certified as re-read. Because `yt_wiki.py`
  computes staleness as git arithmetic against `verified_sha`, bumping it to `b887883`
  told the tool the ENTIRE article had been re-read against that sha, so the sweep
  reported CLEAN over a Fact that was false at that exact sha — the same defect class
  as STORY-204's MAJOR 2 (an article re-stamped over a Fact the implementer had already
  flagged as wrong), and the third instance of it this sprint. **Fixed**: the "second
  compliant citation" Fact rewritten to NINE/FIVE with all seven re-type sites
  re-derived directly against HEAD (`:548`, `:616`, `:617`, `:745`, `:751`, `:752`,
  `:753`); the "Fixed and guarded (STORY-203)" Fact's own two stale spans corrected
  (`harness.py`'s blocklist `:761-774`->`:762-775`; `env_matrix.py`'s `Settings.aws_region`
  site `:50`->`:52`, further shifted by `935cd70`'s two added imports;
  `failure_path_reality_gate.py`'s site untouched, still `:150`); and three more stale
  citations this same commit's line-shifts produced, found by re-deriving the WHOLE
  ZR-3 section rather than spot-fixing only the ones named — `env_matrix.py:82,84`
  corrected to `:84,86`, `harness.py:615` corrected to `:616` (both in the main
  STORY-215 History bullet below), and `test_demo_fleet_config.py:174`/`:206-212`
  corrected to `:194`/`:226-232` (the AC5 mutation citations, shifted by the SAME
  story's separate `61152a3` commit, +20 net lines). **Re-verified, not re-stamped
  blindly, this time**: every `file:line` citation in the ZR-3 section was re-opened
  and its content read directly against HEAD before this bullet was written — see the
  full re-derivation list in the STORY-215 implementer's report. Also re-checked (not
  re-stamped): `demo-engine.md`, the other article `7fb87fe` bumped `verified_sha` on —
  no content-affecting drift found; see that article's own History for what was
  actually re-read. **A CLEAN `yt_wiki.py sweep` after this fix is evidence only that
  `verified_sha` is not behind — it is not evidence any Fact is true; that can only
  come from actually re-reading the cited lines, which is what this bullet records
  happening.** `verified_sha` is **NOT changed by this commit (`c752c14`)** — it
  stays `b887883`, set by `7fb87fe`. That stamp remains accurate for what it
  actually certifies (code drift, not prose correctness): `git diff b887883
  c752c14 --stat` touches only `docs/scrum/wiki/demo-engine.md`,
  `docs/scrum/wiki/zone-rules.md` and `.scrum/sprint-current.yaml` — no file in
  this article's `code_refs` changed between `b887883` and this commit, so the
  sha is still the right one to diff FROM. What `b887883` never certified, and
  what re-bumping it here would have wrongly implied, is that the Fact's PROSE
  was correct — it was false at `b887883` itself (per the MAJOR above), and this
  bullet fixes that falseness by re-reading the cited lines, not by moving the
  sha.
- sprint-68 (STORY-215): **Closed STORY-202's remainder — the two `DYNATRACE_*`
  env-var NAMES, plus a third and fourth `CONFIG_DIR` reader the sweep cannot see at
  all.** `DYNATRACE_ENV_URL_VAR`/`DYNATRACE_API_TOKEN_VAR` promoted in `settings.py`
  (same `<NAME>_VAR` convention as the other seven), and `load_live_secrets` now reads
  through them; `tools/demo_loop_gate/env_matrix.py:84,86` and `harness.py:616` (a
  dict-key literal inside a `print`, not the f-string's own `"DYNATRACE_ENV_URL="`
  text, which does not match) import the constants instead of re-typing them —
  `grep -rn '"DYNATRACE_ENV_URL"\|"DYNATRACE_API_TOKEN"' tools/` now zero hits.
  **Corrected in the STORY-215 fix round: this bullet originally read `:82,84` and
  `:615`** — the commit message's own line numbers for the PRE-fix literal sites;
  this same commit's import-block insertion (+2 lines in `env_matrix.py`, +1 in
  `harness.py`) had already shifted the FIXED sites to `:84,86`/`:616` by the time
  this commit landed, so the bullet was wrong from the moment it was written, not
  merely stale by the time of this fix round.
  **Sweep count, re-derived at this story's own start commit and again after each
  edit:** 9 (start, matching STORY-203's post-fix count) -> 12 with ONLY the two
  constants declared and `tools/` left un-fixed (`test_zr3_sweep_finds_no_
  unadjudicated_collision` went RED, naming exactly the three sites above — no more,
  no fewer) -> 9 again once `tools/` was fixed in the same commit. Landing both
  together is why the net is 9 -> 9, not a story that appears to leave the guard
  broken. Adding the import line to `harness.py`'s existing `from
  src.composition.settings import (...)` block re-keyed the two surviving
  `INDEPENDENT` entries it had already re-keyed twice this sprint (STORY-202 then
  STORY-203): `:927` -> `:928`, `:988` -> `:989`; re-keyed in
  `test_zr3_duplicate_declarations.py`, reason text preserved, both ZR-3 guard tests
  re-verified green.
  **A fourth `MUST-IMPORT-FROM-SRC`-shaped site was found that this rule's own sweep
  cannot see and never adjudicated**, because `tools/zr3_duplicate_sweep.py:209-211`
  scans only `backend/src/` (declaring side) against `tools/` (consuming side) —
  `backend/tests/test_demo_fleet_config.py:163-164,168-169,199-202` re-typed
  `"CONFIG_DIR"`/`"DYNAMO_ENDPOINT_URL"`/`"STATUSPAGE_PAGE_ID"`/`"STATUSPAGE_API_KEY"`
  as literals in the `create_app()` publish-safety pair (STORY-176), the last two
  being the credential-name drift the "why only two rules were mechanised"
  paragraph below already names among ZR-3's credential-safety drift risk. Fixed by
  importing `CONFIG_DIR_VAR`/`DYNAMO_ENDPOINT_URL_VAR`/
  `STATUSPAGE_PAGE_ID_VAR`/`STATUSPAGE_API_KEY_VAR` — invisible to the sweep either
  way, so this fix is verified by AC5's mutation, not by a sweep count.
  `backend/tests/test_settings.py:30` (`assert CONFIG_DIR_VAR == "CONFIG_DIR"`) is
  the PIN, not a duplication, and was left untouched — a test asserting a constant's
  value is protection; a test re-typing the name to consume it is drift.
  **A fifth site, also outside the sweep's two scanned trees**:
  `scripts/seed_topology.py:25` read `CONFIG_DIR` via its own
  `os.environ.get("CONFIG_DIR", "config/apps")`, independently declaring both the
  name and the default a third time. Now calls `load_settings()` first and uses
  `settings.config_dir`; confirmed at execution that `load_settings` was already
  imported (`:20`) and called (`:34`), so this was a re-order, not a new dependency
  — the AC's escape hatch for an import obstacle did not apply and was not used.
  **AC5's two-sided mutation (renaming `CONFIG_DIR_VAR`'s VALUE in `settings.py`,
  run pre-fix in an isolated `git worktree` with `PYTHONPATH=<worktree>/backend`,
  `module.__file__` printed to prove the worktree tree ran):**
  `test_demo_fleet_config.py:194` (the demo-side assertion) went RED —
  `statuspage_mapping() = {'http-check': 'xdnywbx77npw'}`, delegate type
  `BestEffortPublisher` — a WORKING detector, not rescued by this story's fix; while
  `test_demo_fleet_config.py:226-232` (the live-side assertion) stayed GREEN, because
  its own literal sets `CONFIG_DIR=config/apps`, which is also the resolved default
  when the renamed var is unset — passing for the wrong reason regardless of what the
  variable is called. That vacuity is what the site-3/site-5 fixes above close **for
  the rename mutation** — AC5's definition of the fix. It is **not closed
  intrinsically**: with `CONFIG_DIR_VAR`'s setenv line deleted entirely,
  `load_settings()` resolves the unset var to its own default, `"config/apps"`,
  which `load_config` reads into the same `{'http-check': 'xdnywbx77npw'}` mapping
  `LIVE_CONFIG_DIR` (`config/apps`, absolute) also yields — so
  `test_demo_fleet_config.py:219-232` still passes with that line gone. No
  constant substitution can fix this; the test would have to assert against a
  `CONFIG_DIR` value that DIFFERS from the default to stop passing vacuously.
  **Corrected in the STORY-215 fix round: this bullet originally read `:174` and
  `:206-212`** — the exact lines at the pre-fix (`61152a3^`) commit the AC5 mutation
  ran against, which this bullet copied forward uncorrected even though the same
  story's own `61152a3` (AC3, +20 net lines to this file's docstring and import block)
  had already shifted them to `:194`/`:226-232` by the time this bullet was written.
  **No claim that the tools<->src name boundary is now fully closed**: this rule's
  own sweep is structurally blind to `backend/tests/` and `scripts/`, so a future
  re-typed name in either tree would not be caught by `test_zr3_sweep_finds_no_
  unadjudicated_collision` — only by a mutation proof like AC5's, which is not a
  standing guard (`ZR-5`'s STORY-209, sprint-69, is the nearest planned mechanisation,
  and it is scoped to `CONFIG_DIR` parity between the two composition roots, not a
  general `backend/tests/`/`scripts/` sweep widening). Added
  `backend/tests/test_live_secrets.py` to `code_refs` (it now holds the
  `DYNATRACE_*_VAR` pin this article's Compliant-citation reasoning depends on).
  verified_sha -> b887883 (this article's content commit is the direct child of
  that sha, the same self-reference gap STORY-197/199/202/203/205 hit before it).
- sprint-68 (STORY-203): **Fixed and guarded ZR-3's last four `MUST-IMPORT-FROM-SRC` entries;
  zero remain.** `env_matrix.py:49` and `failure_path_reality_gate.py:149` (pre-fix line
  numbers; each fix's own import-block edit shifted the line by +1, to `:50`/`:150` at HEAD)
  each hardcoded `Settings.aws_region`'s `"us-east-1"` default a second time; both now import
  `Settings` and reference `Settings.aws_region`. `harness.py:754`/`:757`'s defensive blocklist hardcoded
  `Settings.dynamo_observations_table`/`dynamo_control_table`'s defaults; fixed on the
  blocklist's RIGHT-hand side only (the LEFT stays the real `api_env` read) — replacing the
  LEFT-hand side too would turn the check into a tautology disconnected from the environment
  it exists to guard, demonstrated by mutation:
  `test_harness_assertions.py::test_assert_ac1_preconditions_blocklist_does_not_fire_on_fresh_table_names`
  went RED under that exact mistake (a bare `AssertionError` where `httpx.HTTPError` was
  expected), reverted, `git diff` empty. Adding `Settings` to `harness.py`'s existing import
  block shifted two surviving `INDEPENDENT` entries by +11 lines (`:910`->`:921`,
  `:971`->`:982`); re-keyed, reason text preserved. Sweep count: 13 -> 9 (re-derived at HEAD
  both before and after); the remaining 9 are all `INDEPENDENT`.
  **AC4's fifth, cross-representation case (`store.py`'s `VENDOR_HEALTH_WINDOW`, invisible to
  this sweep's literal-equality comparison) was a DECISION, not a fix**: its existing
  wire-contract justification (the window is part of the vendor wire contract the demo engine
  answers, not borrowed from `adapters/inbound/dynatrace/query.py`'s `HEALTH_CHECK_WINDOW`) is
  upheld, and `test_zr3_duplicate_declarations.py`'s entry rewritten from
  `MUST-IMPORT-FROM-SRC ... Fix: STORY-203` (which would have pointed at this same, now-closed
  story as an outstanding fix) to `INDEPENDENT`, citing
  `test_vendor_health_query.py::test_vendor_health_window_matches_the_composition_health_check_window`
  as the mechanical pin against silent divergence, rather than arguing from the docstring
  alone. **AC6 mutation proof (re-run for this article):** re-introduced the fixed
  `harness.py` duplicate (reverted the blocklist's right-hand side back to the literal
  `"uptime-observations"`) — `test_zr3_sweep_finds_no_unadjudicated_collision` failed, naming
  `tools/demo_loop_gate/harness.py:762` exactly; reverted, `git diff` empty. Rewrote the ZR-3
  Fact bullet (the "genuine, adjudicated violation" paragraph, now past tense), the Measurement
  bullet's stale present-tense "violation" reference, and the adjudication table row (all four
  `MUST-IMPORT-FROM-SRC` fixed, zero remain). Added `backend/tests/test_zr3_duplicate_declarations.py`
  and `backend/tests/demo_loop_gate/test_harness_assertions.py` to `code_refs` (both now hold
  Facts this article cites by name, the same reason `test_vendor_health.py` was added at
  STORY-204). verified_sha -> `1c07def` (this article's content commit is the direct child of
  that sha, the same self-reference gap STORY-197/199/202/205 hit before it).
- sprint-68 (STORY-203 fix round): a quality-review minor asked for a named failure message on
  each of the AC1(b) blocklist asserts (`harness.py:761-774` at HEAD, widened from `:761-768`) —
  every other assert in `_assert_ac1_preconditions` already carried one. That edit added lines
  inside the function, shifting the two `INDEPENDENT` entries the bullet above re-keyed to
  `:921`/`:982` a further +6 lines each, to `:927`/`:988`; re-keyed again in
  `test_zr3_duplicate_declarations.py`, reason text preserved, `test_zr3_adjudications_are_still_current`
  and `test_zr3_sweep_finds_no_unadjudicated_collision` both re-verified green. **This fix round
  also missed constraint C3 once**: `zone-rules.md`'s ZR-3 update (this article, `3ab9c9b`) landed
  after the code fixes it describes (`e9cb8c8`, `691227f`, `db949c8`) and after `1c07def`'s own
  ledger rewrite — at least two committed states (`92241bd`, `1c07def`) carried this article still
  asserting a live violation the tree had already fixed. Recorded plainly in
  `docs/scrum/stories/STORY-203-tools-import-shared-literals.md`'s History per PO direction; not
  rewritten, and AC7 is not claimed MET. verified_sha -> `b68165c` (this article's content
  commit is the direct child of that sha, the same self-reference gap noted above).
- sprint-68 (STORY-204 third fix round): the second fix round fixed the `query.py:133`->`:136`
  single-point citation (below) but missed a DIFFERENT stale pattern in Finding 2's own body: the
  `build_vendor_health_dql` whole-function citation, `query.py:136-155`, was that span BEFORE the
  fix round's 3-line "PUBLIC" comment insertion and needed the same +3 shift, to `:139-158` —
  corrected below. Found by re-deriving every `query.py` citation in the repo against the real
  file, not by trusting a named list (a named four-site list given for this round was itself
  incomplete). No Fact's substance changed; citation-only. verified_sha -> 81a1351 (this article's
  content commit is the direct child of that sha).
- sprint-68 (STORY-204): **Fixed and guarded ZR-8 Finding 2 — the second and final live
  violation this rule adjudicated.** `composition/vendor_health.py` no longer builds any DQL
  string; `build_vendor_health_query` relocated into
  `backend/src/adapters/inbound/dynatrace/query.py` as `build_vendor_health_dql`, sharing the new
  `_reject_dql_breaking_native_id` helper with `build_dql_query` (extracted from the latter's own
  inline check, not a second copy) — so a `native_id` containing any of the four
  `_DQL_BREAKING_CHARS` now raises `InvalidNativeIdError` identically on both the ingest path and
  the vendor-health probe path, which previously silently built a malformed query. **Shown RED**:
  the new parametrised composition-level test
  (`test_vendor_health.py::test_check_vendor_id_health_rejects_native_id_with_dql_breaking_char`,
  all four breaking characters) failed against real pre-fix HEAD with
  `Failed: DID NOT RAISE InvalidNativeIdError` for every case; green after the fix, no code left
  mutated. Rewrote Finding 2's body to past tense, its Coverage verdict (the guard is stronger than
  the "parallel assertion" shape this article originally proposed — the builder itself is gone from
  composition, not merely checked), the adjudication table row (both findings now
  `ENFORCED-BY`), and the "why only two rules were mechanised" paragraph, which had said Finding 2
  "remains live" — both of ZR-8's findings are now fixed and guarded; no live violation remains
  under this rule. Added `backend/tests/test_vendor_health.py` and
  `backend/tests/test_dynatrace_adapter.py` to `code_refs` (they now hold the guard tests this
  article cites by name, the same reason `test_zone_layout.py` was already a `code_ref` for
  Finding 1's guard). verified_sha -> c815ebe.
- sprint-68 (STORY-205 fix round): RE-VERIFIED, no content change. The sweep flagged
  `backend/src/adapters/persistence/topology_keys.py`, `backend/tests/test_topology_keys.py`
  and `backend/tests/test_zone_layout.py` (all `code_refs`) for four quality-review minor
  fixes: renaming the meta-test `test_seed_dynamo_owns_no_hand_built_topology_key` (this
  article never cited that name — it cites the real standing guard,
  `test_seed_dynamo_uses_shared_topology_key_schema`, which is unchanged); sorting
  `find_hand_built_topology_key_dicts`'s returned line numbers into source order (the
  Fact above only claims the guard "fails, naming the offending line" — true either way);
  making `TOPOLOGY_PK` private (`_TOPOLOGY_PK`, no consumer outside the module and its own
  test); and documenting the guard's blind spots in its own docstring (this article's
  Coverage verdict already says "narrow and per-instance... checks exactly this one file's
  exact shape", which the docstring addition is consistent with, not a correction to).
  Re-confirmed the guard still fires RED and names the offending lines after reintroducing
  a hand-built `pk`/`sk` dict into `seed_dynamo.py`; file restored, `git diff` empty.
  verified_sha -> d9a3f95.
- sprint-68 (STORY-205, sha bump): re-stamped `verified_sha` to `96f9048`. The commit
  that landed the Finding 1 rewrite (`e8768e8`) also touched
  `tools/demo_loop_gate/failure_path_reality_gate.py` (a `code_ref`) in the SAME
  commit, so the sha it could truthfully record (its own parent) was already stale
  the moment it landed — the same self-reference gap this article's own History
  shows STORY-197/199/202 hitting and re-stamping in a follow-up commit each time.
  No content changed here.
- sprint-68 (STORY-204 fix round): **AC7b problem 2 (spec review FAIL).** The adjudication row and
  Coverage verdict cited only the two validation-parity tests, never
  `test_vendor_health.py::test_vendor_health_module_builds_no_dql_string_itself` (AC4) — the guard
  that actually tests ZR-8's own statement ("vendor query-construction logic lives in exactly ONE
  adapter"). Worse, the Coverage verdict positively claimed "there is no DQL string construction
  left in `composition/vendor_health.py` for a guard to police" — false, since that guard exists and
  polices exactly that. Cited it in both the adjudication row and the Coverage verdict; deleted the
  false claim; disclosed the guard's limit (a literal-substring check, proven evadable by a
  re-derived builder using a spliced `fetch` constant, `"|filter "` without the space, and
  `"\n".join(...)` — the dangerous half, missing validation, is still caught by the behaviour
  test). Also updated `test_vendor_health.py`'s own docstring for the same guard, same disclosure,
  in the same commit (STORY-205's AC2 docstring-disclosure shape, applied here). Also fixed the
  run.py/vendor_health.py stale comment (`composition/run.py::main`,
  `composition/vendor_health.py::check_vendor_id_health`) both reviewers independently found — it
  claimed the probe "never raises"/"propagates identically to the ingest path"; recorded the real
  blast-radius asymmetry (ingest degrades one signal via `run_periodic`, the probe aborts `main()`
  entirely). code_refs already covered every file touched. verified_sha -> bfa5f77.
- sprint-68 (STORY-204 fix round, second pass): `_HEALTH_CHECK_WINDOW` made public
  (`HEALTH_CHECK_WINDOW`, an unrelated minor from the same fix round — the only private-**name**
  import across a module AND zone boundary in `backend/src`, under a leading-underscore-*symbol*
  reading). Finding 2's Fact above repointed to the new public name. verified_sha -> bfa5f77.
- sprint-68 (STORY-204 second fix round): fixed a stale line ref (`query.py:133` -> `:136`, moved
  by bfa5f77's added comment lines) in Finding 2's Fact above, and narrowed both "the only
  private-name import" occurrences in this article to the leading-underscore-*symbol* reading they
  actually hold under — `composition/app.py:224` imports the private *package*
  `src.api.v1._shared.errors` across the same kind of zone boundary, which is a private PACKAGE,
  not a private name. No file in this article's `code_refs` changed (prose-only correction).
- sprint-68 (STORY-204 second fix round): the sweep flagged `run.py` again. STORY-204's second fix
  round reordered (did not change the substance of) the vendor-id drift probe's call-site comment
  so its opening line states the fail-fast scope on its own (see [[dynatrace-adapter]]). The
  blast-radius asymmetry this article records (ingest degrades one signal via `run_periodic`, the
  probe aborts `main()` entirely) is unchanged. Re-verified only; no Fact changed. verified_sha ->
  d554227.
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
- sprint-69 (STORY-206, verified_sha bumped `6ba2558` -> `b8e22d2`): ZR-1's adjudication row
  flips `GUARDABLE-DEFERRED (STORY-206)` -> `` `ENFORCED-BY inbound-adapters-dont-persist` ``. The
  ninth `lint-imports` contract (`pyproject.toml`) is now real, shown RED by mutation and reverted
  (`git diff` empty) — see the row for the exact command output. Contract count of record moves
  8 -> 9 throughout this article's own general/current-tense prose (title, Purpose, ZR-6/ZR-7/ZR-8
  "why the contracts pass it" Facts, the closing Inference paragraph); the legend's "existing eight
  DoD commands" phrase (a DoD-COMMAND count, not a contract count) is unchanged by design, and
  dated History entries above keep whatever count was accurate at the sprint they describe. The
  Purpose section's STORY-190 example ("passed all eight ... that existed at the time") is likewise
  left as a historically-accurate count with a forward pointer to this story, rather than bumped to
  a now-false "passes all nine." `forbidden_modules`' own completeness (a newly added port appended
  in the same commit) remains hand-maintained until STORY-220 (sprint 70) — the row states this.
- sprint-69 (STORY-206 rework, quality review MAJOR-1/MINOR-3, verified_sha unchanged at
  `b8e22d2` — no code_ref moved, only this article's own prose was corrected): ZR-1's Coverage
  verdict stated the exact-module-import constraint positively for the first time — the package
  form (`from src.core.ports import SignalIngestPort`) is not itself forbidden but trips the
  contract today only because `core/ports/__init__.py`'s re-exports make it transitively import
  all nine forbidden modules at once; proven by mutation both directions (`8 kept, 1 broken` ->
  `9 kept, 0 broken`), both reverted, `git diff` empty. The adjudication row's single stated
  residue became TWO: the pre-existing hand-maintained-list residue is kept verbatim (not
  weakened — the PO's STORY-220 approval was conditioned on that sentence), and a second residue
  is added naming the exact-module-form dependency as a real, if currently harmless, gap. Also
  fixed: the Coverage verdict's "STORY-197 can show this RED... " was future tense and
  misattributed the mutation to STORY-197 (ZR-1's completeness-test story) rather than STORY-206
  (the story that actually ran it) — corrected to past tense, attributed to STORY-206.
