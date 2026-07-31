# STORY-195 — Audit findings: `core` and `adapters` against the zone-rule catalogue

Point-in-time findings report. Sprint history, **not** the wiki — this describes the codebase at
`sprint-66` HEAD `d62276ef91003f922f61856c3572540a93e8c0a7` (short `d62276e`) and must never be
re-stamped later as if still current. Yardstick: `docs/scrum/wiki/zone-rules.md` (`ZR-1..ZR-5`,
`status: verified`, STORY-194) plus the eight `lint-imports` contracts it links to
(`docs/scrum/wiki/architecture-boundary.md`).

## 1. Enumeration (AC1)

Command, run from `backend/src`:

```
find core -name "*.py" -not -path "*__pycache__*" | sort   # 31 files
find adapters -name "*.py" -not -path "*__pycache__*" | sort   # 27 files
```

Output counts: `core` **31**, `adapters` **27**, total **58** — matches planning's V1 exactly. No
mismatch to report.

Every file below was read in full and judged against `ZR-1..ZR-5`. Verdict legend:
- `CLEAN` — no finding.
- `ZR-n` — violates that catalogue rule (none found this story — see §2).
- `GAP-1` — a real observation no `ZR-n` expresses; a catalogue gap, not a rule violation (see §3).

### `core/` (31 files)

| # | File | Verdict |
|---|------|---------|
| 1 | `core/__init__.py` | CLEAN |
| 2 | `core/domain/__init__.py` | CLEAN |
| 3 | `core/domain/component.py` | CLEAN |
| 4 | `core/domain/maintenance.py` | CLEAN |
| 5 | `core/domain/proposal.py` | CLEAN |
| 6 | `core/domain/publication.py` | CLEAN |
| 7 | `core/domain/signal.py` | CLEAN |
| 8 | `core/domain/status.py` | CLEAN |
| 9 | `core/domain/topology.py` | CLEAN |
| 10 | `core/domain/verdict.py` | CLEAN |
| 11 | `core/ports/__init__.py` | CLEAN |
| 12 | `core/ports/clock.py` | CLEAN |
| 13 | `core/ports/component_repository.py` | CLEAN |
| 14 | `core/ports/maintenance_repository.py` | CLEAN |
| 15 | `core/ports/observation_repository.py` | CLEAN |
| 16 | `core/ports/proposal_repository.py` | CLEAN |
| 17 | `core/ports/publication_repository.py` | CLEAN |
| 18 | `core/ports/rejected_observation_repository.py` | CLEAN |
| 19 | `core/ports/sample_mode_repository.py` | CLEAN |
| 20 | `core/ports/signal_ingest.py` | CLEAN |
| 21 | `core/ports/signal_repository.py` | CLEAN |
| 22 | `core/ports/status_publisher.py` | CLEAN |
| 23 | `core/ports/watermark.py` | CLEAN |
| 24 | `core/queries/__init__.py` | CLEAN |
| 25 | `core/queries/availability.py` | CLEAN |
| 26 | `core/services/__init__.py` | CLEAN |
| 27 | `core/services/approval.py` | CLEAN |
| 28 | `core/services/decide.py` | CLEAN |
| 29 | `core/services/ingest_service.py` | CLEAN |
| 30 | `core/services/pipeline.py` | CLEAN |
| 31 | `core/services/skew.py` | CLEAN |

### `adapters/` (27 files)

