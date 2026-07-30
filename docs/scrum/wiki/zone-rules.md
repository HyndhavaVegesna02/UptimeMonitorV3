---
title: Zone-intent rule catalogue — the boundary rules the eight contracts cannot see
code_refs: [backend/src/adapters/inbound/dynatrace/adapter.py, backend/src/core/services/ingest_service.py, backend/src/core/domain/signal.py, backend/src/core/ports/status_publisher.py, backend/src/adapters/outbound/statuspage/__init__.py, backend/src/adapters/inbound/dynatrace/health_mapping.py, tools/demo_engine/assumed_failure_codes.py]
verified_sha: 227d5bf
verified_sprint: sprint-66
status: verified
# code_refs deliberately NARROW (STORY-194, sprint-66): scoped to EXACTLY the
# files this article's rules cite as compliant/illustrative examples — never
# whole-zone directories. A whole-zone ref (e.g. "backend/src/core/") would
# mark this article stale on every future sprint that touches ANY file in
# core/adapters/tools, quarantining the yardstick STORY-195/196/197 depend on
# from every future subagent brief. Same discipline architecture-boundary.md
# records in its own frontmatter comment (sprint-5 retro amendment).
# `pyproject.toml` is deliberately NOT a code_ref here: it is already a
# code_ref in 5 articles against the refs-check's AMPLIFIER_THRESHOLD of 4,
# and architecture-boundary.md already owns the eight import-linter contracts
# — this article LINKS to that article for the mechanical set instead of
# re-citing or restating it.
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
`ZR-1..ZR-3` that a future audit (STORY-195, STORY-196) measures the codebase against
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
  both `src.core` and `src.adapters` — no fourth contract is needed to say so.

None of the above is restated from [[architecture-boundary]]; that article owns the
eight-contract citations. This article's job is everything below, which the contracts
cannot see.

### The gap — rules the eight contracts do not enforce

#### ZR-1 — an inbound adapter is a pure translation function; it must never hold or call a persistence port

- **Statement.** An inbound adapter (`adapters/inbound/*`) returns canonical values
  only. It must never import, hold, or call a `core/ports` repository/persistence
  interface — persisting a batch (or a quarantined row) is core's job, done by the
  service the adapter's return value is handed to.
- **Source.** PO directive 2026-07-30 (memory `code-boundary-discipline`), stated
  verbatim as "always respect the code boundaries and discipline I wanted to follow,"
  concrete rule 1: "an inbound adapter is a pure translation function — it returns
  values and persists nothing." Also CLAUDE.md's "two things to know" preamble, which
  names this exact shape as the STORY-190 motivating case.
- **Compliant citation.** `backend/src/adapters/inbound/dynatrace/adapter.py::fetch_observations`
  (line 26) returns `NormalizationOutcome` — a value — and the whole
  `adapters/inbound/dynatrace/` package imports `src.core.domain` only, never
  `src.core.ports` (verified: `grep -n "from src.core" backend/src/adapters/inbound/dynatrace/*.py`
  returns only `domain` imports, zero `ports` imports). Persistence itself happens one
  layer further in, inside core:
  `backend/src/core/services/ingest_service.py::IngestService.ingest_observations`
  (line 121) calls `self._rejected_repo.save(...)` — the injected
  `RejectedObservationRepository` port is held and called by the CORE service that
  consumes the adapter's return value, never by the adapter itself.
- **Coverage verdict.** `GUARDABLE` (a new import-linter `forbidden` contract:
  `source_modules = ["src.adapters.inbound"]`, `forbidden_modules = ["src.core.ports"]`.
  An inbound adapter needs only `src.core.domain` types to return values; needing any
  port at all is the persist-capability smell. Verified 0 current violations, so the
  contract would land green and would have caught STORY-190's tempting-but-wrong first
  draft had it shipped.)

#### ZR-2 — inside `core/`, a vendor name may appear only as explanatory prose; never as an identifier, type annotation, signature, or stored data value

- **Statement.** Within `core/domain`, `core/ports`, and `core/services`, a vendor
  word (`Dynatrace`, `Statuspage`, `Grail`, `DQL`, …) may appear ONLY inside a
  docstring or comment explaining the boundary. It must never appear as a function or
  class name, a parameter name, a type annotation, a function signature, or a stored
  data value — that form of vendor vocabulary stays inside the adapter that owns it.
