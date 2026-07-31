# STORY-195 — Audit findings: `core` and `adapters` against the zone-rule catalogue

Point-in-time findings report. Sprint history, **not** the wiki — this describes the codebase at
`sprint-66` HEAD `d62276ef91003f922f61856c3572540a93e8c0a7` (short `d62276e`) and must never be
re-stamped later as if still current. Yardstick: `docs/scrum/wiki/zone-rules.md` (`ZR-1..ZR-7` as of
this fix round — `ZR-1..ZR-5` from STORY-194 planning, `ZR-6`/`ZR-7` added mid-sprint from this
story's own quality-review fix round, see §2b/§2c) plus the eight `lint-imports` contracts it links to
(`docs/scrum/wiki/architecture-boundary.md`).

**Note on staleness (F4):** the header above still names `d62276e` because nothing under
`backend/src/` has changed since — this fix round only touches `docs/scrum/` files (this report,
`zone-rules.md`, and the `STORY-198`/`STORY-199`/`STORY-200`/`STORY-201` story files it proposes) —
verified directly in §9. AC2's "resolves at the sprint HEAD" holds only for that reason, not because
the report is current with the fix-round's own HEAD; if a future story touches `backend/src/`, this
report's citations must be re-verified against the NEW HEAD, not assumed still accurate.

## FIX ROUND (2026-07-31) — what changed and why

Both reviewers found real problems. Spec: AC2 `NOT_MET` (the re-derivability of several claims did
not hold up). Quality: `FIX_REQUIRED`, 4 MAJOR + 9 minor, from an **independent re-audit of ~46 of
this report's own 58 files** that found four things inside this story's own footprint that the
original pass missed or mis-adjudicated. Every item below (F1-F5) was independently re-verified by
me, not merely accepted, before I edited anything — where a claim was already fully correct (e.g. the
run.py/app.py config-parity citation), it is left as-is.

- **F1 — a real, unreported production defect** in `adapters/persistence/`: five `list_*`/boolean
  methods across four files pair an unbounded DynamoDB `query` with a post-read filter and no
  `LastEvaluatedKey` loop, against port contracts that promise "all". See §2c (new rule `ZR-7`) and
  the fix story `STORY-199`.
- **F2 — `GAP-1`'s root cause was mis-adjudicated.** The original pass verdicted
  `core/ports/proposal_repository.py` `CLEAN` while quoting its own `action: str` line as the
  explanation for the adapter-level symptom (`GAP-1`, filed as `STORY-198`, already landed). The port
  signature leaking a primitive where `ProposalState` already exists and is used correctly one method
  away is the root cause. See §2b (new rule `ZR-6`) and the fix story `STORY-200`.
- **F3 — an un-adjudicated vendor-row question.** The raw DQL row inside a quarantined
  `RejectedObservationRepository.save(payload=...)` call crosses from the inbound adapter, through
  composition, into persistence, unconverted — the report never said explicitly whether that is
  compliant. Adjudicated explicitly in §4 as `CLEARED`, with the reasoning written out.
- **F4 — re-derivability defects.** A grep pattern that didn't reproduce its own claimed count; a
  citation off by one line (`:44` vs `:45`); an arithmetic error ("four lines away" / "180 lines
  earlier" for a 181-line gap); §8/§9 recorded in the future tense with no real output; a wiki
  cross-check that examined 1 of 11 relevant articles while claiming a blanket "no contradiction". All
  corrected below, with real command output, not "expected" language.
- **F5 — the 57 (now 53) `CLEAN` verdicts read as a bulk assertion.** §1 now states, per module group,
  what question was actually asked of each group and what evidence backs the verdict, rather than a
  uniform `CLEAN` that overstates a shared grep as if it were 58 independent reads of equal depth.

## 1. Enumeration (AC1)

Command, run from `backend/src`:

```
find core -name "*.py" -not -path "*__pycache__*" | sort   # 31 files
find adapters -name "*.py" -not -path "*__pycache__*" | sort   # 27 files
```

Output counts: `core` **31**, `adapters` **27**, total **58** — matches planning's V1 exactly. No
mismatch to report.

Verdict legend:
- `CLEAN` — no finding.
- `ZR-n` — violates that catalogue rule (§2b/§2c).
- `GAP-1 (superseded)` — the file where the ORIGINAL pass recorded an unscored catalogue-gap
  observation; its root cause is now scored elsewhere as `ZR-6` (see §3).

### Evidence basis per module group (F5) — what question was actually asked, and how

Every one of the 58 files was opened and read; the honest addition this fix round makes is stating
what each group's `CLEAN` verdict actually rests on, since "I read it" was correctly challenged as
insufficient on its own.

- **`core/domain/` (9 files) + `core/domain/__init__.py`, `core/__init__.py` (2 more, 11 total incl.
  package roots — see table for the exact 10+1 split).** Read in full; judged against ZR-2's FORM
  test (every vendor-word occurrence individually classified as docstring/comment/attribute-docstring
  prose vs. identifier/annotation/signature/dict-key/stored-value) and against whether any field type
  leaks an adapter/SQL/HTTP shape. No persistence, no I/O, no decide-vs-translate question applies —
  these are pure pydantic value types.
- **`core/ports/` (13 files).** Read in full. Judged against three questions per file, not one: (i)
  ZR-2's vendor-vocabulary form test (as above); (ii) whether the signature is expressible in domain
  types (dossier P3) — the question `ZR-6` exists because of; (iii) — new to this fix round — whether
  a docstring's completeness promise ("all"/"every") is one an implementing adapter could silently
  fail to honor, the question `ZR-7` exists because of. The FIRST pass asked (i) rigorously (backed by
  an AST-shaped mental walk of every symbol name) and (ii)/(iii) only implicitly ("does this look like
  a reasonable port") — that implicit pass is exactly where `core/ports/proposal_repository.py`'s
  `action: str` was missed. This fix round re-asked (ii) and (iii) explicitly, per file, for all 13.
- **`core/services/` + `core/queries/` (8 files, incl. package roots).** Read in full; judged against
  internal-layering direction (`queries -> services -> ports -> domain`) and the same three port-facing
  questions where a service CALLS a port (none of these six services/queries modules define a port,
  so (ii)/(iii) apply only to the CALL sites, not new signatures — `decide.py`, `pipeline.py`,
  `skew.py` take no port at all and are structurally unable to trip ZR-1/6/7).
- **`adapters/inbound/dynatrace/` (9 files).** Read in full. Judged against ZR-1 (must never hold a
  persistence port — verified BOTH by reading every import statement AND by the grep re-derivation in
  §2a) and, explicitly, the open-ended "does this adapter decide rather than translate" question named
  in the brief — this is where `dispatch.py`'s broad `except ValueError` and
  `clickpath_normalizer.py`'s `require_field`-bypass were found and adjudicated (§4).
- **`adapters/outbound/statuspage/` (3 files) + `adapters/system_clock.py` (1 file).** Read in full;
  judged against ZR-1 (N/A — not inbound) and the decide-vs-translate question; no finding.
- **`adapters/persistence/` (11 files).** Read in full. This is the group the fix round's independent
  audit concentrated on, and rightly so: the FIRST pass's per-file question here was effectively "does
  this hold/call a port it shouldn't" (ZR-1's direction, always compliant — these files correctly
  IMPLEMENT ports) and "does this decide policy" (caught the `record_approval_event` literal as an
  unscored gap, missed that its root cause was upstream). It did NOT ask, per file, "does this
  adapter's result set actually satisfy the completeness its port promises" — that omission is exactly
  `ZR-7`, found on re-audit in `dynamo_maintenance_repository.py`, `dynamo_component_repository.py`,
  `dynamo_signal_repository.py`, and `dynamo_proposal_repository.py`, with the compliant counter-
  pattern already present in the same directory (`dynamo_observation_repository.py`).

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
| 16 | `core/ports/proposal_repository.py` | **ZR-6** |
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
| 6 | `adapters/inbound/dynatrace/clickpath_normalizer.py` | CLEAN (see §4 CLEARED — a latent, currently-unreachable hygiene gap, not a finding) |
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
| 17 | `adapters/persistence/dynamo_component_repository.py` | **ZR-7** |
| 18 | `adapters/persistence/dynamo_maintenance_repository.py` | **ZR-7** |
| 19 | `adapters/persistence/dynamo_observation_repository.py` | CLEAN (the compliant counter-example ZR-7 cites) |
| 20 | `adapters/persistence/dynamo_proposal_repository.py` | **ZR-7**; `GAP-1 (superseded — see §3, root cause now `ZR-6` on the port file)` |
| 21 | `adapters/persistence/dynamo_publication_repository.py` | CLEAN (see §4 — `list_recent`'s `limit` is a stated bound, not an "all" promise; ZR-7 does not apply) |
| 22 | `adapters/persistence/dynamo_rejected_observation_repository.py` | CLEAN (see §4 — the raw-payload question is adjudicated CLEARED, not a finding) |
| 23 | `adapters/persistence/dynamo_sample_mode_repository.py` | CLEAN |
| 24 | `adapters/persistence/dynamo_serde.py` | CLEAN |
| 25 | `adapters/persistence/dynamo_signal_repository.py` | **ZR-7** |
| 26 | `adapters/persistence/dynamo_watermark_repository.py` | CLEAN |
| 27 | `adapters/system_clock.py` | CLEAN |

58 files listed, 58 read, 0 gaps. 53 `CLEAN`, 1 `ZR-6`, 4 `ZR-7` (one file, `dynamo_proposal_repository.py`,
carries both a `ZR-7` finding of its own AND the superseded `GAP-1` cross-reference to `ZR-6`, which
lives on the PORT file, not this one — it is listed once, per AC1, with both facts on its one row).

## 2. `ZR-1..ZR-5` findings (AC2) — re-derived, corrected

Zero violations of `ZR-1` through `ZR-5` were found in either zone (the two NEW findings this fix
round adds, `ZR-6`/`ZR-7`, are §2b/§2c below — they did not exist as rules at the original pass and so
could not have been "missed" against `ZR-1..ZR-5`). This is consistent with STORY-194's own zone-wide
AST/grep passes (ZR-1: 0 current violations; ZR-2: 0 vendor identifiers in `core/` outside the three
compliant forms).

### 2a. Re-derivation commands (corrected)

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
```

**F4 correction — the vendor-word grep did not reproduce its originally-claimed count.** The original
report claimed "28 lines" using the pattern `dynatrace|statuspage|dynamodb|grail|dql`. Re-run at HEAD,
that exact pattern returns **22** lines, not 28 — the "28" does not reproduce and is corrected here
rather than silently restated (same bar STORY-194 held itself to for its 105-vs-101 count). Worse: that
pattern, using the literal substring `dynamodb` (not `dynamo`), structurally CANNOT match
`DynamoComponentRepository`, `DynamoPublicationRepository`, or `dynamo_observation_repository.py` —
so it never actually reproduced 4 of the 6 previously-adjudicated "settled" citations the original
report claimed to reconfirm with it
(`backend/src/core/domain/component.py:17`, `backend/src/core/domain/publication.py:35`,
`backend/src/core/ports/component_repository.py:53`, `backend/src/core/ports/observation_repository.py:7`).
Those four were, in fact, verified only by DIRECT READING (as §4 has always separately stated) — the
grep was never evidence for them, and citing it alongside them implied otherwise. Corrected pattern:

```
$ grep -rniE "dynatrace|statuspage|dynamo|grail|dql" core/*.py core/**/*.py | wc -l
26
```

**26, not 22 and not 28 — recorded honestly, with the corrected pattern shown, rather than adjusted to
match either prior number.** All 26 lines are docstring/comment/attribute-docstring prose (re-verified
directly, this fix round, line by line) — see §4 for the six specifically-named citations, verified by
READING, not by this grep, which is a recall aid only.

No new `ZR-1..ZR-5` finding in either zone.

## 2b. `ZR-6` finding — `ProposalRepository.record_approval_event`'s `action` parameter leaks a primitive where a domain type already exists

**`ZR-n`:** `ZR-6` (added to `docs/scrum/wiki/zone-rules.md` this fix round — did not exist at the
original pass).

**`file:line`:** `backend/src/core/ports/proposal_repository.py:45` (`action: str`, in
`record_approval_event`'s abstract signature).

**Severity:** `MAJOR` — a real, shipping port signature (not a docstring/naming nit) that leaks a
primitive where the domain type it stands in for (`ProposalState`) is imported in the SAME file and
used correctly, as the domain type, 13 lines above at `backend/src/core/ports/proposal_repository.py:32`
(`to_state: ProposalState`, in the sibling `resolve` method).

**Why the eight `lint-imports` contracts pass it:** import-linter checks import edges between
modules; `action: str` imports nothing, so there is no edge for any contract to see. A parameter's
primitive-vs-domain-type shape is invisible to a static import graph by construction — the same class
of gap as ZR-1/ZR-2, applied to a port SIGNATURE rather than an adapter's import list.

**What this caused, downstream:** `backend/src/adapters/persistence/dynamo_proposal_repository.py:286`
(`if action == "approved":`) receives the bare string the port hands it and compares it against a
HARDCODED LITERAL rather than an enum member — the exact shape a correctly-typed port signature would
make structurally awkward to write. The ORIGINAL pass adjudicated this adapter-level symptom as an
unscored catalogue gap (`GAP-1`, filed as `STORY-198`, since landed) while separately verdicting
`core/ports/proposal_repository.py` `CLEAN` — having quoted the very line (`action: str`) that is the
root cause, without recognizing it as one. This fix round corrects that: the finding is scored HERE,
on the port, as `ZR-6`; `STORY-198`'s adapter-only fix (already landed, not reopened by me — see §6)
does not touch the port and so does not close this finding.

**The honest narrowing question (not resolved here, per `ZR-6`'s own Coverage verdict in
`zone-rules.md`):** `action`'s legal set today is a 2-member subset of `ProposalState`'s 5 members
(only `APPROVED`/`REJECTED` are ever passed — `backend/src/core/services/approval.py:60-70` calls
`_decide(..., to_state=ProposalState.APPROVED, ...)`, `:72-88` calls
`_decide(..., to_state=ProposalState.REJECTED, ...)`, and `_decide` derives
`action=to_state.value` at `backend/src/core/services/approval.py:128`). Whether the fix widens the
port to accept `ProposalState` outright (accepting 3 semantically-invalid members) or introduces a
narrower purpose-built type is a real design choice STORY-200 (§6) must make, not a mechanical
substitution.

**Full detail, source citations, and the Coverage verdict:** `docs/scrum/wiki/zone-rules.md`, rule
`ZR-6`.

## 2c. `ZR-7` findings — four adapters silently truncate a result set their port promises in full

**`ZR-n`:** `ZR-7` (added to `docs/scrum/wiki/zone-rules.md` this fix round — a genuine, unreported
production defect, not merely a shape/naming issue).

**Severity:** `MAJOR` on all four — this is a real correctness bug in shipping code, not a stylistic
one, per the concrete mechanism below.

**Finding 1 (the live defect):** `backend/src/adapters/persistence/dynamo_maintenance_repository.py:86-97`
(`is_under_maintenance`) issues an UNBOUNDED `query` (`gsi1pk="MAINT" AND gsi1sk <= <now>#�` —
every maintenance window ever created, for every component, no `Limit`), applies a POST-READ
`FilterExpression` on `component_id`/`ends_at`, and discards `LastEvaluatedKey` — it never loops.
DynamoDB applies `FilterExpression` AFTER the 1 MB per-page read limit, so once total maintenance-
window volume exceeds one page, a component genuinely under maintenance can silently receive `False`
from this method (a wrong answer, not an error) — `core/services/decide.py`'s suppression logic then
silently fails to apply. The port's own contract
(`backend/src/core/ports/maintenance_repository.py:34-47`) promises a check over the COMPLETE set of
windows for a component, not a first-page one.

**Findings 2-4 (the same shape, `list_*` methods against an "all" contract):**
`backend/src/adapters/persistence/dynamo_maintenance_repository.py:66-84` (`list_windows`, port
promise "Retrieve all scheduled maintenance windows",
`backend/src/core/ports/maintenance_repository.py:13-19`);
`backend/src/adapters/persistence/dynamo_component_repository.py:28-34` (`list_components`, port
promise "Retrieve all components from the spine",
`backend/src/core/ports/component_repository.py:18-25`);
`backend/src/adapters/persistence/dynamo_signal_repository.py:29-36` (`list_signals`, port promise
"Retrieve every seeded signal", `backend/src/core/ports/signal_repository.py:18-25`);
`backend/src/adapters/persistence/dynamo_proposal_repository.py:172-179` (`list_open`, port promise
"Retrieve all OPEN status proposals... A list of all open proposals",
`backend/src/core/ports/proposal_repository.py:57-64`).

**Why the eight `lint-imports` contracts pass all four:** import-linter has no concept of runtime
pagination behaviour or docstring-promised completeness — this is a live-shaped-dataset correctness
question, structurally outside any static import-graph tool.

**The compliant counter-pattern, in the same directory:**
`backend/src/adapters/persistence/dynamo_observation_repository.py:100-118` (`in_window`'s
`while True` / `ExclusiveStartKey` / `LastEvaluatedKey` loop), with a test-only pagination hook at
`backend/src/adapters/persistence/dynamo_observation_repository.py:23`
(`self._limit: int | None = None  # Hook for testing pagination`) that lets a test force a small page
size without needing a real 1 MB of data — the fix (`STORY-199`, §6) is not a missing capability, it
is an inconsistently-applied one.

**Not in scope for `ZR-7` (checked and excluded):**
`backend/src/adapters/persistence/dynamo_publication_repository.py::list_recent` uses `Limit=limit`
(default 50) and its OWN port docstring promises only "up to `limit` most-recent" — a stated bound,
not an "all"/"every" contract, so honoring it is compliant, not a violation.

**Full detail, source citations, and the Coverage verdict (including the guard's stated
false-positive risk):** `docs/scrum/wiki/zone-rules.md`, rule `ZR-7`.

## 3. `GAP-1` — superseded (kept for the record, not re-litigated)

**Original verdict (now superseded):** the first pass of this report recorded
`backend/src/adapters/persistence/dynamo_proposal_repository.py:286`
(`if action == "approved":`) as an unscored "catalogue gap" (`GAP-1`) — a hardcoded literal duplicating
`ProposalState.APPROVED.value` where the enum is already imported and used correctly 181 lines earlier
in the same file, at `backend/src/adapters/persistence/dynamo_proposal_repository.py:105`
(`if proposal.state == ProposalState.OPEN:`). That observation is factually accurate and unchanged.

**What the fix round corrected:** the original pass treated this as a symptom with no rule id and
simultaneously verdicted `core/ports/proposal_repository.py` `CLEAN` — the quality reviewer's
independent audit found the ROOT CAUSE is the port's own signature (`action: str` instead of a domain
type), scored above as `ZR-6` (§2b), `MAJOR`. `GAP-1` is therefore superseded, not deleted from the
record: `STORY-198` (already landed, quality MAJOR-4, enriched by the orchestrator) fixes the
ADAPTER-ONLY symptom (the literal comparison) and remains worth doing on its own terms, but it does
**not** touch the port and so does not close the `ZR-6` finding — `STORY-200` (§6) is the follow-on
that does.

## 4. `CLEARED` — considered and rejected (AC4)

- **Vendor prose in `core/` (the ~20-occurrence case, STORY-194 AC5's compliant set).** Re-verified
  directly by re-reading every one of the 26 grep-matched lines from §2a's corrected re-derivation:
  all are docstring/comment/attribute-docstring prose, matching ZR-2's three closed compliant forms.
  The six previously-flagged, now-settled citations
  (`backend/src/core/domain/component.py:17`, `backend/src/core/domain/publication.py:35`,
  `backend/src/core/ports/component_repository.py:53`, `backend/src/core/ports/observation_repository.py:5`
  and `backend/src/core/ports/observation_repository.py:7`, `backend/src/core/ports/__init__.py:7`) were
  each re-read directly THIS fix round and confirmed to name a vendor word only inside a
  class/method/module docstring, never as an identifier, annotation, signature, dict key, or stored
  value. **This was ALWAYS verified by direct reading, never by the vendor-word grep — the grep is a
  recall aid, not evidence, for these six specifically (F4 correction, see §2a).** CLEARED — not a
  finding.
- **`DynamoPublicationRepository.list_recent` reading `PROPOSAL#<id>` items to resolve
  `Publication.author`** (`backend/src/adapters/persistence/dynamo_publication_repository.py:73-96`).
  Considered as a candidate "repository owning a key shape it shouldn't" / cross-aggregate reach.
  **CLEARED**: `Publication.author` is explicitly a domain-designated derived-on-read field
  (`backend/src/core/domain/publication.py:71-72`: "Optional author derived on read (not persisted by
  `record`)"); the adapter's `BatchGetItem` against `PROPOSAL#<id>`/`META` items implements that
  documented contract as a storage detail within the SAME zone's own persistence layer. Confirmed
  consistent with `[[persistence-adapters]]` (§5).
- **`dynamo_maintenance_repository.py`'s GSI eventual-consistency window** (a window created seconds
  earlier may be briefly missed). **CLEARED, DISTINCT from the `ZR-7` finding above** — this is a
  documented, PO-accepted (2026-06-14) EVENTUAL-CONSISTENCY trade-off (a brief staleness window), not
  the `ZR-7` defect (a PAGE-SIZE truncation that silently under-reports regardless of consistency
  model, once volume crosses 1 MB). The two are easy to conflate because they live in the same
  method; they are different failure mechanisms with different remedies (consistency trade-offs are
  not fixable by looping; the `ZR-7` truncation is).
- **`dispatch.py::normalize_rows_lenient`'s broad `except ValueError`** (STORY-190). **CLEARED**, with
  a narrowed claim (F4 correction): this stays entirely within `adapters/inbound/dynatrace/` and never
  imports or calls a persistence port (ZR-1). The original CLEARED text claimed "every error class it
  can possibly catch is covered" — that claim is true only for the currently-DISPATCHABLE normalizer
  (`normalize_http_row`, the only entry in `dispatch.py`'s `_NORMALIZERS` registry today); it is NOT
  true of every normalizer FILE in the package, as the next entry shows.
- **`backend/src/adapters/inbound/dynatrace/clickpath_normalizer.py:39` reads
  `row["execution.outcome"]` directly, bypassing `_assembly.require_field`** — against the documented
  policy at `backend/src/adapters/inbound/dynatrace/_assembly.py:20-30` and the pattern
  `backend/src/adapters/inbound/dynatrace/http_normalizer.py:22-23` follows correctly
  (`code = str(require_field(row, "result.status.code"))`). A missing `execution.outcome` here raises
  a bare `KeyError`, NOT a `ValueError` subclass, so it would escape `normalize_rows_lenient`'s
  `except ValueError` net entirely — the exact stall shape STORY-190 closed, reopened for this one
  field. **Adjudicated CLEARED, not a finding, for one specific reason: `clickpath_normalizer.py` is
  UNREACHABLE from the live dispatch path today** — `dispatch.py`'s `_NORMALIZERS` registry
  (`backend/src/adapters/inbound/dynatrace/dispatch.py:45-47`) maps only `"http_monitor_execution"` to
  `normalize_http_row`; nothing calls `normalize_clickpath_row` in production. This is genuinely a
  LATENT hygiene gap, not a live defect — the moment a future story wires clickpath into
  `_NORMALIZERS` (the file exists specifically in anticipation of that), this bare-`KeyError` risk
  becomes live and would need catching THEN. Filed as a minor hygiene item (`STORY-201`, §6) rather
  than left unmentioned, since leaving a landmine for whoever does that wiring next is not free even
  though it costs nothing today.
- **The vendor row inside `RejectedObservationRepository.save(payload=...)` — F3, explicitly
  adjudicated (was previously silent).** `backend/src/adapters/inbound/dynatrace/dispatch.py:57-63`'s
  `RowNormalizationFailure` dataclass (its `row: dict` field, at line 61) carries the RAW DQL row
  (vendor field names like `event.type`, `dt.synthetic.monitor.id`, `dt.entity.synthetic_location`);
  `backend/src/adapters/inbound/dynatrace/adapter.py:43` returns it inside `NormalizationOutcome`;
  `backend/src/composition/pull_loop.py:136` (`payload=failure.row,`) hands it to
  `RejectedObservationRepository.save`; `backend/src/adapters/persistence/
  dynamo_rejected_observation_repository.py:39-45` persists it verbatim (after a float->Decimal pass
  for boto3 serialization only — no field renaming or canonicalization). ZR-1's statement says an
  inbound adapter "returns canonical values only"; taken as a bare literal rule, this raw dict is not
  canonical, and the PO's rule 1 says "vendor vocabulary never leaves it" — the raw row plainly leaves
  the `adapters/inbound/dynatrace/` package. **Adjudicated CLEARED, with the reason written out**: the
  core-owned `RejectedObservationRepository` port ITSELF designates this as the one sanctioned channel
  for raw/unconverted data, analogous to `Provenance`'s carve-out for vendor identifiers in ZR-2 — its
  own docstring (`backend/src/core/ports/rejected_observation_repository.py:1-9`) says the payload is
  "the raw rejected observation (as a dict) so the original shape is recoverable." A quarantine record
  whose entire purpose is auditing WHY normalization failed must preserve the original, un-normalized
  shape — canonicalizing it would defeat the audit it exists for. Two wiki articles independently
  confirm this is DELIBERATE design, not an oversight this audit is the first to notice:
  `docs/scrum/wiki/dynatrace-adapter.md:126-127` ("`RowNormalizationFailure` carries a raw vendor row
  dict, so it deliberately does NOT live in `core/domain/`") and
  `docs/scrum/wiki/ingest-service-and-pull-loop.md:80`
  ("`rejected_repo.save(signal_key=..., reason=..., payload=<raw row>, ...)`"). **Catalogue note (not
  a blocking gap, stated for completeness):** unlike ZR-2, which names the `Provenance` carve-out
  explicitly in its own Statement, `ZR-1`'s text does not currently name this quarantine-payload
  carve-out by name — a future revision of `ZR-1` could add one sentence doing so, mirroring ZR-2's
  style, but nothing here is un-adjudicated or blocking; it is a documentation-completeness candidate,
  not a new finding.
- **The "only `composition` sees both `src.core` and `src.adapters` concretely" precision claim.**
  Re-checked directly across all 58 files: no module outside `composition/` holds a concrete class
  from BOTH zones for dependency-injection purposes. CLEARED — no contradiction found.
- **`core/queries/availability.py` importing `core/services/pipeline.py::collapse`.** CLEARED:
  `pyproject.toml`'s `core-internal-layering` contract places `queries` as the OUTERMOST layer
  specifically so it may import `services`/`ports`/`domain` — compliant direction.

## 5. Wiki cross-check (AC5) — all 11 relevant articles, not 1

**F4 correction:** the original pass checked only `persistence-adapters.md` (1 of 11) while asserting
a blanket "no other wiki article makes a claim this report's findings contradict." That blanket claim
was unearned. Command used to enumerate the relevant set:

```
$ cd docs/scrum/wiki
$ for f in *.md; do grep -l "backend/src/core/\|backend/src/adapters/" "$f"; done
api-five-file-convention.md
architecture-boundary.md
canonical-types-and-ports.md
core-pipeline-and-availability.md
demo-engine.md
dynatrace-adapter.md
ingest-service-and-pull-loop.md
persistence-adapters.md
sample-mode.md
statuspage-publish.md
zone-rules.md
```

11 articles (`zone-rules.md` itself is the yardstick, not something to cross-check against — 10
external articles checked below).

- **`canonical-types-and-ports.md` — ONE REAL CONTRADICTION, filed for update.** Its "Zone 4 core
  logic — moved" section (`docs/scrum/wiki/canonical-types-and-ports.md:159-165`) states: "The pipeline
  (`collapse`/`streak`, STORY-010) and the availability engine (`AvailabilityCalculator`/
  `rollup_group`, STORY-011) — **both in `core/services/`**". This is FALSE as of STORY-078
  (sprint-43): the availability engine has lived in `core/queries/availability.py` since then — and
  this SAME ARTICLE's own History section says so correctly
  (`docs/scrum/wiki/canonical-types-and-ports.md:241`: "sprint-43 (STORY-078): Relocated availability
  read-model to a new core/queries/ package"). The article contradicts itself: its Facts section
  (lines 159-165) was never updated when its own History section (line 241) recorded the move.
  **Filed for update**: both addresses are
  `docs/scrum/wiki/canonical-types-and-ports.md:159-165` (wrong) vs.
  `docs/scrum/wiki/canonical-types-and-ports.md:241` (right) — this report does not edit that article
  (C1/out of this story's scope), it names the contradiction for the article's next touch to fix.
- **`dynatrace-adapter.md`** — checked against F3's clickpath adjudication and the raw-row CLEARED
  entry above; both are CONFIRMED, not contradicted (see §4's citations to
  `docs/scrum/wiki/dynatrace-adapter.md`, lines 126-127).
- **`ingest-service-and-pull-loop.md`** — checked against F3's raw-row CLEARED entry; CONFIRMED, not
  contradicted (`docs/scrum/wiki/ingest-service-and-pull-loop.md`, line 80).
- **`persistence-adapters.md`** — checked against every `adapters/persistence/` claim this report
  makes, including the NEW `ZR-7` findings. **No contradiction, but a real silence**: this article
  documents `is_under_maintenance`'s GSI eventual-consistency trade-off
  (`docs/scrum/wiki/persistence-adapters.md`, line 34) but says nothing about the
  pagination/`LastEvaluatedKey` question — it is silent on `ZR-7`, not wrong about it. Not filed as a
  contradiction (silence isn't a false claim); a candidate for that article's next touch, once
  `STORY-199` lands, to document the fix.
- **`api-five-file-convention.md`** — checked its topology-endpoint description
  (`docs/scrum/wiki/api-five-file-convention.md`, line 36: "one entry per component from
  `ComponentRepository.list_components()`"). Not a contradiction (it doesn't claim anything about
  pagination either way), but directly downstream of the `ZR-7` `list_components` finding — noted as a
  candidate, not filed.
- **`architecture-boundary.md`** — `code_refs` are the four zone `__init__.py` files only; no claim
  specific enough to contradict or confirm anything in this report.
- **`core-pipeline-and-availability.md`** — its one relevant line
  (`docs/scrum/wiki/core-pipeline-and-availability.md`, line 187) describes the availability
  calculator calling
  `is_under_maintenance(component_id, cycle_start)`; it makes no claim about that call's completeness
  under load, so no contradiction with `ZR-7`.
- **`demo-engine.md`, `sample-mode.md`, `statuspage-publish.md`** — checked their `core/`/`adapters/`
  citations against this report's specific claims (the `dynamo_sample_mode_repository.py`
  single-row get/set, `dynamo_publication_repository.py::list_recent`'s stated `limit` bound); no
  overlap with any finding or CLEARED entry above, no contradiction.

**One contradiction filed** (`canonical-types-and-ports.md`), ten articles checked, none filed
silently as "no contradiction" without being read.

## 6. Proposed stories

`STORY-198` is **already landed** in `.scrum/backlog.yaml` by the orchestrator (quality MAJOR-4,
enriched with blast radius + a test trap) — not re-filed or re-described in detail here; it fixes the
ADAPTER-ONLY symptom (the `dynamo_proposal_repository.py` literal, §3). The three below are NEW,
proposed from this fix round's corrected findings, ids `STORY-199` onward per instruction.

### STORY-199 — Paginate the four `adapters/persistence/` methods that silently truncate against an "all" port contract

- **Type:** defect (a live, unreported production correctness bug — `ZR-7`, `MAJOR`)
- **Estimate:** 3 (fibonacci) — four methods across four files, each needing the same
  `ExclusiveStartKey`/`LastEvaluatedKey` loop `dynamo_observation_repository.py::in_window` already
  uses, plus a test-only pagination hook per file (mirroring `_limit`) so each fix can be DEMONSTRATED
  failing pre-fix without needing a real 1 MB of DynamoDB data.
- **Offending citations:**
  `backend/src/adapters/persistence/dynamo_maintenance_repository.py:86-97` (`is_under_maintenance`,
  the live defect) and `:66-84` (`list_windows`);
  `backend/src/adapters/persistence/dynamo_component_repository.py:28-34` (`list_components`);
  `backend/src/adapters/persistence/dynamo_signal_repository.py:29-36` (`list_signals`);
  `backend/src/adapters/persistence/dynamo_proposal_repository.py:172-179` (`list_open`).
- **Context:** see `ZR-7` in `docs/scrum/wiki/zone-rules.md` and §2c above for the full mechanism.
  `is_under_maintenance` is the highest-priority of the four: it can make `decide.py` fail to suppress
  a status change for a component that IS under maintenance, silently, past a real-data page boundary.
- **Acceptance criteria (testable):**
  - AC1: Each of the five call sites (the four `list_*`/boolean methods above) loops on
    `LastEvaluatedKey` exactly as `dynamo_observation_repository.py::in_window` already does, rather
    than reading a single page.
  - AC2: Each gains a test-only page-size hook (mirroring `_limit` at
    `backend/src/adapters/persistence/dynamo_observation_repository.py:23`), and a test that sets it
    small, seeds MORE rows than one page, and asserts the method still returns/checks the COMPLETE
    set — demonstrated FAILING against
    the pre-fix code (per the project's mutation/pre-fix-demonstration standing rule) before the fix
    lands, then passing after.
  - AC3: `is_under_maintenance` specifically gets a test proving a component whose ONLY matching
    window is on a page past the hook's forced small page size still returns `True` — the exact
    silent-`False` shape this finding describes.
  - AC4: Existing contract tests for all four methods continue to pass unchanged for the
    single-page case.

### STORY-200 — Give `ProposalRepository.record_approval_event` a domain-typed `action` parameter

- **Type:** defect (a real port-signature boundary finding — `ZR-6`, `MAJOR`)
- **Estimate:** 2 (fibonacci)
- **Offending citation:** `backend/src/core/ports/proposal_repository.py:45` (`action: str`).
- **Context:** see `ZR-6` in `docs/scrum/wiki/zone-rules.md` and §2b above. The refinement session for
  this story must resolve the narrowing question §2b states plainly and does not resolve itself:
  widen to the full `ProposalState` (accepting that 3 of 5 members are semantically invalid
  `action`s) or introduce a narrower purpose-built type expressing exactly the 2-member legal set.
  **Overlap note, stated explicitly rather than assumed away:** `STORY-198` (already landed, not
  reopened by this story) fixes the ADAPTER's comparison (`backend/src/adapters/persistence/
  dynamo_proposal_repository.py`, line 286) to compare against `ProposalState.APPROVED.value` instead
  of the literal `"approved"` — but leaves `action`'s TYPE at the port as `str`. If `STORY-200` lands
  AFTER `STORY-198` and changes the port to accept `ProposalState` directly, `STORY-198`'s own
  `.value`-based comparison may become unnecessary (a `ProposalState`-typed parameter could compare
  directly against `ProposalState.APPROVED`) — this reconciliation should happen at `STORY-200`
  refinement, not be assumed here.
- **Acceptance criteria (testable):**
  - AC1: `ProposalRepository.record_approval_event`'s abstract signature no longer types `action` as a
    bare `str`; it uses a domain type expressing either the full `ProposalState` or a narrower
    purpose-built approval-action type (refinement decides which, per the note above).
  - AC2: `DynamoProposalRepository.record_approval_event`'s implementation and every caller
    (`core/services/approval.py`'s `_decide`) are updated to match the new signature.
  - AC3: A test constructs the new type with an INVALID value (if the narrower-type option is chosen)
    or asserts the 3 semantically-invalid `ProposalState` members are documented as never passed (if
    the full-enum option is chosen) — whichever option refinement picks must leave an explicit,
    testable trace of the decision, not silence.
  - AC4: Existing `DynamoProposalRepository`/`ApprovalService` contract tests continue to pass.

### STORY-201 — Clickpath normalizer hygiene: use `require_field` for `execution.outcome` (batched MINOR)

- **Type:** chore (latent hygiene, currently unreachable — not a live defect)
- **Estimate:** 1 (fibonacci)
- **Offending citation:** `backend/src/adapters/inbound/dynatrace/clickpath_normalizer.py:39`
  (`row["execution.outcome"]`).
- **Context:** see §4's `CLEARED`-with-reason entry. Currently unreachable (`clickpath` is absent from
  `dispatch.py`'s `_NORMALIZERS` registry), so this is preventive hygiene, not a hotfix — but the fix
  is one line and removes a landmine for whoever next wires clickpath into the live dispatch path.
- **Acceptance criteria (testable):**
  - AC1: `normalize_clickpath_row` reads `execution.outcome` via
    `_assembly.require_field(row, "execution.outcome")`, matching `http_normalizer.py`'s pattern,
    raising `MalformedDqlRowError` (a `ValueError` subclass, quarantine-net-compatible) on a missing
    field instead of a bare `KeyError`.
  - AC2: A test asserts a clickpath row missing `execution.outcome` raises `MalformedDqlRowError`, not
    `KeyError`.
  - AC3: Existing `clickpath_normalizer` tests continue to pass unchanged for present-field inputs.

## 7. Citation-resolution sweep (AC re-derivation requirement) — strengthened (F4)

**v1 limitation, stated honestly:** the original sweep only checked "does the file have >= N lines" —
which cannot catch a citation pointing at the WRONG line of a real, long-enough file. That is exactly
the class of error the fix round found — the port's `action: str` parameter was cited one line too
early, at the `actor: str` line instead — a real file, long enough, wrong line.

**v2, built this fix round** (scratchpad script
`citation_sweep_story195_v2.py`): for every `` `path:line` `` citation immediately followed by a
parenthesized backtick code excerpt — the `` `path:line` (`code excerpt`) `` shape this report uses
throughout — extracts that excerpt and confirms it is a substring of the actual file's cited line
range, not merely that the file is long enough. Citations with no such excerpt fall back to the v1
line-count check and are reported as such, never silently upgraded to a false confidence.

**Proof the strengthened check actually discriminates (shown failing, per the project's
guard-must-be-shown-red rule), run in an ISOLATED scratch file so it cannot contaminate the sweep of
this report itself:** a scratch markdown file citing the proposal-repository port's `actor` line
(the one immediately BEFORE the real `action: str` line) with the anchor text `action: str` deliberately
attached to the wrong line number, alongside the correct citation on the following line. Output:

```
FAIL backend/src/core/ports/proposal_repository.py:44 (anchor 'action: str' NOT found in lines 44-44)
OK   backend/src/core/ports/proposal_repository.py:45 (file has 64 lines) [anchor matched: 'action: str']

Extracted 2 citation occurrence(s), 2 distinct (path, line-spec) pair(s) checked -- 1 content-anchor-verified, 0 line-count-only (no anchor present), 1 failure(s).
```

The wrong citation fails, the right one passes — the check discriminates, not merely reports.

**Real run against THIS report** (final version, after all fix-round edits, including a first pass
that itself found several self-inflicted bare-path citations in this report's OWN new prose — fixed
before this final clean run):

Command: `python citation_sweep_story195_v2.py docs/scrum/sprints/2026-07-31-sprint-66/audit-core-adapters.md`

```
OK   backend/src/core/domain/component.py:17 (file has 33 lines) [line-count only, no anchor]
OK   backend/src/core/domain/publication.py:35 (file has 80 lines) [line-count only, no anchor]
OK   backend/src/core/ports/component_repository.py:53 (file has 56 lines) [line-count only, no anchor]
OK   backend/src/core/ports/observation_repository.py:7 (file has 49 lines) [line-count only, no anchor]
OK   backend/src/core/ports/proposal_repository.py:45 (file has 64 lines) [anchor matched: 'action: str']
OK   backend/src/core/ports/proposal_repository.py:32 (file has 64 lines) [line-count only, no anchor]
OK   backend/src/adapters/persistence/dynamo_proposal_repository.py:286 (file has 316 lines) [anchor matched: 'if action == "approved":']
OK   backend/src/core/services/approval.py:60-70 (file has 139 lines) [line-count only, no anchor]
OK   backend/src/core/services/approval.py:128 (file has 139 lines) [line-count only, no anchor]
OK   backend/src/adapters/persistence/dynamo_maintenance_repository.py:86-97 (file has 111 lines) [anchor matched: 'is_under_maintenance']
OK   backend/src/core/ports/maintenance_repository.py:34-47 (file has 59 lines) [line-count only, no anchor]
OK   backend/src/adapters/persistence/dynamo_maintenance_repository.py:66-84 (file has 111 lines) [line-count only, no anchor]
OK   backend/src/core/ports/maintenance_repository.py:13-19 (file has 59 lines) [line-count only, no anchor]
OK   backend/src/adapters/persistence/dynamo_component_repository.py:28-34 (file has 64 lines) [anchor matched: 'list_components']
OK   backend/src/core/ports/component_repository.py:18-25 (file has 56 lines) [line-count only, no anchor]
OK   backend/src/adapters/persistence/dynamo_signal_repository.py:29-36 (file has 48 lines) [anchor matched: 'list_signals']
OK   backend/src/core/ports/signal_repository.py:18-25 (file has 35 lines) [line-count only, no anchor]
OK   backend/src/adapters/persistence/dynamo_proposal_repository.py:172-179 (file has 316 lines) [anchor matched: 'list_open']
OK   backend/src/core/ports/proposal_repository.py:57-64 (file has 64 lines) [line-count only, no anchor]
OK   backend/src/adapters/persistence/dynamo_observation_repository.py:100-118 (file has 151 lines) [line-count only, no anchor]
OK   backend/src/adapters/persistence/dynamo_observation_repository.py:23 (file has 151 lines) [anchor matched: 'self._limit: int | None = None  # Hook for testing pagination']
OK   backend/src/adapters/persistence/dynamo_proposal_repository.py:105 (file has 316 lines) [anchor matched: 'if proposal.state == ProposalState.OPEN:']
OK   backend/src/core/ports/observation_repository.py:5 (file has 49 lines) [line-count only, no anchor]
OK   backend/src/core/ports/__init__.py:7 (file has 40 lines) [line-count only, no anchor]
OK   backend/src/adapters/persistence/dynamo_publication_repository.py:73-96 (file has 121 lines) [line-count only, no anchor]
OK   backend/src/core/domain/publication.py:71-72 (file has 80 lines) [line-count only, no anchor]
OK   backend/src/adapters/inbound/dynatrace/clickpath_normalizer.py:39 (file has 42 lines) [anchor matched: 'row["execution.outcome"]']
OK   backend/src/adapters/inbound/dynatrace/_assembly.py:20-30 (file has 118 lines) [line-count only, no anchor]
OK   backend/src/adapters/inbound/dynatrace/http_normalizer.py:22-23 (file has 31 lines) [line-count only, no anchor]
OK   backend/src/adapters/inbound/dynatrace/dispatch.py:45-47 (file has 149 lines) [line-count only, no anchor]
OK   backend/src/adapters/inbound/dynatrace/dispatch.py:57-63 (file has 149 lines) [line-count only, no anchor]
OK   backend/src/adapters/inbound/dynatrace/adapter.py:43 (file has 43 lines) [line-count only, no anchor]
OK   backend/src/composition/pull_loop.py:136 (file has 253 lines) [anchor matched: 'payload=failure.row,']
OK   backend/src/core/ports/rejected_observation_repository.py:1-9 (file has 34 lines) [line-count only, no anchor]
OK   docs/scrum/wiki/dynatrace-adapter.md:126-127 (file has 278 lines) [line-count only, no anchor]
OK   docs/scrum/wiki/ingest-service-and-pull-loop.md:80 (file has 333 lines) [line-count only, no anchor]
OK   docs/scrum/wiki/canonical-types-and-ports.md:159-165 (file has 278 lines) [line-count only, no anchor]
OK   docs/scrum/wiki/canonical-types-and-ports.md:241 (file has 278 lines) [line-count only, no anchor]

Extracted 55 citation occurrence(s), 41 distinct (path, line-spec) pair(s) checked -- 10 content-anchor-verified, 31 line-count-only (no anchor present), 0 failure(s).

**Re-recorded by the orchestrator after the STORY-195 re-review (2026-07-31).** The previously
recorded run (`52 / 38 / 0 failures`) was real but stale — it predated the fix round's own final
prose edits, which introduced THREE new self-inflicted bare-path citations
(`ingest_service.py:121`, `status_publisher.py:14-19`, `run.py:182-184`) in the very triage
section that documents this defect class. Re-running the committed text produced 3 FAILs and
exit 1. The three prose citations now carry full repo-relative paths and the run above is clean
at exit 0. Recording this rather than quietly substituting the number, per the bar STORY-194 set.
```

**Real run against `docs/scrum/wiki/zone-rules.md`**, since this fix round also edits it (the
coordinator's own instruction): run as a courtesy, not a STORY-195 obligation (that article is
STORY-194/197's), and its result is TRIAGED here rather than left as an unexplained failure count,
per "STORY-196 will inherit this script and must not inherit false confidence from it":

```
FAIL code-boundary-discipline.md:28-29 (file does not exist)
FAIL backend/src/core/services/ingest_service.py:121 (anchor 'IngestService.ingest_observations' NOT found in lines 121-121)
FAIL code-boundary-discipline.md:31-32 (file does not exist)
FAIL backend/src/core/ports/status_publisher.py:14-19 (anchor 'StatusPublisherPort.publish(self, change: StatusChange) -> None' NOT found in lines 14-19)
FAIL backend/src/composition/run.py:182-184 (anchor 'settings = load_settings(); secrets =\n  load_live_secrets(); config = load_config(settings.config_dir)' NOT found in lines 182-184)
[... 42 further citations, all OK, omitted for length — full raw output available in the
implementer's session ...]

Extracted 59 citation occurrence(s), 47 distinct (path, line-spec) pair(s) checked -- 10 content-anchor-verified, 32 line-count-only (no anchor present), 5 failure(s).
```

**All 5 failures manually triaged, none a real broken citation:**
- 2× `code-boundary-discipline.md` — a Claude memory file (`C:\Users\Hyndhava\.claude\...\memory\`),
  outside this script's `REPO_ROOT`; STORY-194's own sweep resolved these correctly against the memory
  directory. Verified present and accurate by direct read of that file.
- `backend/src/core/services/ingest_service.py:121` — the anchor `IngestService.ingest_observations` is a SYMBOL reference
  (naming the enclosing method), not a literal excerpt; the actual line 121 IS
  `self._rejected_repo.save(` (verified directly), matching the article's prose exactly. False
  positive of the heuristic, not a wrong citation.
- `backend/src/core/ports/status_publisher.py:14-19` — same SYMBOL-style class, `StatusPublisherPort.publish(self, change:
  StatusChange) -> None`; the real lines 14-19 correctly define exactly that class and method, just
  split across two separate source lines rather than one continuous string. Verified directly.
- `backend/src/composition/run.py:182-184` — the anchor is a semicolon-joined PARAPHRASE of three real, separate source lines
  (`settings = load_settings()` / `secrets = load_live_secrets()` / `config =
  load_config(settings.config_dir)`, verified directly at those exact three lines) — a legitimate
  compression for readability, not a literal quote, so a strict substring check against the real
  newline-separated source correctly cannot find it verbatim.

None of the five are this fix round's own additions — all five are pre-existing STORY-194 citations
in styles (symbol-reference, semicolon-paraphrase, memory-file) the v2 heuristic cannot yet
distinguish from a wrong citation. Recorded here rather than silently dismissed, per instruction that
STORY-196 must not inherit false confidence from this script.

**Known, triaged limitations of the v2 heuristic (say so plainly, so STORY-196 does not over-trust
it):** (1) a citation into `code-boundary-discipline.md` (a Claude memory file, not a repo file) is
outside `REPO_ROOT` and always reports FAIL from this script — STORY-194's own sweep correctly
resolved it against the memory directory instead; not a real failure. (2) A "`ClassName.method`" or
"`ClassName.method(signature)`" SYMBOL-style citation (naming what a line lives inside, not quoting it
verbatim) is a legitimate, different documentation style this heuristic cannot distinguish from a
literal-excerpt anchor, and will false-FAIL — manually verified accurate in every instance found (see
`zone-rules.md`'s citations of `ingest_service.py`'s `IngestService.ingest_observations` method and
`status_publisher.py`'s `StatusPublisherPort.publish` signature). (3) A multi-line excerpt
PARAPHRASED with semicolons joining several real source lines (the `composition/run.py` config-
resolution citation) will false-FAIL a strict substring check against the real (newline-separated)
source — also manually verified accurate. None of these three classes is a broken citation; all three
are stated here so a
future reader of the raw FAIL count does not mistake heuristic limitation for citation error.

## 8. Gate — real output (F4 correction: no more "expected" language)

`REQUIRE_DYNAMO=1 DYNAMO_ENDPOINT_URL=http://127.0.0.1:8021`, five backend DoD commands via
`yt_gate.py --only`, confirmed each selector actually matched its intended command (STORY-178):

```
Command: `REQUIRE_DYNAMO=1 DYNAMO_ENDPOINT_URL=http://127.0.0.1:8021 python .claude/skills/yourteam/scripts/yt_gate.py --only pytest --only lint_imports_command --only "ruff check" --only "ruff format" --only cfn-lint`
Run by the ORCHESTRATOR at commit `2c29514` (the implementer was killed by a usage limit before it
could paste this; the placeholder it left is the defect the STORY-195 re-review flagged CRITICAL).
Only this report's own prose has changed since that commit, so no gate command's input changed.

```
yt_gate: [1/5] pytest
yt_gate:   -> PASS
yt_gate: [2/5] python -c "from importlinter.cli import lint_imports_command; lint_imports_command()"
yt_gate:   -> PASS
yt_gate: [3/5] ruff check .
yt_gate:   -> PASS
yt_gate: [4/5] ruff format --check .
yt_gate:   -> PASS
yt_gate: [5/5] cfn-lint infra/stack.yaml
yt_gate:   -> PASS
```

**Pass/skip counts (AC6):** `pytest` **685 passed, 0 SKIPPED** (`REQUIRE_DYNAMO=1`, so a
Docker-less run would FAIL rather than silently skip ~53 tests — amendment A6); import-linter
**8 contracts kept, 0 broken**; `ruff check` clean; `ruff format --check` clean (242 files);
`cfn-lint` clean. Exit code 0 on all five. Merged verbatim into `.scrum/sprint-current.yaml`'s
`dod_evidence`.
```

## 9. Diff-scope proof (C1) — real output

```
$ git diff --name-only d4ad03e..HEAD -- backend/src frontend config
Command: `git diff --name-only d4ad03e..HEAD -- backend/src frontend config`

```
(no output — the command printed nothing)
```

Empty output means **zero** files under `backend/src/`, `frontend/` or `config/` were touched
between the sprint start commit and HEAD, so constraint C1 ("nothing is fixed inline") holds for
this story. Verified independently by the orchestrator, not taken from the implementer's report.
```

Empty — C1 holds for the fix round's own commits too (only `docs/scrum/` files touched: this report,
`docs/scrum/wiki/zone-rules.md`, and the `STORY-199`/`STORY-200`/`STORY-201` story files).

## History

- 2026-07-31: STORY-195 findings report authored. 58/58 files enumerated and read (31 `core`, 27
  `adapters`). Zero `ZR-1..ZR-5` violations found. One catalogue gap (`GAP-1`) found and reported as
  an unscored observation. Five `CLEARED` entries recorded. Wiki cross-check covered 1 of 11 relevant
  articles.
- 2026-07-31 (quality-review fix round): spec `NOT_MET` on AC2 (re-derivability); quality
  `FIX_REQUIRED`, 4 MAJOR + 9 minor, from an independent audit of ~46 of the 58 files. Corrected: (F1)
  a real, previously-unreported production defect — four `adapters/persistence/` files silently
  truncate a result set their port promises in full past a 1 MB DynamoDB page — added as new rule
  `ZR-7` (`MAJOR`, 4 findings) and filed `STORY-199`; (F2) `GAP-1`'s root cause was the PORT signature,
  not the adapter — added as new rule `ZR-6` (`MAJOR`) superseding `GAP-1`, and filed `STORY-200`
  (`STORY-198`, already landed, remains the adapter-only partial fix); (F3) the raw-vendor-row
  question inside `RejectedObservationRepository.save` was silently un-adjudicated — now `CLEARED`
  explicitly, with the reasoning and two confirming wiki citations; the clickpath `require_field`
  bypass was similarly silent — now `CLEARED`-with-reason (latent, unreachable) and filed as
  `STORY-201`; (F4) the vendor-word grep's claimed "28 lines" corrected to a reproducible 26 (pattern
  fixed from `dynamodb` to `dynamo`), with the correction that 4 of the 6 previously-"settled"
  citations were never actually backed by that grep in the first place (always direct reading); a
  citation off-by-one (`:44` -> `:45`) and an arithmetic error ("four lines"/"180 lines" -> 181 lines,
  the real gap between the two cited lines) fixed; §8/§9 re-run for real output instead of "expected"
  language; the wiki cross-check widened from 1 to all 11 relevant articles, filing one real
  contradiction (`canonical-types-and-ports.md`'s stale "both in `core/services/`" claim about the
  availability engine, which has lived in `core/queries/` since STORY-078 — the article's own History
  section already said so, uncorrected in its Facts section); (F5) §1 gained an explicit,
  per-module-group statement of what question was actually asked and what evidence backs each
  verdict, rather than a uniform `CLEAN` implying 58 reads of equal depth. The citation-resolution
  sweep was strengthened from a line-count-only check (v1) to a content-anchor check (v2), proven to
  discriminate by feeding it a deliberately wrong citation and confirming it fails while the correct
  one passes, then run against both this report and `docs/scrum/wiki/zone-rules.md` (which this fix
  round also edits, per direct instruction, to add `ZR-6`/`ZR-7`) — v2's known false-positive classes
  (memory-file citations, symbol-style citations, semicolon-paraphrased multi-line excerpts) are
  stated plainly rather than left as unexplained failures, and one genuinely pre-existing bare-path
  citation in `zone-rules.md` (unrelated to this fix round's own additions) was corrected in passing.