| # | File | Verdict |
|---|------|---------|
| 1 | `adapters/__init__.py` | CLEAN |
| 2 | `adapters/inbound/__init__.py` | CLEAN |
| 3 | `adapters/inbound/dynatrace/__init__.py` | CLEAN |
| 4 | `adapters/inbound/dynatrace/_assembly.py` | CLEAN |
| 5 | `adapters/inbound/dynatrace/adapter.py` | CLEAN |
| 6 | `adapters/inbound/dynatrace/clickpath_normalizer.py` | CLEAN |
| 7 | `adapters/inbound/dynatrace/dispatch.py` | CLEAN |
| 8 | `adapters/inbound/dynatrace/grail_executor.py` | CLEAN |
| 9 | `adapters/inbound/dynatrace/health_mapping.py` | CLEAN |
| 10 | `adapters/inbound/dynatrace/http_normalizer.py` | CLEAN |
| 11 | `adapters/inbound/dynatrace/query.py` | CLEAN |
| 12 | `adapters/outbound/__init__.py` | CLEAN |
| 13 | `adapters/outbound/statuspage/__init__.py` | CLEAN |
| 14 | `adapters/outbound/statuspage/http_executor.py` | CLEAN |
| 15 | `adapters/outbound/statuspage/status_mapping.py` | CLEAN |
| 16 | `adapters/persistence/__init__.py` | CLEAN |
| 17 | `adapters/persistence/dynamo_component_repository.py` | CLEAN |
| 18 | `adapters/persistence/dynamo_maintenance_repository.py` | CLEAN |
| 19 | `adapters/persistence/dynamo_observation_repository.py` | CLEAN |
| 20 | `adapters/persistence/dynamo_proposal_repository.py` | **GAP-1** |
| 21 | `adapters/persistence/dynamo_publication_repository.py` | CLEAN |
| 22 | `adapters/persistence/dynamo_rejected_observation_repository.py` | CLEAN |
| 23 | `adapters/persistence/dynamo_sample_mode_repository.py` | CLEAN |
| 24 | `adapters/persistence/dynamo_serde.py` | CLEAN |
| 25 | `adapters/persistence/dynamo_signal_repository.py` | CLEAN |
| 26 | `adapters/persistence/dynamo_watermark_repository.py` | CLEAN |
| 27 | `adapters/system_clock.py` | CLEAN |

58 files listed, 58 read, 0 gaps. 57 `CLEAN`, 1 `GAP-1`.

## 2. `ZR-1..ZR-5` findings (AC2)

**None.** Zero violations of any of the five catalogued rules were found in either zone. This is
consistent with what STORY-194's own zone-wide AST/grep passes already established (ZR-1: 0 current
violations; ZR-2: 0 vendor identifiers in `core/` outside the three compliant forms) — this story's
per-file read did not surface anything those passes missed, and additionally confirms ZR-1/ZR-2 hold
under manual reading, not only the mechanical sweep. Re-derivation commands (re-run this story, at
HEAD `d62276e`):

```
$ cd backend/src
$ grep -rn "from src.core" adapters/inbound/dynatrace/*.py
adapters/inbound/dynatrace/_assembly.py:17:from src.core.domain import Health, Provenance, SignalObservation
adapters/inbound/dynatrace/clickpath_normalizer.py:15:from src.core.domain import SignalObservation
adapters/inbound/dynatrace/dispatch.py:37:from src.core.domain import SignalObservation
adapters/inbound/dynatrace/health_mapping.py:23:from src.core.domain import Health
adapters/inbound/dynatrace/http_normalizer.py:15:from src.core.domain import SignalObservation
# -> only src.core.domain imports; zero src.core.ports imports anywhere in adapters/inbound/dynatrace/ (ZR-1)

$ grep -rln "from src.core.ports\|import src.core.ports" adapters/*.py adapters/**/*.py adapters/**/**/*.py
adapters/system_clock.py
adapters/persistence/dynamo_component_repository.py
adapters/persistence/dynamo_maintenance_repository.py
adapters/persistence/dynamo_observation_repository.py
adapters/persistence/dynamo_proposal_repository.py
adapters/persistence/dynamo_publication_repository.py
adapters/persistence/dynamo_rejected_observation_repository.py
adapters/persistence/dynamo_sample_mode_repository.py
adapters/persistence/dynamo_signal_repository.py
adapters/persistence/dynamo_watermark_repository.py
adapters/outbound/statuspage/__init__.py
# -> exactly the modules IMPLEMENTING a port; no adapters/inbound/* module appears (ZR-1 compliant direction)

$ grep -rniE "dynatrace|statuspage|dynamodb|grail|dql" core/*.py core/**/*.py
# (28 lines, every one inside a module/class/function docstring or comment — none as an identifier,
# annotation, signature, dict key, or stored value; the same six previously-unadjudicated lines
# ZR-2 already settles appear again here unchanged — see CLEARED §4)
```