- **Source.** PO directive 2026-07-30 concrete rule 3: "a port the core owns must be
  expressible in domain types — if an interface would have to name vendor words (e.g.
  Dynatrace `code`/`message`), it does not belong in `core/ports/`." Dossier principle
  P3 ("The core speaks only canonical vocabulary... A port signature must make sense
  to someone who has never heard of Dynatrace"). CLAUDE.md's ~20-occurrence note is
  the planning-time evidence this rule adjudicates.
- **Compliant citation (prose, inside core).** `backend/src/core/domain/signal.py`
  line 6: "... every other field reads to someone who has never heard of Dynatrace" —
  one of ~20 such docstring/comment mentions across `core/domain/publication.py`,
  `core/domain/status.py`, `core/ports/__init__.py`, `core/ports/status_publisher.py`,
  `core/services/approval.py`, `core/services/decide.py`,
  `core/services/ingest_service.py`, and `core/services/pipeline.py` (re-verified this
  story: `grep -rniE "dynatrace|statuspage|grail|dql" backend/src/core/` — every hit is
  inside a docstring/comment line, none an identifier). **Compliant citation
  (domain-typed port signature).**
  `backend/src/core/ports/status_publisher.py::StatusPublisherPort.publish` (lines
  14–19) takes and mentions only `StatusChange`, a domain type — no vendor word
  anywhere in the class name, the method name, or the signature.
- **Illustrative citation of the FORBIDDEN FORM** — an identifier bearing vendor
  vocabulary — shown at the one place that form is currently compliant, because it has
  never left its own adapter: `backend/src/adapters/outbound/statuspage/__init__.py::StatuspagePublisher`
  (line 23) and its constructor's vendor-shaped identity (`page_id`, `component_mapping`
  resolving to a Statuspage id at publish time). This repo has **zero** occurrences of
  this identifier/signature form inside `core/` today — verified this story with an AST
  walk of every `core/` module's `FunctionDef`/`AsyncFunctionDef`/`ClassDef` names, and
  every `arg` and `Name` node, for the substrings `dynatrace|statuspage|grail|dql`
  (case-insensitive): zero matches, confirming the ~20 grep hits above are ALL
  docstring/comment content, which an AST identifier walk does not see. The identical
  class-name/kwarg shape appearing anywhere under `core/` is exactly what this rule
  forbids; `StatuspagePublisher` is compliant only because `adapters/outbound/statuspage/`
  is its rightful home.
- **Coverage verdict.** `GUARDABLE` (a pytest test that parses every `core/` module
  with `ast`, walks its `FunctionDef`/`AsyncFunctionDef`/`ClassDef` names plus every
  `arg` and `Name` node, and asserts none contains a vendor substring from a small,
  named list. Docstrings are string constants and comments are outside the AST
  entirely, so an identifier-only walk excludes both without a separate allowlist —
  the exact discrimination this rule needs.)

#### ZR-3 — a constant shared across the `tools/` -> `backend/src/` one-way boundary is declared once, in `backend/src/`, and imported by `tools/` — never re-declared

- **Statement.** Where `tools/` needs a value that must agree with something declared
  in `backend/src/` (a vendor code/message mapping, a threshold, any constant whose
  drift would be a silent bug), the value is declared exactly once, inside
  `backend/src/`, and `tools/` imports it. `tools/` never re-declares the literal.
- **Source.** PO directive 2026-07-30 concrete rule 4: "`tools/` may import `src.*`,
  never the reverse — so a constant shared between them lives in `backend/src/` and
  `tools/` imports it rather than duplicating the literal." CLAUDE.md's "two things to
  know" preamble: "They live in exactly one place — `tools/` derives them, never
  redeclares them."
- **Compliant citation.** `tools/demo_engine/assumed_failure_codes.py` line 31 imports
  `PROVISIONAL_STATUS_MAPPING` from
  `backend/src/adapters/inbound/dynatrace/health_mapping.py` line 35, rather than
  re-declaring the `("1", "UNHEALTHY")` / `("2", "DEGRADED")` pairs a second time.
- **Coverage verdict.** `UNGUARDABLE` by `lint-imports` — its `root_package` setting is
  `"src"` (see [[architecture-boundary]]), which makes it structurally blind to
  anything under `tools/` (verified at sprint-66 planning, V6 in
  `docs/scrum/sprints/2026-07-31-sprint-66/plan.md`; no `tools/` module is even a
  candidate `source_modules`/`forbidden_modules` entry for any contract). `GUARDABLE`
  by a pytest test instead (the "duplicated-declaration
  sweep" STORY-196 builds and demonstrates capable of finding something; STORY-197 may
  promote it to a standing test): parse every literal declared under `tools/` and every
  literal declared under `backend/src/`, and fail if a `tools/`-side literal matches a
  `backend/src/`-side literal byte-for-byte with no import edge between the two
  declaring modules.

## Inference (synthesis, not verified)

The eight contracts plus `ZR-1..ZR-3` together are the audit's yardstick: every
`lint-imports`-legal-but-intent-violating shape the PO named now has either a
contract citation (already mechanical) or a rule id, a verdict, and — where
`GUARDABLE` — a concrete next rung. A finding with no rule id in STORY-195/196 is
either a new rule (amend this catalogue and say so) or an opinion to drop (sprint-66
plan, constraint C5).

## History

- sprint-66 (STORY-194): created. Rules ZR-1..ZR-3 cover the PO's five named areas
  ((a) adapter persistence -> ZR-1; (b) core reaching outward -> already mechanical;
  (c) api reaching another feature/an adapter -> already mechanical; (d) vendor
  vocabulary escaping its adapter -> ZR-2; (e) the `tools/` <-> `backend/src/`
  duplicated constant -> ZR-3). verified_sha -> 227d5bf (the commit immediately
  preceding this article's own commit; no code_ref file changes between the two).
