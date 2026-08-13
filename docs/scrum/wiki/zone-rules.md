---
title: Zone-intent rule catalogue — the boundary rules the nine contracts cannot see
code_refs: [backend/src/adapters/inbound/dynatrace/adapter.py, backend/src/core/services/ingest_service.py, backend/src/core/domain/signal.py, backend/src/core/ports/status_publisher.py, backend/src/adapters/outbound/statuspage/__init__.py, backend/src/adapters/inbound/dynatrace/health_mapping.py, tools/demo_engine/assumed_failure_codes.py, backend/src/core/domain/publication.py, backend/src/core/domain/component.py, backend/src/core/ports/component_repository.py, backend/src/core/ports/observation_repository.py, backend/src/core/ports/__init__.py, backend/src/core/ports/signal_ingest.py, tools/demo_loop_gate/harness.py, tools/demo_loop_gate/env_matrix.py, backend/src/composition/settings.py, backend/src/composition/run.py, backend/src/composition/app.py, backend/tests/test_zone_layout.py, backend/src/api/v1/health/controller.py, backend/src/api/v1/decisions/__init__.py, backend/src/adapters/persistence/dynamo_observation_repository.py, backend/src/core/ports/proposal_repository.py, backend/src/adapters/persistence/dynamo_proposal_repository.py, backend/src/core/services/approval.py, backend/src/core/domain/proposal.py, backend/tests/test_approval.py, backend/src/core/ports/maintenance_repository.py, backend/src/adapters/persistence/dynamo_maintenance_repository.py, backend/src/adapters/persistence/dynamo_component_repository.py, backend/src/core/ports/signal_repository.py, backend/src/adapters/persistence/dynamo_signal_repository.py, backend/src/composition/seed_dynamo.py, backend/src/adapters/persistence/topology_keys.py, backend/tests/test_topology_keys.py, backend/src/composition/vendor_health.py, backend/src/adapters/inbound/dynatrace/query.py, tools/demo_loop_gate/failure_path_reality_gate.py, backend/tests/test_dynamo_maintenance_repository.py, backend/tests/test_vendor_health.py, backend/tests/test_dynatrace_adapter.py, backend/tests/test_zr3_duplicate_declarations.py, backend/tests/demo_loop_gate/test_harness_assertions.py, backend/tests/test_live_secrets.py, backend/tests/test_demo_fleet_config.py, scripts/seed_topology.py, tools/zr3_duplicate_sweep.py, backend/tests/test_zr2_vendor_vocabulary.py, backend/tests/test_zr5_config_dir_parity.py, backend/tests/pagination_diagnostics.py]
tier: map
verified_sprint: sprint-69
status: verified
# tier: map, `verified_sha` dropped 2026-08-12 (yourteam 2.3.0): the staleness baseline is now
# this article's own last commit, so the stamp is derived and there is nothing to keep current.
# The 580-line `## History` moved to [[zone-rules-history]] (`tier: reference`) — see the
# pointer at the foot of this file. Everything that claims something about code as it stands
# now stayed HERE and is still swept.
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
# sprint-71 (STORY-201): re-verified after this article's code_ref
# `backend/tests/test_dynatrace_adapter.py` changed (a new clickpath
# require_field test, unrelated to any ZR rule). Confirmed the one line this
# article cites in that file -- test_build_vendor_health_dql_rejects_
# native_id_with_dql_breaking_char (ZR-8 Finding 2) -- is untouched and still
# exists at the cited name. No Fact in this article changed.
# sprint-71 (STORY-189): re-verified after this article's code_ref
# `composition/vendor_health.py` changed -- a false "logs nothing" docstring
# absolute corrected to state the code's actual behaviour (logs at INFO),
# line-count neutral. The ZR-8 Finding 2 citations here
# (`check_vendor_id_health`/`_extract_count`, `vendor_health.py:70-133`) are
# symbol- and range-based and untouched; the :70-133 bound still lands on the
# same two lines (def at :70, the warning branch's closing paren at :133) --
# confirmed after the edit. No Fact in this article changed.
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
- **Coverage verdict.** `ENFORCED-BY backend/tests/test_zr2_vendor_vocabulary.py::test_core_has_no_vendor_vocabulary_leak`
  (STORY-207) — a pytest test that parses every `core/` module with `ast` and asserts
  no detection-seed substring appears in: (1) `FunctionDef`/`AsyncFunctionDef`/
  `ClassDef` names; (2) `arg` names (positional, keyword-only, or otherwise); (3) `Name`
  nodes (identifier references, including type annotations written as bare names);
  (4) `ast.Attribute.attr` (attribute names, e.g. a hypothetical `.dynatrace_id`);
  (5) `ast.keyword.arg` (call-keyword names); (6) `ast.Constant` string/number values
  that are NOT the sole value of an `ast.Expr` statement (i.e. neither a real
  docstring nor the attribute-docstring idiom) — covering assignment right-hand sides
  and dict keys/values. This walk covers the rule's forbidden forms (identifier,
  attribute name, annotation/signature via `Name`/`Attribute`/`arg` nodes, and
  stored/dict-key data values) while correctly excluding both prose forms as
  compliant — proven in the compliant direction too by
  `test_compliant_prose_forms_are_not_flagged` (AC2), which shows the walk WOULD flag
  `signal.py`'s module docstring and `publication.py:66`'s attribute docstring with
  rule (6)'s exclusion disabled, and does not with it enabled. **Shown RED by
  mutation (AC5, STORY-207):** adding `dynatrace_code: str` to
  `backend/src/core/domain/component.py`'s `Component` model failed the guard naming
  the file, the line, and the node class (`Name`); reverted, `git diff` empty.
  **Residue this guard still cannot see — corrected here from an earlier, FALSE
  statement.** An earlier draft of this residue paragraph named
  `def f(x: "DynatraceRow")` and `getattr(obj, "dynatrace_" + suffix)` as escapes;
  neither actually escapes the six-rule walk above — both surface as rule (6)
  `Constant` string values (`'DynatraceRow'`, `'dynatrace_'`) and are caught, because
  neither is the sole value of an `Expr` statement. That text was written against an
  earlier, narrower walk (names/`arg`/`Name` only, before rule (6) existed) and was
  carried forward into the six-rule verdict without being re-derived — caught at
  STORY-207 plan verification (finding G8). **The TRUE residue:** this walk sees a
  string annotation or a dynamically-built identifier's string argument only as an
  opaque `ast.Constant` value, with no way to distinguish "this string names a type
  forward-reference or a runtime-constructed identifier" from "this string is
  comment-like prose" — and an identifier ASSEMBLED FROM FRAGMENTS carrying no whole
  seed token in a single `Constant` (e.g. `"dyna" + "trace_id"`, or a seed token split
  across an f-string's static and interpolated parts) is invisible to it, because no
  single node this walk inspects ever holds the complete token. **The `Provenance`
  carve-out (above) is NOT implemented by this walk** — `Provenance(system="dynatrace")`
  written inside `core/` would be flagged by rule (6) as an unexempted `Constant`
  argument; moot today because no such literal exists in `core/` and `Provenance`'s own
  definition carries no vendor token, so a test asserting it unflagged would be
  vacuous. The correct fix when that literal first appears is a narrow exemption for
  `Constant` arguments to a `Provenance(...)` call, never a widening of the `Expr`-sole
  exclusion and never deletion of the domain's one sanctioned vendor-data channel.
  `ENFORCED-BY` to this extent, with this residue stated: **ZR-2 may not be described
  anywhere as fully enforced.**

#### ZR-3 — a module-level constant shared across the `tools/` -> `backend/src/` one-way boundary is declared once, in `backend/src/`, and imported by `tools/` — never re-declared

- **Statement.** SCOPE, pinned (see the measurement below for why): a value DECLARED in
  `backend/src/` — in either of TWO declaration shapes, (i) a module-level named constant
  (an UPPER_CASE assignment target) or (ii) a **default on a settings/config field**
  (e.g. `backend/src/composition/settings.py:57-58`, re-keyed from `:21-22` by
  STORY-218's own `Settings`-docstring insertion, which displaced these two field
  defaults without changing their declared status) — whose value `tools/` also needs,
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
  defensive blocklist (`:772-785` at HEAD — re-keyed from `:762-775` by STORY-218's own
  AC6 comment edit above these asserts, correcting the "follows a future rename
  automatically" claim; before that, a fix-round edit named each assert's failure
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
  neither — `backend/src/composition/settings.py:57-58` (`:21-22` at the time of this
  measurement; re-keyed by STORY-218, see the Statement above)
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
  **(STORY-213, 2026-08-13):** the assertion itself is now self-diagnosing — wrapped in
  `PaginationSpy` (`backend/tests/pagination_diagnostics.py`) so a failure reports the observed page
  count and whether `LastEvaluatedKey` was still present when the loop exited, not just the bare
  `True`/`False` mismatch. The `assert True` this Fact cites is unchanged; only the failure message
  changed. A fix-round pass further keyed the message on page count, not LEK alone: `LastEvaluatedKey=True`
  is this repository's own loop stopping early (a regression); `=False` with exactly one page read is
  DynamoDB Local under-reporting that page's boundary; `=False` with more than one page read means the
  loop ran to exhaustion and the target component's window was never visible on the wire at all (GSI
  lag or a lost write, not a pagination defect) — the three causes render identically on `LastEvaluatedKey`
  alone but not on `page_count` too. Full detail: [[persistence-adapters]].
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
  **Re-affirmed 2026-08-13 (STORY-217, sprint-70 planning).** Re-derived by PORT IMPORT
  rather than the token grep the 2026-08-05 re-check used (that grep is retired: it
  cannot see a write method mentioning neither `topology` nor `APP#`, and its own hit
  count had already drifted from twelve to thirteen). Command run: `grep -rn "from
  src.core.ports" backend/src/core/services/` — the three services that import
  anything from `src.core.ports` (`approval.py`, `decide.py`, `ingest_service.py`)
  import exactly seven ports between them (`ClockPort`, `ObservationRepository`,
  `RejectedObservationRepository`, `SignalIngestPort`, `WatermarkRepository`,
  `ProposalRepository`, `StatusPublisherPort`); a follow-up `grep -rln
  "ComponentRepository\|SignalRepository" backend/src/core/services/` returns no
  matches (exit 1). Neither topology port — `ComponentRepository` (write-capable via
  `set_status`) nor `SignalRepository` (read-only) — is imported by any core service.
  **The expiry condition has NOT fired. Option (b) stands until it does.**
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

**This table is authoritative.** Each rule carries the verdict(s) that actually apply to it — usually
exactly one, but a rule whose own Coverage verdict already splits into two independently-adjudicated
halves carries one verdict PER HALF, in the same cell (ZR-5 is that case: `ENFORCED-BY` for its
code-level half, `UNGUARDABLE` for its operational half — corrected here, STORY-209, from an earlier
version of this line that claimed "exactly one verdict" unconditionally while ZR-5's own row already
carried two). `ENFORCED-BY` means a guard exists, runs inside the existing eight DoD commands, and has
been **shown RED** (C3/A9) — never merely "is green". `GUARDABLE-DEFERRED` means the guard is
specified in the rule above and a named story will land it. `UNGUARDABLE` states the reason no
mechanical rung can hold it.

| Rule | Verdict | Detail |
| --- | --- | --- |
| ZR-1 | `ENFORCED-BY inbound-adapters-dont-persist` + `backend/tests/test_zr1_forbidden_list_completeness.py::test_forbidden_modules_matches_discovered_persistence_ports_exactly` | A ninth `lint-imports` contract (`pyproject.toml`, STORY-206) forbids `src.adapters.inbound` from importing any of the nine enumerated repository/watermark port modules, excluding the `signal_ingest` front door and `clock`/`status_publisher` (neither is persistence). **Shown RED**: temporarily adding `from src.core.ports.observation_repository import ObservationRepository` (an unused import) to `backend/src/adapters/inbound/dynatrace/adapter.py` tripped the import-boundary DoD command — exit 1, `inbound-adapters-dont-persist` BROKEN, naming the edge `src.adapters.inbound.dynatrace.adapter -> src.core.ports.observation_repository`; reverted, exit 0, `Contracts: 9 kept, 0 broken.`, `git diff` empty. **Residue, stated rather than hidden:** the list's completeness is now itself mechanically guarded — `backend/tests/test_zr1_forbidden_list_completeness.py::test_forbidden_modules_matches_discovered_persistence_ports_exactly` (STORY-220, sprint 70) asserts SET EQUALITY between this contract's `forbidden_modules` and the persistence ports discovered on disk under `backend/src/core/ports/` (every `*_repository.py` file plus `watermark.py`), shown RED by THREE mutations against the real tree, each reverted with `git diff` empty. Two were performed by the implementer (a new port added to disk without updating the list; an existing entry removed from the list) and BOTH land in the assertion's *first* branch — removing an entry from the contract while its file stays on disk produces the identical `On disk but not in the contract` shape as adding a file. **The second branch, `In the contract but not on disk`, was therefore never exercised by either**, and was proven separately by the orchestrator on 2026-08-13: adding `src.core.ports.ghost_repository` to the contract with no such file reds the test naming it under that branch, with the first branch empty. Recorded this way because the implementer disclosed the collision rather than letting 'both directions' stand unqualified. That test's own docstring states its remaining residue: a persistence port named following neither pattern is invisible to its discovery rule, as is a port that is persistence-shaped by that rule but is not actually persistence. The one residue this guard's own construction leaves: **the front-door EXCLUSION binds only in the exact-module form.** `from src.core.ports.signal_ingest import SignalIngestPort` is KEPT; the package form `from src.core.ports import SignalIngestPort` is BROKEN today — not because the package form is forbidden, but because `core/ports/__init__.py` re-exports all nine forbidden modules, so the chain `adapter -> src.core.ports -> src.core.ports.<each>` exists. **That is a FALSE POSITIVE on the front door, and narrowing those re-exports would REMOVE it, not open a hole** — verified by mutation (STORY-206 rework, re-verified by the orchestrator 2026-08-06 in a scratch tree with `PYTHONPATH` pinned): with `__init__.py` narrowed to the three non-persistence ports, the package-form front-door import both imports cleanly and reports `9 kept, 0 broken`; and a forbidden port cannot be reached that way at all, because a name `__init__.py` does not import raises `ImportError` — dead code, not an escape. **The genuinely unguarded shape is a DYNAMIC re-export**: a PEP 562 `__getattr__` / `importlib` indirection in `__init__.py` resolves `ObservationRepository` at runtime while this contract reports `9 kept, 0 broken` — static analysis cannot follow it, so an inbound adapter could hold a repository port with a fully green gate. Nothing here guards that. Two measured qualifiers, so this is not read as more or less than it is: the dynamic hole requires the STATIC re-export of that port to be GONE (today's full `__init__.py` plus the same `__getattr__` still reports `8 kept, 1 broken` — there is something static left to follow); and narrowing is a real cleanup, not a free one, because eleven package-form import statements across `backend/src` and `backend/tests` name a repository symbol and would become `ImportError` (measured at sprint-69: api/dependencies, composition/app, composition/pull_loop, three core services, two api v1 services, tests/fakes, test_core_ports, test_ingest_service). Round-3 quality review reproduced every clause of this residue independently, in a scratch tree with `PYTHONPATH` pinned on the linter invocation itself. |
| ZR-2 | `ENFORCED-BY backend/tests/test_zr2_vendor_vocabulary.py::test_core_has_no_vendor_vocabulary_leak` | The six-rule AST walk specified above (STORY-207). **Shown RED by mutation**: adding `dynatrace_code: str` to `backend/src/core/domain/component.py`'s `Component` model failed the guard naming the file, the line, and the node class (`Name`); reverted, `git diff` empty. **Shown compliant-direction too (AC2)**: a discrimination test proves the walk WOULD flag `signal.py`'s module docstring and `publication.py:66`'s attribute docstring with rule (6)'s `Expr`-sole exclusion disabled, and does not with it enabled — an over-triggering guard would be reverted, not obeyed by editing compliant code. **Extent, not more — two residues stated, not hidden:** (1) the TRUE residue (corrected from an earlier false statement, see the Coverage verdict above) — a string annotation or a dynamically-constructed identifier is seen only as an opaque `Constant`, and an identifier assembled from fragments carrying no whole seed token in one `Constant` is invisible; (2) the `Provenance` carve-out is NOT implemented — a future `Provenance(system="…")` literal inside `core/` will false-positive under rule (6); moot today (no such literal exists), fix is a narrow `Provenance(...)`-call exemption, never a wider exclusion or deleting the carve-out. **ZR-2 is not fully enforced.** |
| ZR-3 | `ENFORCED-BY backend/tests/test_zr3_duplicate_declarations.py` | Promotes the committed `tools/zr3_duplicate_sweep.py` to a standing test. **Shown RED** by injecting a new duplicate of `Settings.dynamo_observations_table`'s default into a non-excluded `tools/` module — reconfirmed by STORY-203 AC6's own re-introduce/revert mutation. **All four `MUST-IMPORT-FROM-SRC` entries this rule adjudicated are fixed as of STORY-203 (sprint-68); zero remain.** Green via a per-entry adjudication list, now entirely `INDEPENDENT` (13 entries — STORY-219, sprint 70, added `tools/citation_gate.py:53`'s coincidental `str.find` start-offset literal; STORY-212, sprint 70, added two more from the new `tools/evidence_check.py`; STORY-212's sprint-70 FIX ROUND added a third and re-keyed the other two for line shifts its own edits caused — `raw[2:]`'s slice bound, `len(parts) >= 2`'s minimum-token-count guard, and `_SELECTOR_DID_NOT_RUN_EXIT_CODES = (2, 3, 4, 5)`'s pytest exit-code tuple, all coincidental) — a future genuine finding is still expected to be filed there, the same way these four were. |
| ZR-4 | `ENFORCED-BY backend/tests/test_zone_layout.py::test_zone_layout_agreements` | STORY-208 extended the existing `test_zone_layout_agreements` (which already asserted feature-SET equality and router registration) with a per-feature five-file SHAPE assertion: for each feature `discover_features(v1_dir)` returns, except the literal exception set `{"health"}`, its `*.py` file set must equal exactly `{"__init__.py", "controller.py", "models.py", "validation.py", "service.py"}` (set equality via `assert_feature_five_file_shape`, not a superset check); the comparison is `*.py`-only, explicitly excluding `__pycache__/` and any other non-`.py` entry because it exists in every feature directory on any machine that has already run the suite. `health`'s exception cites its own docstring (`backend/src/api/v1/health/controller.py`) as the reason. A non-vacuity assertion (`filesystem_features` non-empty) guards against a vacuous pass. **Shown RED twice, both directions (AC4):** (a) renaming `backend/src/api/v1/approvals/validation.py` to `validation_renamed.py` failed the guard naming feature `approvals`, difference `{'validation_renamed.py', 'validation.py'}` — the full-file run still collected and passed the other 5 tests (`1 failed, 5 passed`), proving the guard itself fired rather than a `ModuleNotFoundError` collection error (the trap `models.py` would have hit); (b) adding a sixth file (`helpers.py`) to the same conforming feature failed the guard naming feature `approvals`, extra item `helpers.py` — proving set equality rather than a subset check. Both mutations reverted, `git diff` empty each time. |
| ZR-5 | `ENFORCED-BY backend/tests/test_zr5_config_dir_parity.py::test_create_app_does_not_read_config_dir_env_var_directly` (code-level half only); the operational half stays `UNGUARDABLE` | STORY-209 landed the guard specified above: `test_load_settings_config_dir_resolves_to_patched_value` / `test_load_settings_config_dir_defaults_to_config_apps_when_unset` pin `load_settings().config_dir` (AC1 — both roots' shared mechanism); `test_run_main_does_not_read_config_dir_env_var_directly` and `test_create_app_does_not_read_config_dir_env_var_directly` are the AST walks over `run.py::main` and `app.py::create_app` respectively (AC2), each asserting the function neither reads the `CONFIG_DIR` literal / `CONFIG_DIR_VAR` name directly nor skips `load_settings()`; `test_create_app_config_dir_parameter_override_is_not_flagged` proves the `config_dir=` keyword-parameter override stays explicitly permitted, against the real parameter, not just in prose. **Shown RED by mutation, once per root (AC4/AC5):** changing `app.py::create_app` to read `os.environ.get("CONFIG_DIR", "config/apps")` directly instead of `settings.config_dir` failed `test_create_app_does_not_read_config_dir_env_var_directly` naming `app.py`; the identical change to `run.py::main` failed `test_run_main_does_not_read_config_dir_env_var_directly` naming `run.py`; both reverted, `git diff` empty each time. A guard watching only one of the two roots would be the exact asymmetry ZR-5 is about. **It still cannot guard the failure that actually caused the sprint-64 incident** (the operational half): the loop and the API are separate OS processes, each reading its own environment, and no single-process test sees across a process boundary — that half stays `tools/demo_loop_gate/harness.py` runbook discipline, never claimed otherwise. **The code-level half also has its own stated residue (AC3(b)):** AC2's walk catches only a DIRECT env-var read bypassing `load_settings()`; a root rewritten to hardcode `load_config("config/apps")` while still calling `load_settings()` for its other fields would pass every assertion above, because none of them checks that the RETURNED `config_dir` field was the value actually used. Not mechanised by this guard. |
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

Moved 2026-08-12 to [[zone-rules-history]] (`tier: reference`) — 580 lines of append-only
compile record, anchored to the commits it describes and therefore unable to rot. This
article keeps the rules, their citations, the Coverage verdicts and the Adjudication table:
everything that makes a claim about code as it stands now.