No new finding in either zone against `ZR-1..ZR-5`.

## 3. Catalogue gap — `GAP-1` (not a `ZR-n` finding, per instructions)

**Location:** `backend/src/adapters/persistence/dynamo_proposal_repository.py:286`
(`if action == "approved":`), inside `record_approval_event`.

**What it is:** `record_approval_event`'s `action: str` parameter (the port signature at
`backend/src/core/ports/proposal_repository.py:44` already types it as a bare `str`, not
`ProposalState` — `backend/src/core/services/approval.py:128` derives it from `to_state.value`, so its only two
real values are `"approved"`/`"rejected"`, mirroring `ProposalState.APPROVED.value`/
`ProposalState.REJECTED.value`). The adapter branches on the **hardcoded literal** `"approved"` to
decide whether to denormalize an `approved_actor` attribute onto the proposal's META item — a
persistence-layer decision that duplicates the domain enum's value **as a string**, in the same file
that already imports `ProposalState` for an unrelated purpose. A compliant counter-example sits 180
lines earlier in the **same file**: `backend/src/adapters/persistence/dynamo_proposal_repository.py:105`
(`if proposal.state == ProposalState.OPEN:`) compares the ENUM member correctly, showing the
duplicated-literal shape at line 286 is avoidable with the same import already in scope, not a
missing capability.

**Why no `ZR-n` rule adjudicates this:** `ZR-3` is the catalogue's only "don't re-declare a value
that lives elsewhere" rule, but its *statement* is explicitly scoped to the `tools/` <->
`backend/src/` one-way boundary ("a value DECLARED in `backend/src/` ... whose value `tools/` also
needs..."), not to duplication *within* `backend/src/` between a core domain enum and an adapter in
the same zone. `ZR-1` (persistence-port holding) and `ZR-2` (vendor-vocabulary confinement) do not
apply either — this is neither an adapter holding a persistence port it shouldn't, nor a vendor word;
`"approved"` is a **domain** value, not a vendor one. No existing rule's text covers "an adapter
compares a domain enum's value as a literal instead of importing the enum, within the same `src`
tree." **This is therefore a genuine catalogue gap** — a real, findable pattern (the brief's own
"adapters that decide rather than translate" and "duplicated domain logic across the two zones"
categories both name this shape) that `ZR-1..ZR-5` as currently adjudicated do not settle.

**Why the eight `lint-imports` contracts pass it:** import-linter checks module import *edges*, never
literal *values*. `dynamo_proposal_repository.py` importing `src.core.domain.proposal.ProposalState`
is exactly the legal, expected `adapters -> core` direction (`adapters-independence` and
`core-independence` are both satisfied); nothing in the eight contracts inspects what a module does
with a value once it has imported it, so a hardcoded string sitting next to a correct enum comparison
in the same file is invisible to every one of them. This is not a broken build — it is precisely the
class of gap this audit sprint was scheduled to find.

**Proposed rule for STORY-197 to adjudicate (`ZR-6`, draft text, not yet in the catalogue):**

> Within `backend/src/`, a module that already imports a core domain `Enum` must compare against that
> enum's member (or `.value`) rather than an independently-typed string/int literal that happens to
> equal it. A literal comparison is permitted only where importing the enum is itself impossible
> (e.g. genuinely external input with no corresponding domain type) — never where the import is
> already present in the same file for another purpose.

Coverage verdict (my own assessment, pending STORY-197 adjudication): likely `GUARDABLE` only
partially — an AST-based lint could flag "a string/int constant compared with `==` against a
parameter/variable, in a module that also imports an `Enum` subclass whose `.value` set contains that
literal" but this is a heuristic (false positives on genuinely-external strings are likely), not a
clean `lint-imports` contract. **STORY-197 would need the catalogue amended with this rule (or a
narrower version of it) before this shape becomes a scored, guardable finding; this report does not
score it as such itself, per instruction.**

I did not fix this inline (C1) — see §5 for the proposed backlog story for the code-level fix, which
is independently worth doing regardless of whether `ZR-6` is ever formalized as a mechanical guard.

## 4. `CLEARED` — considered and rejected (AC4)

- **Vendor prose in `core/` (the ~20-occurrence case, STORY-194 AC5's compliant set).** Re-verified
  directly by re-reading every one of the ~28 grep-matched lines in §2's re-derivation: all are
  docstring/comment prose, matching ZR-2's three closed compliant forms. The six previously-flagged,
  now-settled citations (`backend/src/core/domain/component.py:17`, `backend/src/core/domain/publication.py:35`,
  `backend/src/core/ports/component_repository.py:53`, `backend/src/core/ports/observation_repository.py:5` and
  `backend/src/core/ports/observation_repository.py:7`,
  `backend/src/core/ports/__init__.py:7`) were each re-read directly this story and confirmed to name a vendor
  word only inside a class/method/module docstring, never as an identifier, annotation, signature,
  dict key, or stored value. **CLEARED — not a finding**, per ZR-2's own ruling and this story's
  independent re-read.
- **`DynamoPublicationRepository.list_recent` reading `PROPOSAL#<id>` items to resolve
  `Publication.author`** (`backend/src/adapters/persistence/dynamo_publication_repository.py:73-96`).
  Considered as a candidate "repository owning a key shape it shouldn't" / cross-aggregate reach.
  **CLEARED**: `Publication.author` is explicitly a domain-designated derived-on-read field
  (`backend/src/core/domain/publication.py:71-72`: "Optional author derived on read (not persisted by `record`)");
  the adapter's `BatchGetItem` against `PROPOSAL#<id>`/`META` items implements that documented
  contract as a storage detail within the SAME zone's own persistence layer, not a policy decision the
  adapter invented, and not a reach into core or another adapter's port. `[[persistence-adapters]]`
  already documents this exact behaviour (line 32 of that article) with no contradiction to my
  reading (see §5 wiki check).
- **`dynamo_maintenance_repository.py`'s GSI eventual-consistency window** (`is_under_maintenance`
  querying a GSI that may lag a just-created window by one pull cycle). Considered as a possible
  hidden policy decision in a persistence adapter. **CLEARED**: this is a documented,
  PO-accepted (2026-06-14, per the module's own docstring and `[[persistence-adapters]]:34`) storage
  trade-off, not an undisclosed decision — and it is a DynamoDB consistency-model fact, not business
  logic about what maintenance means.
- **`dispatch.py::normalize_rows_lenient`'s broad `except ValueError`** (STORY-190). Considered as a
  possible over-broad boundary violation (an adapter "deciding" what counts as a bad row rather than
  translating). **CLEARED**: this stays entirely within `adapters/inbound/dynatrace/` — it never
  imports or calls a persistence port (ZR-1), and every error class it can possibly catch
  (`UnknownVendorStatusError`, `UnknownVendorOutcomeError`, `UnsupportedMonitorTypeError`,
  `MalformedDqlRowError`, pydantic `ValidationError`) is either declared in this same package or is a
  library validation error over a value this package itself constructs; the function's contract is
  still "return a value" (`NormalizationOutcome`), never "persist." Its own docstring already
  documents the widening rationale (sprint-65 quality review) — not a new decision this audit found.
- **The "only `composition` sees both `src.core` and `src.adapters` concretely" precision claim**
  (zone-rules.md's precision parenthetical). Re-checked directly across all 58 files this story reads:
  no module outside `composition/` holds a concrete class from BOTH zones for dependency-injection
  purposes; the only "imports both" shapes found are ordinary within-adapter-package imports
  (`adapters/inbound/dynatrace/adapter.py` importing sibling `dispatch.py`/`query.py`, already named
  by the catalogue as the non-counterexample). **CLEARED — no contradiction found.**
- **`core/queries/availability.py` importing `core/services/pipeline.py::collapse`.** Considered as a
  possible `core-internal-layering` concern (does `queries` reaching into `services` violate the
  domain<-ports<-services<-queries ordering?). **CLEARED**: `pyproject.toml`'s `core-internal-layering`
  contract (`layers = ["src.core.queries", "src.core.services", "src.core.ports", "src.core.domain"]`)
  places `queries` as the OUTERMOST layer specifically so it may import `services`, `ports`, and
  `domain` — this import is the compliant direction, matching the contract exactly.

## 5. Wiki cross-check (AC5)

Checked `docs/scrum/wiki/persistence-adapters.md` (the article whose `code_refs` most directly
overlap this audit's `adapters/persistence/` findings) against every claim this report makes about
that directory. **No contradiction found.** The article's line 32 claim
("`DynamoPublicationRepository` implements `list_recent` ... resolving authors via BatchGetItem on
distinct proposal METAs using the denormalized `approved_actor` attribute") is consistent with what I
read and CLEARED in §4. The article does not mention the `GAP-1` literal-comparison observation at
all (neither confirming nor contradicting it) — it is a genuine gap in the article's coverage, not a
wrong claim, so no correction is filed against it; a future revision of `persistence-adapters.md`
MAY want to note the `record_approval_event` denormalization decision explicitly if/when `GAP-1`'s
proposed fix lands, but that is a candidate, not a contradiction requiring filing now.

No other wiki article makes a claim this report's findings (or lack thereof) contradict.

## 6. Proposed stories

No `MAJOR` or `MINOR` `ZR-n` findings exist in this audit to file (see §2) — filing a story for a
non-existent finding would be exactly the "manufactured finding" the brief warned against. The one
substantive output, `GAP-1`, is filed below as its own draft, independent of any `ZR-n` id, since the
underlying code issue (a hardcoded literal duplicating an enum value, with a correct counter-example
four lines' worth of imports away in the same file) is worth fixing regardless of whether STORY-197
ever formalizes `ZR-6` as a mechanical guard.

### STORY-198 — Fix the hardcoded `"approved"` literal in `DynamoProposalRepository.record_approval_event`

- **Type:** defect (code-quality / drift-risk, not a live incident — verified no test currently
  exercises the divergent-value case, so this is preventive, not a hotfix)
- **Estimate:** 1 (fibonacci)
- **Offending citation:** `backend/src/adapters/persistence/dynamo_proposal_repository.py:286`
- **Context:** `record_approval_event` compares its `action: str` parameter against the hardcoded
  literal `"approved"` to decide whether to denormalize `approved_actor` onto the proposal's META
  item, even though `ProposalState` (whose `.value` this literal duplicates) is already imported in
  the same file and is compared correctly, as an enum member, four lines away in the same class
  (line 105: `if proposal.state == ProposalState.OPEN:`). If `ProposalState.APPROVED`'s value were
  ever renamed, this comparison would silently stop firing with no import-linter or type-check
  signal — the class of gap STORY-195 was scheduled to find (`GAP-1` in
  `docs/scrum/sprints/2026-07-31-sprint-66/audit-core-adapters.md`).
- **Acceptance criteria (testable):**
  - AC1: `record_approval_event`'s branch reads
    `if action == ProposalState.APPROVED.value:` (or an equivalent enum-member comparison), never the
    bare string literal `"approved"`.
  - AC2: A test asserts that calling `record_approval_event` with
    `action=ProposalState.APPROVED.value` denormalizes `approved_actor` onto the META item (the
    existing behaviour, now pinned against a literal drift: mutate `ProposalState.APPROVED`'s value
    in a throwaway subclass/monkeypatch scenario, or equivalently assert the comparison is against the
    enum object, not a copy-pasted string, per the mutation-testing standing rule for computational
    guards where applicable).
  - AC3: Existing `test_dynamo_proposal_repository`-family contract tests continue to pass unchanged
    (this is a like-for-like literal replacement, not a behaviour change for the two real inputs
    `"approved"`/`"rejected"`).

## 7. Citation-resolution sweep (AC re-derivation requirement)

Extraction-based, not hand-typed — script parses every `` `path:line` `` citation directly out of
this finished report's own text and checks it against the repo at HEAD, mirroring STORY-194's
`citation_sweep_v2.py` approach.

Command: `python citation_sweep_story195.py` (scratchpad script,
`C:\Users\Hyndhava\AppData\Local\Temp\claude\C--Hyn-uptime-monitor-v3\9084bd9e-0098-41f0-bb7b-8d9c8dfa1d32\scratchpad\citation_sweep_story195.py`),
run at HEAD `d62276e`. Same regex STORY-194's `citation_sweep_v2.py` used:
`` `([\w./\\-]+\.(?:py|md)):((?:\d+(?:-\d+)?)(?:,\d+(?:-\d+)?)*)` `` applied to this file's full text,
each `(path, line-spec)` resolved against the repo root. **First run found 9 failures** — several of
this report's own citations used a shorthand path (e.g. `dynamo_proposal_repository.py:105` instead
of the full `backend/src/adapters/persistence/dynamo_proposal_repository.py:105`) that the sweep
correctly refused to resolve; all were rewritten to full repo-relative paths (the versions now in
§3/§4 above) and the sweep re-run clean. Final output:

```
OK   backend/src/adapters/persistence/dynamo_proposal_repository.py:286 (file has 316 lines)
OK   backend/src/core/ports/proposal_repository.py:44 (file has 64 lines)
OK   backend/src/core/services/approval.py:128 (file has 139 lines)
OK   backend/src/adapters/persistence/dynamo_proposal_repository.py:105 (file has 316 lines)
OK   backend/src/core/domain/component.py:17 (file has 33 lines)
OK   backend/src/core/domain/publication.py:35 (file has 80 lines)
OK   backend/src/core/ports/component_repository.py:53 (file has 56 lines)
OK   backend/src/core/ports/observation_repository.py:5 (file has 49 lines)
OK   backend/src/core/ports/observation_repository.py:7 (file has 49 lines)
OK   backend/src/core/ports/__init__.py:7 (file has 40 lines)
OK   backend/src/adapters/persistence/dynamo_publication_repository.py:73-96 (file has 121 lines)
OK   backend/src/core/domain/publication.py:71-72 (file has 80 lines)

Extracted 14 citation occurrence(s), 12 distinct (path, line-spec) pair(s) checked, 0 failure(s).
```

(The two `docs/scrum/wiki/persistence-adapters.md` bare line-number mentions in prose — "line 32",
"line 34" — are natural-language references, not `path:line` citations, and are not in the regex's
match shape; they were verified by direct reading in §4/§5, not by the mechanical sweep.)

## 8. Gate

`REQUIRE_DYNAMO=1 DYNAMO_ENDPOINT_URL=http://127.0.0.1:8021`, five backend DoD commands via
`yt_gate.py`, run at HEAD `d62276e` (see the implementer's session for the raw `yt_gate.py` output;
this is a docs-only story, so no backend/adapters code changed — the gate is expected to reproduce the
sprint's V7 baseline unchanged). Recorded pass/skip counts and exit codes are in the final report's
`dod_self_run` block.

## 9. Diff-scope proof (C1)

`git diff --name-only d4ad03e..HEAD -- backend/src frontend config` — expected empty for this story's
own commits (checked at report time; see the implementer's final commit list).

## History

- 2026-07-31: STORY-195 findings report authored. 58/58 files enumerated and read (31 `core`, 27
  `adapters`). Zero `ZR-1..ZR-5` violations found (consistent with STORY-194's planning-time zero-
  violation measurements, re-derived independently here by direct reading + re-run commands). One
  catalogue gap (`GAP-1`) found and reported as such, not scored as a `ZR-n` finding, per instruction:
  `backend/src/adapters/persistence/dynamo_proposal_repository.py:286` hardcodes `"approved"` instead of comparing
  `ProposalState.APPROVED.value`, with a correct counter-example 180 lines earlier in the same file.
  Proposed `ZR-6` (draft, not yet in the catalogue) and filed `STORY-198` for the code-level fix,
  independent of whether `ZR-6` is ever formalized. Five `CLEARED` entries recorded. No wiki
  contradiction found (one article, `persistence-adapters.md`, checked directly; no claim it makes
  conflicts with this report). The extraction-based citation sweep (§7) initially found 9 failures —
  self-inflicted shorthand paths in this report's own prose, not real broken citations — corrected to
  full repo-relative paths and re-run clean; recorded rather than silently fixed, per instruction to
  flag rather than substitute.
