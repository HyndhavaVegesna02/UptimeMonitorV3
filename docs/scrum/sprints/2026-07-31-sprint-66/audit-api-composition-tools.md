# STORY-196 — Audit findings: `api` + `composition` + the `tools/` -> `backend/src/` one-way boundary

Point-in-time findings report. Sprint history, **not** the wiki — this describes the codebase at
`sprint-66` HEAD `10ee45aee4ceb44a11597a2ec6d481724f922ab7` for the ORIGINAL pass, re-verified and
extended at HEAD `6ece7f8` for the FIX ROUND below (see History). Must never be re-stamped later as
if still current. Yardstick: `docs/scrum/wiki/zone-rules.md` (`ZR-1..ZR-8` as of this fix round —
`ZR-1..ZR-7` landed by STORY-194/195, `ZR-8` landed by this story's own quality-review fix round)
plus the eight `lint-imports` contracts it links to (`docs/scrum/wiki/architecture-boundary.md`).
Same report contract as `docs/scrum/sprints/2026-07-31-sprint-66/audit-core-adapters.md` (STORY-195).

## FIX ROUND (2026-07-31) — what changed and why

Spec verdict: PASS on all six AC (independently re-implemented the `ZR-3` sweep from this report's
own prose description and got byte-identical output — the sweep and the enumeration are sound).
Quality verdict: `FIX_REQUIRED`, 4 MAJOR + 7 minor, from an independent re-audit of all 13
`composition/` modules, `api/dependencies.py`, the six `service.py` files, and the `tools/` boundary
crossers (it corroborated that `api/` is genuinely clean and that the directional half of the
one-way rule holds).

- **F1 — the biggest miss:** `composition/seed_dynamo.py` is adapter-shaped (raw DynamoDB
  persistence, a hand-built key schema) and was verdicted `CLEAN`. See §1/§4/§5; landed as `ZR-8`
  finding 1 in `zone-rules.md`; filed `STORY-205`.
- **F2 — two silent holes on the `tools/` boundary itself:** the `_assembly` private-module import
  (`query_grammar.py`/`store.py`) was never adjudicated; the directional half of the "one-way
  boundary" this report is titled for was never verified with a recorded command. See new §3e.
- **F3 — §3c's ledger did not balance** (15 collisions, 6 `MUST-IMPORT-FROM-SRC`, only 8 `CLEARED`
  line-entries — `tools/demo_engine/store.py:22`'s own numeral hit unadjudicated) **and misread `tools/demo_loop_gate/harness.py:964`**
  (real content is `print(json.dumps(evidence, indent=2, default=str))`, not
  `print("=" * 78)`). Both corrected in §3c; §7 reconciled.
- **F4 — the `MAJOR` rating for the credential pair was argued against the wrong comparison:** five
  more `env_matrix.py` env-var key-name literals sit five lines above the credential pair with the
  identical rename-drift mechanism, never listed. Added to §3c; `STORY-202` widened (§6).
- **F5 — the minors:** the sweep's real blind-spot class stated honestly (12 of 20 module-level
  UPPER_CASE constants under `backend/src/` are non-`ast.Constant`-valued and invisible to it,
  including `ZR-3`'s OWN compliant reference `PROVISIONAL_STATUS_MAPPING`); the shape-(ii) count
  corrected (6 tree-wide, not 5, with the 6th correctly out of scope by definition, not miscounted);
  the sweep scripts committed under `tools/`; §5's "five" keyword arguments corrected to six; §11's
  diff-scope base stated against both commit ranges; `backend/src/composition/orchestrate.py:95-98` excluded from the
  "routes and returns unchanged" generalisation.

Every item below marked "(F1)"/"(F2)"/etc. is this fix round's correction; everything else is the
original pass, unchanged where it was already correct.

## 1. Enumeration (AC1)

Command, run from the repo root:

```
$ cd backend/src && find api -name "*.py" -not -path "*__pycache__*" | wc -l
55
$ cd backend/src && find composition -name "*.py" -not -path "*__pycache__*" | wc -l
13
$ find tools -name "*.py" -not -path "*__pycache__*" | wc -l
17
```

`api` **55**, `composition` **13**, `tools` **17** — total **85**, matches planning's V1 exactly. No
mismatch to report.

Verdict legend: `CLEAN` — no finding. `ZR-n` — violates that catalogue rule (§2). `GAP-2` — the
historical/working name for `ZR-8` finding 2 (§4), landed as a scored `MAJOR` this fix round, not an
unscored observation any longer.

### Evidence basis per module group (F5 discipline, carried over from STORY-195's review) —
what question was actually asked of each group, and how

- **`composition/` (13 files) — read in full, every one.** Judged against ZR-5 (do the two
  composition roots, `run.py::main` / `app.py::create_app`, resolve `CONFIG_DIR` and every other
  behaviour-changing setting identically?), plus the open-ended questions the brief poses
  explicitly: does anything here decide when it should only wire; is any wiring duplicated between
  the two roots; does either root read config through a path the other doesn't. This is the
  smallest of the three zones and the highest-judgement one, so it got the most uniform full-read
  treatment.
- **`tools/` (17 files) — read in full, every one**, plus a written, executed AST sweep (§3) rather
  than a hand read alone — ZR-3's whole point is that a duplicated literal is invisible to casual
  reading (nobody reads two files side by side comparing every string), so the mechanical sweep is
  the actual evidence for this zone's `CLEAN`/`ZR-3` split, with the full read providing the
  semantic judgement (MUST-IMPORT-FROM-SRC vs INDEPENDENT) the sweep cannot make on its own.
- **`api/` (55 files) — mixed depth, stated per file-type, not a uniform "CLEAN".** All 9
  `service.py` and all 9 `validation.py` (the two file types most likely to carry decide-vs-translate
  or business-logic drift) were read in FULL — 18 files. `decisions/controller.py`,
  `decisions/__init__.py`, `health/controller.py`, `health/__init__.py`, all 5 `_shared/*.py`
  (including `_shared/__init__.py`), `api/dependencies.py`, `api/__init__.py`, `api/v1/__init__.py`
  were also read in FULL — 12 more files, 30 total full reads. The remaining 8
  `controller.py` and 9 `models.py`, plus 8 per-feature `__init__.py` router re-exports (25 files)
  were verified by TWO targeted greps, not a full
  read: (a) every `from src...`/`import src...` line in `api/`, confirming each resolves to only
  its own feature package, `src.core`, `src.api.v1._shared`, or `src.api.dependencies` (§4); (b)
  every `models.py` grepped for `def `/`model_validator`/`field_validator`/`computed_field` —
  zero matches, confirming no feature's DTOs carry embedded logic. The 8 remaining per-feature
  `__init__.py` router re-exports (one-line files) were seen via the same import grep. This is
  stated explicitly rather than left as a uniform `CLEAN`, per STORY-195's own review finding
  that a bulk `CLEAN` overstates equal-depth reads that did not happen.

### `api/` (55 files)

| # | File | Verdict |
|---|------|---------|
| 1 | `api/__init__.py` | CLEAN (full read) |
| 2 | `api/dependencies.py` | CLEAN (full read — see AC4 precision note, §5) |
| 3 | `api/v1/__init__.py` | CLEAN (full read) |
| 4 | `api/v1/_shared/__init__.py` | CLEAN (full read) |
| 5 | `api/v1/_shared/errors.py` | CLEAN (full read) |
| 6 | `api/v1/_shared/middleware.py` | CLEAN (full read) |
| 7 | `api/v1/_shared/validation.py` | CLEAN (full read) |
| 8 | `api/v1/_shared/windowing.py` | CLEAN (full read) |
| 9 | `api/v1/approvals/__init__.py` | CLEAN (import grep) |
| 10 | `api/v1/approvals/controller.py` | CLEAN (import grep) |
| 11 | `api/v1/approvals/models.py` | CLEAN (no-embedded-logic grep) |
| 12 | `api/v1/approvals/service.py` | CLEAN (full read) |
| 13 | `api/v1/approvals/validation.py` | CLEAN (full read) |
| 14 | `api/v1/availability/__init__.py` | CLEAN (import grep) |
| 15 | `api/v1/availability/controller.py` | CLEAN (import grep) |
| 16 | `api/v1/availability/models.py` | CLEAN (no-embedded-logic grep) |
| 17 | `api/v1/availability/service.py` | CLEAN (full read) |
| 18 | `api/v1/availability/validation.py` | CLEAN (full read) |
| 19 | `api/v1/components/__init__.py` | CLEAN (import grep) |
| 20 | `api/v1/components/controller.py` | CLEAN (import grep) |
| 21 | `api/v1/components/models.py` | CLEAN (no-embedded-logic grep) |
| 22 | `api/v1/components/service.py` | CLEAN (full read) |
| 23 | `api/v1/components/validation.py` | CLEAN (full read) |
| 24 | `api/v1/decisions/__init__.py` | CLEAN (full read) |
| 25 | `api/v1/decisions/controller.py` | CLEAN (full read) |
| 26 | `api/v1/decisions/models.py` | CLEAN (no-embedded-logic grep) |
| 27 | `api/v1/decisions/service.py` | CLEAN (full read) |
| 28 | `api/v1/decisions/validation.py` | CLEAN (full read) |
| 29 | `api/v1/health/__init__.py` | CLEAN (full read) |
| 30 | `api/v1/health/controller.py` | CLEAN (full read — ZR-4's documented 2-file exception) |
| 31 | `api/v1/history/__init__.py` | CLEAN (import grep) |
| 32 | `api/v1/history/controller.py` | CLEAN (import grep) |
| 33 | `api/v1/history/models.py` | CLEAN (no-embedded-logic grep) |
| 34 | `api/v1/history/service.py` | CLEAN (full read) |
| 35 | `api/v1/history/validation.py` | CLEAN (full read) |
| 36 | `api/v1/maintenance/__init__.py` | CLEAN (import grep) |
| 37 | `api/v1/maintenance/controller.py` | CLEAN (import grep) |
| 38 | `api/v1/maintenance/models.py` | CLEAN (no-embedded-logic grep) |
| 39 | `api/v1/maintenance/service.py` | CLEAN (full read) |
| 40 | `api/v1/maintenance/validation.py` | CLEAN (full read) |
| 41 | `api/v1/publications/__init__.py` | CLEAN (import grep) |
| 42 | `api/v1/publications/controller.py` | CLEAN (import grep) |
| 43 | `api/v1/publications/models.py` | CLEAN (no-embedded-logic grep) |
| 44 | `api/v1/publications/service.py` | CLEAN (full read) |
| 45 | `api/v1/publications/validation.py` | CLEAN (full read) |
| 46 | `api/v1/sample_mode/__init__.py` | CLEAN (import grep) |
| 47 | `api/v1/sample_mode/controller.py` | CLEAN (import grep) |
| 48 | `api/v1/sample_mode/models.py` | CLEAN (no-embedded-logic grep) |
| 49 | `api/v1/sample_mode/service.py` | CLEAN (full read) |
| 50 | `api/v1/sample_mode/validation.py` | CLEAN (full read) |
| 51 | `api/v1/topology/__init__.py` | CLEAN (import grep) |
| 52 | `api/v1/topology/controller.py` | CLEAN (import grep) |
| 53 | `api/v1/topology/models.py` | CLEAN (no-embedded-logic grep) |
| 54 | `api/v1/topology/service.py` | CLEAN (full read) |
| 55 | `api/v1/topology/validation.py` | CLEAN (full read) |

55 files listed, 55 accounted for, 0 findings. 30 by full read, 25 by targeted, reproducible grep
(stated per-file above, not asserted in bulk) — re-derivable via
`grep -c "(full read" docs/scrum/sprints/2026-07-31-sprint-66/audit-api-composition-tools.md` against
this file's own table.

### `composition/` (13 files)

| # | File | Verdict |
|---|------|---------|
| 1 | `composition/__init__.py` | CLEAN |
| 2 | `composition/app.py` | CLEAN (ZR-5 side B — see §5) |
| 3 | `composition/asgi.py` | CLEAN |
| 4 | `composition/config.py` | CLEAN |
| 5 | `composition/dynamo.py` | CLEAN (constructs the ONE boto3 DynamoDB resource; adapters receive it, never build their own — see §5's correction) |
| 6 | `composition/orchestrate.py` | CLEAN (pure wiring, with one narrowing — see §5) |
| 7 | `composition/publish_helper.py` | CLEAN (the shared `build_publisher` both roots use) |
| 8 | `composition/pull_loop.py` | CLEAN |
| 9 | `composition/run.py` | CLEAN (ZR-5 side A — see §5) |
| 10 | `composition/sample_mode.py` | CLEAN (see §4 CLEARED — temporary, documented, out-of-core by design) |
| 11 | `composition/seed_dynamo.py` | **ZR-8** (duplicates a DynamoDB key schema two persistence adapters own) — MAJOR, see §4 |
| 12 | `composition/settings.py` | CLEAN (the ZR-3 compliant declaration source — see §3) |
| 13 | `composition/vendor_health.py` | **ZR-8** (`GAP-2`: duplicates the DQL query builder without its validation) — MAJOR, see §4 |

13 files listed, 13 read in full, 2 `ZR-8` findings (both MAJOR). **F1 correction (STORY-196
quality-review fix round, 2026-07-31):** the original pass verdicted `seed_dynamo.py` `CLEAN` —
the biggest miss in this report, corrected below.

### `tools/` (17 files)

| # | File | Verdict |
|---|------|---------|
| 1 | `tools/demo_engine/__init__.py` | CLEAN |
| 2 | `tools/demo_engine/assumed_failure_codes.py` | CLEAN (ZR-3's own compliant reference) |
| 3 | `tools/demo_engine/query_grammar.py` | CLEAN |
| 4 | `tools/demo_engine/rows.py` | CLEAN (see §4 CLEARED — `"0"`/`"HEALTHY"` vs `health_mapping.py`'s inline OR-rule literals) |
| 5 | `tools/demo_engine/scenario.py` | CLEAN |
| 6 | `tools/demo_engine/server.py` | CLEAN |
| 7 | `tools/demo_engine/store.py` | **ZR-3** (`VENDOR_HEALTH_WINDOW`) — MINOR |
| 8 | `tools/demo_loop_gate/__init__.py` | CLEAN |
| 9 | `tools/demo_loop_gate/env_matrix.py` | **ZR-3** ×8 (3 MAJOR, 5 MINOR — widened from ×3 this fix round, F4) |
| 10 | `tools/demo_loop_gate/evidence.py` | CLEAN |
| 11 | `tools/demo_loop_gate/publisher_chain.py` | CLEAN |
| 12 | `tools/demo_loop_gate/backfill_reality_gate.py` | CLEAN |
| 13 | `tools/demo_loop_gate/failure_path_reality_gate.py` | **ZR-3** (`_REGION`) — MINOR |
| 14 | `tools/demo_loop_gate/fleet_coverage.py` | CLEAN |
| 15 | `tools/demo_loop_gate/guard_reality_gate.py` | CLEAN |
| 16 | `tools/demo_loop_gate/harness.py` | **ZR-3** (the AC3 reference/demonstration case) — MINOR |
| 17 | `tools/import_provenance.py` | CLEAN |

17 files listed, 17 read in full, **11** `ZR-3` findings across 4 files (**3 MAJOR, 8 MINOR** —
widened this fix round from 6/2/4 by F4's five additional `env_matrix.py` findings), 13 files
with no finding.

## 2. `ZR-1..ZR-8` findings against `api/` and `composition/` (AC2)

**Zero** `ZR-n` violations were found in `api/`. This is not a bulk assertion: `api/`'s zero rests on
the per-file-type evidence in §1 (every `service.py`/`validation.py` read in full and judged
translation-only; every import edge grepped and confirmed to stay inside {own feature, `core`,
`_shared`, `api/dependencies.py`}).

**`composition/` carries TWO `ZR-8` findings (both `MAJOR`), corrected in this fix round — see §4.**
The original pass's "zero" here was wrong: it rested on a full read of all 13 files against the ZR-5
parity question and the three harder questions the brief poses, but the harder-questions answer
itself contained a false generalisation (`orchestrate.py`, `pull_loop.py`, `seed_dynamo.py`,
`dynamo.py` called "pure wiring... every branch routes to a named core service/query/domain type",
which is untrue of `seed_dynamo.py` — routes to `boto3`'s Table API — and of `dynamo.py` — routes to
`boto3.resource`) that hid `seed_dynamo.py`'s real finding. Corrected explicitly in §5.

## 3. `ZR-3` findings — the duplicated-declaration sweep (AC3)

### 3a. The sweep itself: command, scope, and output

Scope, exactly as pinned by `zone-rules.md` `ZR-3` (STORY-194 acceptance correction, 2026-07-31):
`backend/src/` side counts TWO declaration shapes — (i) a module-level UPPER_CASE constant anywhere
under `backend/src/`, and (ii) a settings/config field default, scoped here to
`backend/src/composition/settings.py` and `backend/src/composition/config.py` (the two files
literally named settings/config, matching `ZR-3`'s own illustrative citation
`backend/src/composition/settings.py:21-22`). `tools/` side counts every literal (str/int/float/bool)
ANYWHERE, including inside function bodies. A small, explicitly-stated noise set
(`{0, 1, -1, True, False, None, "", "utf-8"}`) is excluded from the report — these are exactly the
kind of value the `ZR-3` measurement note already names as unusably noisy at the wide reading; every
other collision is reported and adjudicated by hand.

**Stated blind-spot class (F5, STORY-196 quality-review fix round, 2026-07-31).** The `backend/src/`
side collects only `ast.Constant`-valued declarations. Verified this fix round: **20 module-level
UPPER_CASE constants exist under `backend/src/`; only 8 are `ast.Constant`-valued (visible to this
sweep); the other 12 are `dict`/`tuple`/function-call-valued and invisible to it** — including
`PROVISIONAL_STATUS_MAPPING` (`backend/src/adapters/inbound/dynatrace/health_mapping.py:35`), which is `ZR-3`'s OWN compliant reference
example, plus `_DQL_BREAKING_CHARS` (`backend/src/adapters/inbound/dynatrace/query.py:38`), `_STATUS_MAP` (`backend/src/adapters/outbound/statuspage/status_mapping.py:5`),
`STATUS_SEVERITY` (`backend/src/core/domain/status.py:63`), `DEFAULT_OVERLAP` (`backend/src/adapters/inbound/dynatrace/adapter.py:23`), `FUTURE_TOLERANCE`
(`backend/src/core/services/ingest_service.py:37`), `_SECTION_10_DEFAULTS` (`backend/src/composition/config.py:31`), `_NORMALIZERS` (`backend/src/adapters/inbound/dynatrace/dispatch.py:45`),
`_OUTCOME_TO_HEALTH` (`backend/src/adapters/inbound/dynatrace/health_mapping.py:27`), `_STATUS_BY_EXCEPTION` (`backend/src/api/v1/_shared/errors.py:24`), `_NOTHING`
and `_INTERNAL_WARNING` (`backend/src/core/services/pipeline.py:190-191`). Unpacking every nested literal inside these 12 to
compare them would reintroduce ZR-3's own rejected "wide reading" (101 mostly-noise collisions) —
so this is a genuine, accepted scope limit, not an oversight to silently fix. **Verified no live
violation hides in it**, by targeted reasoning rather than an exhaustive nested sweep: `tools/`'s own
compliant reference (`assumed_failure_codes.py`) already imports `PROVISIONAL_STATUS_MAPPING` rather
than redeclaring it; the remaining 11 are either error-message dicts, HTTP-status maps, or
timing/threshold values with no semantic counterpart anywhere under `tools/`. A future reader of a
`0` collision count against one of these 12 should read it as "not this sweep's job," never as
"checked and clean."

**Shape-(ii) narrowing, corrected (F5).** The original claim — "there are exactly 5 class-field
`Constant` defaults tree-wide and all 5 are in `settings.py`/`config.py`" — does not fully hold.
Re-measured this fix round: **6** class-level `Constant`-valued field defaults exist tree-wide under
`backend/src/`; 5 are in `settings.py`/`config.py` (correctly captured by this sweep's shape-(ii)
scope) and the 6th, `backend/src/core/domain/verdict.py:43`
(`under_maintenance: bool = False`, on `Verdict`), sits entirely OUTSIDE `composition/` — a CORE DOMAIN
TYPE's own field default, not a settings/config value, so it is correctly out of `ZR-3`'s
shape-(ii) scope BY DEFINITION (the rule targets settings/config specifically), not a miscount.
Also: `False` is itself in this sweep's noise-exclusion set, so even had it been collected it could
never have produced a spurious collision report.

Script: `tools/zr3_duplicate_sweep.py` (committed this fix round — F5; previously scratchpad-only,
so the recorded command below did not run at HEAD, a C2 gap on this story's central mechanical
artifact). **Committing it under `tools/` makes the sweep self-referential**: it now also finds
coincidental numeral collisions inside its own and `tools/citation_sweep.py`'s source (tuple-index
literals like `d[3]`/`h[2]`, `argv`-count comparisons, an exit code) — adjudicated in §3c along with
every other coincidental hit, not silently dropped. Command and full output, run at this fix round's
final HEAD:

```
$ python tools/zr3_duplicate_sweep.py .
backend/src/ declarations collected: 13 (8 shape-i, 5 shape-ii)
tools/ literal occurrences collected: 1024

Colliding pairs (backend/src declared value == tools/ literal), noise excluded: 21

  value=2 (int)  SRC: backend/src/composition/config.py:278 [shape-ii FreshnessConfig.reentry_cycles]  TOOLS: tools/citation_sweep.py:125
  value=2 (int)  SRC: backend/src/composition/config.py:278 [shape-ii FreshnessConfig.reentry_cycles]  TOOLS: tools/citation_sweep.py:127
  value=2 (int)  SRC: backend/src/composition/config.py:278 [shape-ii FreshnessConfig.reentry_cycles]  TOOLS: tools/citation_sweep.py:129
  value=2 (int)  SRC: backend/src/composition/config.py:278 [shape-ii FreshnessConfig.reentry_cycles]  TOOLS: tools/demo_engine/server.py:244
  value=2 (int)  SRC: backend/src/composition/config.py:278 [shape-ii FreshnessConfig.reentry_cycles]  TOOLS: tools/demo_engine/store.py:22
  value=2 (int)  SRC: backend/src/composition/config.py:278 [shape-ii FreshnessConfig.reentry_cycles]  TOOLS: tools/demo_loop_gate/backfill_reality_gate.py:30
  value='us-east-1' (str)  SRC: backend/src/composition/settings.py:20 [shape-ii Settings.aws_region]  TOOLS: tools/demo_loop_gate/env_matrix.py:39
  value='STATUSPAGE_PAGE_ID' (str)  SRC: backend/src/composition/settings.py:49 [shape-i STATUSPAGE_PAGE_ID_VAR]  TOOLS: tools/demo_loop_gate/env_matrix.py:75
  value='STATUSPAGE_API_KEY' (str)  SRC: backend/src/composition/settings.py:50 [shape-i STATUSPAGE_API_KEY_VAR]  TOOLS: tools/demo_loop_gate/env_matrix.py:77
  value=2 (int)  SRC: backend/src/composition/config.py:278 [shape-ii FreshnessConfig.reentry_cycles]  TOOLS: tools/demo_loop_gate/failure_path_reality_gate.py:65
  value='us-east-1' (str)  SRC: backend/src/composition/settings.py:20 [shape-ii Settings.aws_region]  TOOLS: tools/demo_loop_gate/failure_path_reality_gate.py:149
  value=3 (int)  SRC: backend/src/composition/config.py:275 [shape-ii FreshnessConfig.stale_after_cycles]  TOOLS: tools/demo_loop_gate/failure_path_reality_gate.py:390
  value=2 (int)  SRC: backend/src/composition/config.py:278 [shape-ii FreshnessConfig.reentry_cycles]  TOOLS: tools/demo_loop_gate/guard_reality_gate.py:23
  value=2 (int)  SRC: backend/src/composition/config.py:278 [shape-ii FreshnessConfig.reentry_cycles]  TOOLS: tools/demo_loop_gate/harness.py:49
  value='uptime-observations' (str)  SRC: backend/src/composition/settings.py:21 [shape-ii Settings.dynamo_observations_table]  TOOLS: tools/demo_loop_gate/harness.py:747
  value='uptime-control' (str)  SRC: backend/src/composition/settings.py:22 [shape-ii Settings.dynamo_control_table]  TOOLS: tools/demo_loop_gate/harness.py:750
  value=3 (int)  SRC: backend/src/composition/config.py:275 [shape-ii FreshnessConfig.stale_after_cycles]  TOOLS: tools/demo_loop_gate/harness.py:903
  value=2 (int)  SRC: backend/src/composition/config.py:278 [shape-ii FreshnessConfig.reentry_cycles]  TOOLS: tools/demo_loop_gate/harness.py:964
  value=3 (int)  SRC: backend/src/composition/config.py:275 [shape-ii FreshnessConfig.stale_after_cycles]  TOOLS: tools/zr3_duplicate_sweep.py:160
  value=3 (int)  SRC: backend/src/composition/config.py:275 [shape-ii FreshnessConfig.stale_after_cycles]  TOOLS: tools/zr3_duplicate_sweep.py:161
  value=2 (int)  SRC: backend/src/composition/config.py:278 [shape-ii FreshnessConfig.reentry_cycles]  TOOLS: tools/zr3_duplicate_sweep.py:182
```

### 3b. Proof the sweep is capable of finding something (AC3's gate)

**The sweep's own output contains the AC3 reference case, unprompted**:
`value='uptime-observations' ... SRC: backend/src/composition/settings.py:21 ... TOOLS:
tools/demo_loop_gate/harness.py:747` and the matching `'uptime-control'` /
`backend/src/composition/settings.py:22` / `tools/demo_loop_gate/harness.py:750` pair — exactly the
`ZR-3`-adjudicated violation the wiki names as the demonstration requirement, found by this sweep
with no special-casing. The sweep is shown capable of finding a real duplicate before any other
result is trusted, per AC3.

### 3c. Adjudication — every colliding pair, `MUST-IMPORT-FROM-SRC` or `INDEPENDENT`, with a reason

**`CLEARED` (coincidental — `INDEPENDENT`, not duplicates of the cited `backend/src/` declaration at
all):**

- `tools/demo_engine/server.py:244` — `self._httpd.server_address[:2]` (a slice index, unrelated to
  `FreshnessConfig.reentry_cycles`). **INDEPENDENT.**
- `tools/demo_loop_gate/backfill_reality_gate.py:30`,
  `tools/demo_loop_gate/failure_path_reality_gate.py:65`,
  `tools/demo_loop_gate/guard_reality_gate.py:23`,
  `tools/demo_loop_gate/harness.py:49` — all four are `Path(__file__).resolve().parents[2]` (a
  filesystem-ancestor index, three levels: `tools/demo_loop_gate/<file>.py` -> repo root).
  **INDEPENDENT** — coincidental int match, not a shared declared VALUE.
- `tools/demo_loop_gate/harness.py:903` — `dict(list(per_signal.items())[:3])` (a slice bound,
  unrelated to `FreshnessConfig.stale_after_cycles`). **INDEPENDENT.**
- `tools/demo_loop_gate/harness.py:964` — **corrected misread (F3, STORY-196 quality-review fix
  round, 2026-07-31): the original text said this line was `print("=" * 78)` with the matched `2`
  "elsewhere in the same file" — WRONG, found without opening the cited line. The real line 964 is
  `print(json.dumps(evidence, indent=2, default=str))`; the matched literal is the `indent=2` keyword
  argument, unrelated to `FreshnessConfig.reentry_cycles`.** **INDEPENDENT** (verdict unchanged, only
  the reason was wrong).
- `tools/demo_loop_gate/failure_path_reality_gate.py:390` — `("poison took good rows", {**good,
  "poison_signal_locations": 3})`, a self-test fixture value, unrelated to
  `FreshnessConfig.stale_after_cycles`. **INDEPENDENT.**
- **`tools/demo_engine/store.py:22`'s COINCIDENTAL numeral hit — added in this fix round (F3): the
  original ledger never adjudicated this collision line at all**, though it appears in §3a's raw
  sweep output. The matched literal is the bare `2` inside `timedelta(hours=2)` (the `hours=`
  keyword argument's value), which happens to equal `FreshnessConfig.reentry_cycles` by pure
  coincidence — this is DISTINCT from the semantic finding below about the WHOLE `VENDOR_HEALTH_WINDOW`
  value; the nested integer literal itself carries no relationship to `FreshnessConfig`.
  **INDEPENDENT** (this specific `Constant` node only — the finding on the value it is part of is
  adjudicated separately, below).
- **Six new self-referential hits, from committing the sweep scripts under `tools/` this fix round
  (F5) — `tools/citation_sweep.py:125` (`if len(sys.argv) < 2:`), `:127` (`return 2`), `:129`
  (`Path(sys.argv[2])`/`len(sys.argv) > 2`), `tools/zr3_duplicate_sweep.py:160` and `:161` (`d[3]`,
  a tuple-index literal used twice while formatting the shape-i/shape-ii counts), `:182` (`h[2]`, a
  tuple-index literal while building the dedup key).** All six are argv-length comparisons, an exit
  code, or tuple-index literals inside the sweep's OWN code — coincidental, not shared declared
  values. **INDEPENDENT**, all six.

None of the fifteen coincidental hits above (nine from the original run, one of which — `tools/demo_loop_gate/harness.py:964`
— carried a misread reason now corrected; plus six new self-referential ones from committing the
sweep scripts) shares any semantic relationship with `FreshnessConfig`; the sweep correctly reports
them as candidates (that is its job — prove absence of a PATTERN, never absence of a problem, per
the brief) and adjudication rules them out by reading the surrounding code, exactly as required —
every citation above was opened and read directly for this fix round, not inferred from the sweep's
own summary line. **Ledger balance, corrected (F3): 21 total collisions = 6 `MUST-IMPORT-FROM-SRC`
(below) + 15 `INDEPENDENT`/coincidental (above) — the original ledger listed only 8 coincidental
lines against 15 collisions (6+8=14, one short: `tools/demo_engine/store.py:22`'s own numeral hit was never
adjudicated), corrected here.**

**`MUST-IMPORT-FROM-SRC` — genuine findings, filed (see §6):**

- **`tools/demo_loop_gate/harness.py:747`** (`"uptime-observations"`) and **`:750`**
  (`"uptime-control"`) vs **`backend/src/composition/settings.py:21`**
  (`dynamo_observations_table: str = "uptime-observations"`) and **`:22`**
  (`dynamo_control_table: str = "uptime-control"`) — the AC3
  reference case, already adjudicated by `zone-rules.md` `ZR-3`. Read in context
  (`_assert_ac1_preconditions`): the two literals are a defensive BLOCKLIST
  (`assert result["observations_table"] not in ("uptime-observations", ...)`), not the harness's
  primary table-naming mechanism (`fresh_table_names()` already generates a random per-run suffix,
  so the two never collide with the default names in practice). Still a genuine `ZR-3` violation —
  if `Settings`'s defaults were ever renamed, this blocklist would silently stop recognizing them —
  but its severity is bounded by being defence-in-depth on top of an unrelated primary guard.
  **MINOR.**
- **`tools/demo_loop_gate/env_matrix.py:39`** (`aws_region: str = "us-east-1"`, a `build_child_env`
  parameter default) vs **`backend/src/composition/settings.py:20`**
  (`aws_region: str = "us-east-1"`). A rename of the real default would silently leave this harness targeting the OLD
  region while `Settings` itself moved on — low-churn value, contained blast radius (dev/demo
  harness only). **MINOR.**
- **`tools/demo_loop_gate/failure_path_reality_gate.py:149`** (`_REGION = "us-east-1"`, used
  directly in `_dynamo()`'s `boto3.resource(region_name=_REGION)`) vs the same
  `backend/src/composition/settings.py:20`. Same reasoning as above, a second independent
  hardcode of the identical value in a DIFFERENT tools/ file. **MINOR.**
- **`tools/demo_loop_gate/env_matrix.py:75`** (`env["STATUSPAGE_PAGE_ID"] = statuspage_page_id`)
  vs **`backend/src/composition/settings.py:49`** (`STATUSPAGE_PAGE_ID_VAR = "STATUSPAGE_PAGE_ID"`).
  This is not a low-stakes default — it is the ENV VAR KEY NAME `load_statuspage_secrets()`
  (`backend/src/composition/settings.py:79-90`) reads to find the fake Statuspage page id this
  harness deliberately injects (`FAKE_STATUSPAGE_PAGE_ID`, `tools/demo_loop_gate/harness.py:73`) into the credentialed
  API subprocess. If `STATUSPAGE_PAGE_ID_VAR`'s value were ever renamed in `settings.py`, this
  harness would keep setting the OLD env var name; the child process's own `load_statuspage_secrets`
  would then read nothing under the new name AND `composition/asgi.py`'s `load_dotenv()` (per
  CLAUDE.md's demo-engine section, `override=False`) would fill the gap from the REAL repo-root
  `.env` — silently defeating the exact fake-credential injection this harness's own docstring
  calls "defence in depth" for the real guard. **MAJOR** — directly threatens the credential-safety
  narrative this harness and CLAUDE.md's demo-engine section both document as load-bearing.
- **`tools/demo_loop_gate/env_matrix.py:77`** (`env["STATUSPAGE_API_KEY"] = statuspage_api_token`)
  vs **`backend/src/composition/settings.py:50`** (`STATUSPAGE_API_KEY_VAR = "STATUSPAGE_API_KEY"`).
  Identical mechanism and identical risk to the entry immediately above, on the paired credential.
  **MAJOR.**

**Five more `MUST-IMPORT-FROM-SRC` findings, added this fix round (F4) — the same rename-drift
mechanism as the credential pair above, sitting FIVE LINES ABOVE it in the SAME function, but never
listed in the original pass.** `build_child_env`'s five unconditional env-dict assignments
(`tools/demo_loop_gate/env_matrix.py:64-68`) hardcode five more env-var KEY NAMES that
`backend/src/composition/settings.py::load_settings` (lines 32-38) also reads, by literal string, to
resolve the SAME settings both composition roots depend on:

- **`tools/demo_loop_gate/env_matrix.py:64`** (`env["CONFIG_DIR"] = config_dir`) vs
  **`backend/src/composition/settings.py:32`** (`os.environ.get("CONFIG_DIR", "config/apps")`).
  **`MAJOR`** — the MOST severe of the seven, not merely equal to the credential pair:
  `CONFIG_DIR` is THE publish guard this whole harness's safety story depends on (§3c's own
  "defence in depth" language above is built ON TOP of `config/demo`'s empty
  `statuspage_mapping()`, which `CONFIG_DIR` is what SELECTS). A silent rename-drift here would not
  merely weaken a defence-in-depth layer, the way the credential pair does — it would point the
  harness at `config/apps` (the default), which DOES declare a real `statuspage_component_id`
  (`config/apps/httpcheck.yaml:8`, per CLAUDE.md), reactivating the real publish path this entire
  guard exists to keep closed.
- **`tools/demo_loop_gate/env_matrix.py:65`** (`env["AWS_REGION"] = aws_region`) vs
  **`backend/src/composition/settings.py:33`** (`os.environ.get("AWS_REGION", "us-east-1")`).
  **MINOR** — same low-churn, contained-blast-radius reasoning as the `aws_region` VALUE finding
  above; this is the KEY NAME sibling of that finding.
- **`tools/demo_loop_gate/env_matrix.py:66`** (`env["DYNAMO_ENDPOINT_URL"] = dynamo_endpoint_url`)
  vs **`backend/src/composition/settings.py:38`**
  (`os.environ.get("DYNAMO_ENDPOINT_URL") or None`). **MINOR** — a drift here would point the
  harness's DynamoDB client at nothing (falling through to a real AWS endpoint via boto3's default
  resolution), which would fail loudly (no such throwaway table exists there) rather than silently
  misbehave — bounded risk.
- **`tools/demo_loop_gate/env_matrix.py:67`** (`env["DYNAMO_OBSERVATIONS_TABLE"] = observations_table`)
  vs **`backend/src/composition/settings.py:34-36`**
  (`"DYNAMO_OBSERVATIONS_TABLE", "uptime-observations"`). **MINOR** — parallels the
  already-filed table-NAME-value finding above; this is the KEY NAME sibling.
- **`tools/demo_loop_gate/env_matrix.py:68`** (`env["DYNAMO_CONTROL_TABLE"] = control_table`) vs
  **`backend/src/composition/settings.py:37`**
  (`os.environ.get("DYNAMO_CONTROL_TABLE", "uptime-control")`). **MINOR** — same reasoning as the
  entry immediately above.

**Why the sweep could not see any of these five (F4).** `ZR-3`'s pinned scope collects the
`backend/src/` side only as (i) module-level UPPER_CASE constants or (ii) `settings.py`/`config.py`
class-field defaults. All five of `load_settings`'s `os.environ.get(...)` calls are FUNCTION-BODY
string literals — neither shape — so the `backend/src/` side of each of these five pairs is
invisible to `tools/zr3_duplicate_sweep.py` by construction, exactly like the already-adjudicated
`"0"`/`"HEALTHY"` (§3d) and `"test"` (§3d) cases. This is a FORMATTING ACCIDENT on the `src` side
(`STATUSPAGE_PAGE_ID_VAR`/`STATUSPAGE_API_KEY_VAR` happen to be pulled out as named module
constants two lines below these five calls; the other five env-var names were not), not a
difference in the underlying rename-drift RISK, which is identical across all seven — so all seven
belong in the same finding family (see §6, `STORY-202` widened to cover all seven).

**A genuine finding the sweep, by its own literal-equality design, CANNOT catch — found by manual
reading of `tools/demo_engine/store.py` and `backend/src/composition/vendor_health.py` (§1's evidence
basis for `tools/`), stated here rather than silently added to the sweep's own count:**

- **`tools/demo_engine/store.py:22`** (`VENDOR_HEALTH_WINDOW = timedelta(hours=2)`) vs
  **`backend/src/composition/vendor_health.py:37`** (`_HEALTH_CHECK_WINDOW = "2h"`). Both are
  module-level UPPER_CASE declarations (shape (i) on the `backend/src/` side; the sweep's own
  `collect_src_declarations` run confirms `_HEALTH_CHECK_WINDOW` was collected, value `'2h'` — see
  the full declaration list below), but the sweep's literal-equality comparison cannot match a
  `str` `'2h'` against a `timedelta(hours=2)` `Call` node — a `Call` is not an `ast.Constant`, so
  it is invisible to `_literal_value`. `tools/demo_engine/store.py:20-21`'s own docstring argues this is
  "part of the WIRE CONTRACT this engine answers, not an implementation detail borrowed from
  composition" — that argument does not hold under inspection: `query_grammar.py`'s parser (the
  module `store.py` itself imports at line 16) does NOT extract the window duration from the query
  string at all (`_SUMMARIZE_COUNT_RE`/`_MONITOR_ID_RE` match only the `summarize count()` shape and
  the monitor id filter, never a `from:now()-2h` duration), so `_answer_vendor_health`
  (`tools/demo_engine/store.py:73-83`) is not actually reading the wire's stated window — it is independently
  RE-ASSERTING what it assumes that window to be. If `_HEALTH_CHECK_WINDOW` ever changed in
  `composition/vendor_health.py` (e.g. to `"1h"`), the real query sent would ask for a 1h window
  but this demo engine would keep answering as if it were still 2h — silently including rows the
  real endpoint's actual window would have excluded, values currently agree (both mean "2 hours"),
  so nothing is broken TODAY, but the declared independence is not actually independent of the
  value it mirrors. **MINOR, `MUST-IMPORT-FROM-SRC`** (or, short of an import across the one-way
  boundary changing the TYPE contract, a comment making the coupling explicit and a regression test
  pinning it — a fix-story decision, not this audit's to make).

Full `backend/src/` declaration list the sweep collected (13 entries, for completeness — every value
above traces to one of these rows):

```
('clickpath', 'backend/src/adapters/inbound/dynatrace/clickpath_normalizer.py', 17, 'shape-i', 'NATIVE_KIND')
('http', 'backend/src/adapters/inbound/dynatrace/http_normalizer.py', 17, 'shape-i', 'NATIVE_KIND')
(24, 'backend/src/api/v1/_shared/windowing.py', 10, 'shape-i', 'DEFAULT_WINDOW_HOURS')
(3, 'backend/src/composition/config.py', 275, 'shape-ii', 'FreshnessConfig.stale_after_cycles')
(2, 'backend/src/composition/config.py', 278, 'shape-ii', 'FreshnessConfig.reentry_cycles')
('sample-mode:forced-down', 'backend/src/composition/sample_mode.py', 30, 'shape-i', 'SIMULATED_RAW_REF')
('STATUSPAGE_PAGE_ID', 'backend/src/composition/settings.py', 49, 'shape-i', 'STATUSPAGE_PAGE_ID_VAR')
('STATUSPAGE_API_KEY', 'backend/src/composition/settings.py', 50, 'shape-i', 'STATUSPAGE_API_KEY_VAR')
('us-east-1', 'backend/src/composition/settings.py', 20, 'shape-ii', 'Settings.aws_region')
('uptime-observations', 'backend/src/composition/settings.py', 21, 'shape-ii', 'Settings.dynamo_observations_table')
('uptime-control', 'backend/src/composition/settings.py', 22, 'shape-ii', 'Settings.dynamo_control_table')
('2h', 'backend/src/composition/vendor_health.py', 37, 'shape-i', '_HEALTH_CHECK_WINDOW')
('observed_at is implausibly in the future', 'backend/src/core/services/ingest_service.py', 40, 'shape-i', 'FUTURE_TIMESTAMP_REASON')
```

None of `NATIVE_KIND` (×2), `DEFAULT_WINDOW_HOURS`, `SIMULATED_RAW_REF`, or
`FUTURE_TIMESTAMP_REASON` collides with any `tools/` literal — **`CLEARED`, `INDEPENDENT`** (no
`tools/` occurrence of `'clickpath'`, `'http'` as a standalone constant, `24`, the sample-mode marker
string, or the future-timestamp reason string).

### 3d. `CLEARED` items discovered outside the mechanical sweep (adjudicated INDEPENDENT and OUT OF
SCOPE, not merely unflagged)

- **`tools/demo_engine/rows.py:33-34`** (`STATUS_CODE_HEALTHY = "0"`, `STATUS_MESSAGE_HEALTHY =
  "HEALTHY"`) vs **`backend/src/adapters/inbound/dynatrace/health_mapping.py:73`**
  (`if code == "0" or message == "HEALTHY":`). Considered as a candidate duplicate — both name the
  same two literal healthy-status values. **CLEARED, `INDEPENDENT` under `ZR-3`'s PINNED scope**:
  the `backend/src/` side is a literal inside `map_synthetic_status`'s `if` condition — neither a
  module-level UPPER_CASE constant (shape i) nor a settings/config field default (shape ii) — so it
  is not a "declared value" `ZR-3` covers at all (this is the exact "wide reading finds 101,
  narrow reading finds 0" gap `ZR-3`'s own measurement note already names). Independently, the
  duplication is also semantically SAFER than it looks: `tools/demo_engine/rows.py:26-32`'s own comment already
  states the healthy check is an OR-rule (either half alone maps to `Health.UP`), so this pair
  being out of sync with the OTHER half would not silently break anything the way `ZR-3`'s core
  concern (a hardcoded value that must track a SOLE source of truth) does.
- **`tools/demo_loop_gate/failure_path_reality_gate.py:148`**
  (`_DUMMY_LOCAL_CREDENTIAL = "test"`) vs **`backend/src/composition/dynamo.py:23-24`**
  (`resource_kwargs["aws_access_key_id"] = "test"` / `resource_kwargs["aws_secret_access_key"] =
  "test"`). **CLEARED, `INDEPENDENT` under `ZR-3`'s pinned scope**: the `backend/src/` side is a
  literal inside `make_dynamo_resource`'s function body — neither shape (i) nor shape (ii) — so it
  is out of scope for the same reason as the entry above, and the file's own docstring
  (`tools/demo_loop_gate/failure_path_reality_gate.py:138-147`) already names and explains this exact value
  independently ("MUST match `make_dynamo_resource`... exactly"), so the coupling is at least
  documented even though it is not import-enforced.

### 3e. The private-module import, and the one-way direction itself (F2)

**`tools/demo_engine/query_grammar.py:26` and `tools/demo_engine/store.py:14` both import a
PRIVATE, underscore-prefixed adapter-internal module — never adjudicated in the original pass.**
Both do `from src.adapters.inbound.dynatrace._assembly import parse_ns_timestamp`. This is
DIRECTION-legal (`tools/` importing `src.*`, never the reverse — see the direction check below),
but importing an underscore-prefixed module crosses a convention Python does not enforce: `_assembly`
names itself as an ADAPTER-INTERNAL module, not a published API `tools/` is meant to depend on.
Adjudicated separately per file, since only one documents the choice:

- **`tools/demo_engine/query_grammar.py:54-66`** (`parse_watermark_bound`) documents the reuse
  explicitly and correctly: "Reuses the REAL production timestamp parser
  (`_assembly.py::parse_ns_timestamp`) rather than reimplementing it, so the watermark bound and
  every row's own `timestamp` are parsed by the exact same logic... (a 6-digit bound sorts
  lexicographically BEFORE a 9-digit row at the same instant, which is the STORY-051 stall
  reproduced inside this engine if this parsing is skipped)." **`CLEARED`** — this is the exact
  reuse-not-reimplement discipline `ZR-3`/`ZR-8` both argue FOR, just crossing a private-module
  boundary rather than a zone boundary; the reasoning for doing so is stated, not silent.
- **`tools/demo_engine/store.py:14`** imports the SAME function for the SAME reason (sorting/filtering
  rows by parsed timestamp in `_answer_ingest`/`_answer_vendor_health`) but its module docstring
  (`tools/demo_engine/store.py:1-7`) does not say so — no reuse rationale is recorded at this second import site.
  **`CLEARED`**, same reasoning as `query_grammar.py` (the import itself is sound and direction-legal),
  but flagged as a documentation gap: a future reader of `store.py` alone would not know this import
  is deliberate reuse rather than an accidental reach into adapter internals. Not filed as its own
  story (too small to be worth one), noted as a candidate for `store.py`'s next touch.
- **The real consequence, beyond encapsulation (F2), stated explicitly rather than left implicit:**
  because BOTH import sites use the SAME production timestamp parser the real ingest path uses, **a
  defect in `parse_ns_timestamp` itself is structurally invisible to the demo engine** — the demo
  engine would parse a malformed or edge-case timestamp exactly as wrongly (or exactly as correctly)
  as production does, so this stand-in can never catch a `parse_ns_timestamp` bug the real ingest
  path also has. This is the fidelity trade-off CLAUDE.md's demo-engine section already accepts
  implicitly (the demo engine exists to test the REST of the pipeline against Grail-shaped rows, not
  to independently verify the timestamp parser) — worth stating plainly rather than leaving as an
  unstated assumption.

**The directional half of the "one-way boundary" this report is titled for — verified, not merely
implied.** Command and full output, re-run at this fix round's HEAD:

```
$ grep -rn "^from tools\|^import tools\|from tools\.\|import tools\." backend/src --include="*.py"
$ echo "exit=$?"
exit=1
$ grep -rln "^from demo_engine\|^import demo_engine\|^from demo_loop_gate\|^import demo_loop_gate" backend/src --include="*.py"
$ echo "exit=$?"
exit=1
```

Both greps return NO matches (exit 1, ripgrep/grep convention for "no lines matched") — nothing
under `backend/src/` imports `tools/`, `demo_engine`, or `demo_loop_gate`, by either the qualified
(`tools.demo_engine...`) or the `sys.path`-relative (`demo_engine...`) import spelling both actually
appear in this codebase (`tools/demo_engine/scenario.py` and siblings import `demo_engine.*`
relative to a `sys.path` insertion, never `tools.demo_engine.*` — both spellings checked). This is,
as the reviewer notes, the cheapest and most mechanically-guardable rule in the whole catalogue: a
single `lint-imports`-style `forbidden_modules` contract could enforce it directly were `tools/`
ever brought inside `root_package` — recorded here as re-derivable evidence for `STORY-197`, which
otherwise gets none from this report.

## 4. `ZR-8` findings — storage and vendor mechanics duplicated outside their owning adapter (both `MAJOR`)

**Landed this fix round (STORY-196 quality-review round, 2026-07-31) as `ZR-8` in
`docs/scrum/wiki/zone-rules.md`** — GAP-2 (finding 2 below) was originally reported unscored,
deliberately not catalogued while `zone-rules.md` was under a concurrent quality-review re-read;
that reason has now expired (the coordinator: "the file is now free"), and a second, independently
more severe instance (finding 1) surfaced in this same fix round, so both are landed together as one
rule rather than two separate ad hoc observations. Full rule text, Statement/Source/Coverage
verdict: `docs/scrum/wiki/zone-rules.md` `ZR-8`.

### Finding 1 — `composition/seed_dynamo.py` duplicates a DynamoDB key schema TWO persistence adapters already own (the biggest miss in the original pass)

`backend/src/composition/seed_dynamo.py:29-30` (`"pk": "TOPOLOGY",` / `"sk": f"APP#{app.id}",`), `:43`
(`{"pk": "TOPOLOGY", "sk": f"COMPONENT#{comp.id}"}`), and `:58-59`
(`{"pk": "TOPOLOGY", "sk": f"SIGNAL#{sig.signal_key}"}`) hand-build the SAME key schema
`DynamoComponentRepository` (`backend/src/adapters/persistence/dynamo_component_repository.py:39-40,53-54`)
and `DynamoSignalRepository` (`backend/src/adapters/persistence/dynamo_signal_repository.py:41-42`)
already own and implement — RAW `boto3` persistence (`table.put_item`, `table.update_item`, a
hand-written `UpdateExpression` with `if_not_exists`) issued directly from the composition zone, on
the boot path of BOTH composition roots (`composition/run.py::main`'s topology seed call,
`composition/app.py::create_app`'s lifespan seed call).

**Severity: `MAJOR`, and it is not a theoretical risk — it already drifted once.**
`tools/demo_loop_gate/failure_path_reality_gate.py:163-172`'s own docstring records the SAME class
of drift already happening, in a DIFFERENT hand-rolled key site inside this repo: a first version of
that file used `pk=COMPONENT#<id>, sk=META` where the repository's real schema is
`pk=TOPOLOGY, sk=COMPONENT#<id>` — the write created a phantom item nothing reads, the read-back
"verified" it against the SAME wrong key, and this cost two full debugging runs before the mismatch
was found. `docs/scrum/wiki/persistence-adapters.md:36` already documents `seed_topology_dynamo`
alongside the two adapters it duplicates, in its own Facts section — the wiki article had already,
independently, treated this as adapter-adjacent; the zone-rule catalogue and this audit had not
caught up until this fix round.

**Why the original pass missed it.** §5 (original text) generalised `orchestrate.py`, `pull_loop.py`,
`seed_dynamo.py`, and `dynamo.py` together as "pure wiring — every branch routes to a named core
service/query/domain type and returns its result unchanged." That is FALSE for `seed_dynamo.py`
(routes to `boto3`'s Table API, not a core type) and FALSE for `dynamo.py` (routes to
`boto3.resource`) — the exact bulk-`CLEAN`-overstatement class this report's own §1 criticises
STORY-195 for, now found inside itself. Corrected in §5.

**This fell through the crack between STORY-195 (`adapters/`) and STORY-196 (`composition/`)
auditing disjoint file sets — precisely the failure a two-pass audit exists to prevent, stated
plainly rather than minimised.** `seed_dynamo.py` is a `composition/` file by directory, so it was
this story's job, not STORY-195's — the miss is this report's own, not a gap in scope assignment.

**Why the eight `lint-imports` contracts pass it.** `composition` calling `boto3` directly is
something `adapters-independence` never restricts for the `composition` zone — the contracts check
import edges, never whether a reachable capability (here, raw table access) was reused via the
adapter that already encodes it, rather than re-derived.

### Finding 2 — `composition/vendor_health.py::build_vendor_health_query` duplicates a DQL query builder without its validation (`GAP-2`, first reported in this report's original pass)

`backend/src/composition/vendor_health.py:40-53` re-implements a DQL-query-building responsibility
`adapters/inbound/dynatrace/query.py::build_dql_query`
(`backend/src/adapters/inbound/dynatrace/query.py:52-102`) already owns, WITHOUT reusing that
function's `InvalidNativeIdError` breaking-character validation (STORY-021,
`backend/src/adapters/inbound/dynatrace/query.py:41-49,79-82`). Both functions interpolate the SAME
trusted `native_id` config value into a DQL string literal; only `build_dql_query` checks it for
characters (`"`, `\`, newline, carriage return) that would break out of the `"{native_id}"` literal.
A `native_id` containing such a character would be rejected loudly, with a named error, the moment
`build_dql_query` runs (inside the ingest path) — but `check_vendor_id_health`
(`backend/src/composition/vendor_health.py:96-133`) runs FIRST, at loop startup, and would instead
silently build a malformed query, send it, and (at best) log a generic "Vendor-id health probe
FAILED" WARNING from the resulting Grail-side syntax error, rather than the loud, specific,
`InvalidNativeIdError`-named failure the ingest path would raise moments later for the identical
root cause. **Severity: `MAJOR`** (a real correctness/observability gap in shipping code, not a
stylistic one — matching Finding 1's severity, per the coordinator's ruling that both belong under
one rule).

**Why the eight `lint-imports` contracts pass both findings.** `composition` legally
importing/reaching `adapters` — or, in `seed_dynamo.py`'s case, calling `boto3` directly — is
EXACTLY the wiring permission the eight contracts grant the composition zone by design. The
contracts check import edges, not whether a REACHABLE capability was actually reused rather than
re-derived; a module that hand-builds the same key/query a sibling module already encodes imports
nothing NEW to trip a contract.

Full detail, the rule's Coverage verdict (`GUARDABLE` only as a reviewed pattern, with its stated
false-positive risk), and the compliant counter-pattern: `docs/scrum/wiki/zone-rules.md` `ZR-8`.
Filed as `STORY-205` (§6).

## 5. `composition` parity report (AC5)

**Do the two composition roots agree on every setting where disagreement changes behaviour,
`CONFIG_DIR` included?** Yes, re-derived independently this story (not merely re-cited from
`zone-rules.md`'s existing `ZR-5` Fact):

- **`backend/src/composition/run.py:182`** (`settings = load_settings()`) and
  **`backend/src/composition/run.py:184`** (`config = load_config(settings.config_dir)`) —
  `build_live_loop`'s caller resolves `config_dir` EXCLUSIVELY through `Settings.config_dir`, which
  `load_settings` (`backend/src/composition/settings.py:26-39`) reads from
  `os.environ.get("CONFIG_DIR", "config/apps")`. `run.py` never reads `os.environ["CONFIG_DIR"]`
  directly.
- **`backend/src/composition/app.py:97`** (`settings = load_settings()`) and
  **`backend/src/composition/app.py:137`** (`cfg_dir = config_dir or settings.config_dir`) —
  `create_app` routes through the SAME `load_settings().config_dir`, with an optional explicit
  `config_dir=` constructor parameter (used only by tests) taking priority when supplied, never a
  second env-var read. `app.py` also never reads `os.environ["CONFIG_DIR"]` directly.
- **The shared publisher chain.** `backend/src/composition/run.py:121-128` and
  `backend/src/composition/app.py:176-183` both call the SAME
  `composition/publish_helper.py::build_publisher` (`backend/src/composition/publish_helper.py:183-234`)
  with the same **six** keyword arguments (`component_repo`, `publication_repo`, `clock`,
  `statuspage_page_id`, `statuspage_api_token`, `component_mapping` — corrected from "five", F5),
  sourced from `config.statuspage_mapping()` and either
  `LiveSecrets` (`run.py`) or `StatuspageSecrets` (`app.py`, via `load_statuspage_secrets()`) — the
  two secrets types are deliberately DIFFERENT (`StatuspageSecrets` is documented,
  `backend/src/composition/settings.py:63-73`, as "the Statuspage-only half of `LiveSecrets`" so
  `app.py` never has to call `load_live_secrets` and trip its `MissingLiveSecretError` for the
  irrelevant Dynatrace vars), but both resolve to the identical `page_id`/`api_token` env vars
  (`STATUSPAGE_PAGE_ID_VAR`/`STATUSPAGE_API_KEY_VAR`, `backend/src/composition/settings.py:49-50`) —
  no second naming convention.

**No code-level divergence found.** Confirms `zone-rules.md` `ZR-5`'s existing Fact independently,
by re-reading both files this story rather than re-citing it and stopping.

**The three harder questions the brief poses, answered explicitly (not merely re-derived):**

- **Does anything in `composition/` make a decision that belongs in a core service? (F1 correction —
  the original answer here was FALSE for two of the four files it named.)** The original text
  claimed `orchestrate.py`, `pull_loop.py`, `seed_dynamo.py`, `dynamo.py` are "pure wiring — every
  branch routes to a named core service/query/domain type and returns its result unchanged." That is
  untrue of TWO of the four: `seed_dynamo.py` routes to `boto3`'s Table API, not a core type — and,
  worse, hand-builds a key schema two persistence adapters already own (`ZR-8` finding 1, §4,
  `MAJOR`) — and `dynamo.py` routes to `boto3.resource`, also not a core type (though `dynamo.py`
  itself is NOT a finding: it is the sole place that CONSTRUCTS the DynamoDB resource, which every
  `adapters/persistence/*` module then RECEIVES as a constructor argument rather than building its
  own — legitimate composition-root infrastructure wiring, not a duplicate of anything). Precisely
  per-file, corrected: `pull_loop.py` IS pure wiring (every branch calls `adapters`/`core` functions
  and returns their result). `orchestrate.py` is ALMOST pure wiring but not entirely —
  `backend/src/composition/orchestrate.py:95-98` (`since = until - (max_threshold + 2) * interval`) computes an observation
  window using its OWN `+2` cycles of slack, a small arithmetic rule that does not itself route
  anywhere; it is documented inline (dossier §8 "overlap for edge cadence") and is not scored as a
  finding, but it is not "routes to a named type and returns unchanged" either — excluded from that
  generalisation rather than silently folded into it. `seed_dynamo.py`'s real finding is `ZR-8`
  (§4), not this bullet — but the FALSE per-file claim that hid it is corrected here.
  Separately, `sample_mode.py::SampleModeIngest.ingest_observations`
  (`backend/src/composition/sample_mode.py:53-72`) DOES force every observation's `health` to
  `Health.DOWN` while the flag is on — a real domain-shaped decision (what health value an
  observation carries) sitting in `composition/`, not `core/services/`. This is CLEARED, not a
  finding: the module's own docstring states the reason explicitly and correctly — "It never
  touches `core/services/`: the override wraps the real `IngestService`, so the core stays pure
  (hexagonal constraint, STORY-048 Context)" — this is a first-class, reviewed, TEMPORARY design
  decision (PO directive 2026-07-03, tracked for removal at STORY-155, CLAUDE.md's own "superseded"
  section names it as inert since the Dynatrace trial expired), not an accidental core-logic leak.
- **Is any wiring duplicated between the two roots such that they could drift?** No beyond what §5's
  citations already show is IDENTICAL (both call the same `load_settings`/`load_config`/
  `build_publisher` functions). Two genuine duplications this audit found in `composition/` —
  `vendor_health.py` re-implementing a fragment of `adapters/inbound/dynatrace/query.py`'s
  query-building, and `seed_dynamo.py` re-implementing two persistence adapters' key schema — are
  BOTH `composition`<->`adapters` duplications, not `run.py`<->`app.py` ones, so they are reported
  separately as `ZR-8` findings (§4), not as `ZR-5` findings.
- **Does either root read configuration through a path the other does not?** No — both resolve
  `config_dir`, `dynamo_observations_table`/`dynamo_control_table`, and the Statuspage credential
  pair through the identical `Settings`/`StatuspageSecrets` dataclasses, as cited above.

## 6. Filed stories (AC2 — MAJORs as their own stories; MINORs batched)

**`STORY-202`, `STORY-203`, and `STORY-204` (this report's original pass) are already LANDED in
`.scrum/backlog.yaml` by the orchestrator** — that file is not edited by this report. `STORY-202`'s
DESCRIPTION below is the WIDENED scope this fix round found (F4); the landed backlog entry may still
read the original 2-MAJOR version until the orchestrator reconciles it — noted here rather than
silently assumed updated. New proposed story from this fix round: `STORY-205` (F1), ids from
`STORY-205` onward per instruction (198-204 already landed).

### STORY-202 — `env_matrix.py` must import SEVEN env-var key names from `settings.py`, not re-declare them (widened this fix round, F4)

- **Type:** defect (`ZR-3`, `MAJOR` ×3 + `MINOR` ×4 — a credential-safety-relevant and
  publish-guard-relevant duplicated declaration, widened from the original 2 MAJORs).
- **Estimate:** 2 (fibonacci, widened from 1) — a seven-line import-and-use change in one file
  (`build_child_env`), all in the same function, same fix shape.
- **Offending citations, all in `tools/demo_loop_gate/env_matrix.py`'s `build_child_env`
  (`:63-77`), vs their `backend/src/composition/settings.py` counterparts:**
  - `:64` (`env["CONFIG_DIR"]`) vs `backend/src/composition/settings.py:32` — **MAJOR**, added this
    fix round: `CONFIG_DIR` is THE publish guard (`config/demo`'s empty `statuspage_mapping()` is
    what `build_publisher` checks; `CONFIG_DIR` is what selects `config/demo` vs `config/apps`).
  - `:75` (`env["STATUSPAGE_PAGE_ID"]`) vs `backend/src/composition/settings.py:49`
    (`STATUSPAGE_PAGE_ID_VAR`) — **MAJOR** (original pass).
  - `:77` (`env["STATUSPAGE_API_KEY"]`) vs `backend/src/composition/settings.py:50`
    (`STATUSPAGE_API_KEY_VAR`) — **MAJOR** (original pass).
  - `:65` (`env["AWS_REGION"]`) vs `backend/src/composition/settings.py:33` — MINOR, added this fix
    round.
  - `:66` (`env["DYNAMO_ENDPOINT_URL"]`) vs `backend/src/composition/settings.py:38` — MINOR, added
    this fix round.
  - `:67` (`env["DYNAMO_OBSERVATIONS_TABLE"]`) vs `backend/src/composition/settings.py:34-36` —
    MINOR, added this fix round.
  - `:68` (`env["DYNAMO_CONTROL_TABLE"]`) vs `backend/src/composition/settings.py:37` — MINOR, added
    this fix round.
- **Context:** see §3c. A rename of `STATUSPAGE_PAGE_ID_VAR`/`STATUSPAGE_API_KEY_VAR` in
  `settings.py` would silently defeat this harness's fake-credential injection into the credentialed
  API subprocess, letting `composition/asgi.py`'s `load_dotenv()` fill the gap with REAL repo-root
  `.env` Statuspage credentials instead. A rename of the `"CONFIG_DIR"` string in `settings.py`
  would silently point the harness at `config/apps` (the real fleet, which DOES declare a real
  `statuspage_component_id`) instead of `config/demo` — the single most severe of the seven, since
  it is the guard itself, not defence-in-depth on top of it. All seven escape the sweep for the SAME
  reason: `load_settings`'s `os.environ.get(...)` calls are function-body literals on the
  `backend/src/` side, invisible to `ZR-3`'s pinned shape-(i)/(ii) scope — a formatting accident, not
  a difference in risk (see §3c).
- **Acceptance criteria (testable):**
  - AC1: `tools/demo_loop_gate/env_matrix.py` imports `STATUSPAGE_PAGE_ID_VAR` and
    `STATUSPAGE_API_KEY_VAR` from `src.composition.settings` and uses them as `env[...]` dict keys
    in `build_child_env`, in place of the two literal strings.
  - AC2: The same file gains (or `settings.py` exports) named constants for `CONFIG_DIR`,
    `AWS_REGION`, `DYNAMO_ENDPOINT_URL`, `DYNAMO_OBSERVATIONS_TABLE`, `DYNAMO_CONTROL_TABLE`, used
    identically on both sides — refinement decides whether `settings.py` grows five more
    module-level `_VAR` constants (matching the two that already exist) or `load_settings` is
    refactored to build its `os.environ.get(...)` calls from a single shared name list either side
    can import.
  - AC3: A test asserts `build_child_env(...)`'s returned dict has keys equal to the imported
    symbols for all seven env vars — pinned via the imports, not re-typed literals, so a future
    rename of any one constant moves this test's own expectation with it.
  - AC4: Existing `demo_loop_gate` tests exercising `build_child_env` continue to pass unchanged.

### STORY-203 — batch the 4 MINOR `ZR-3` findings: `tools/` should import shared literals from `backend/src/`, not re-declare them

- **Type:** chore (`ZR-3`, `MINOR` ×4, batched per AC2).
- **Estimate:** 2 (fibonacci) — four small, independent import-and-use changes across three files.
- **Offending citations:**
  - `tools/demo_loop_gate/harness.py:747,750` (`"uptime-observations"`/`"uptime-control"`) vs
    `backend/src/composition/settings.py:21-22` — the AC3 reference case.
  - `tools/demo_loop_gate/env_matrix.py:39` (`aws_region: str = "us-east-1"` default) vs
    `backend/src/composition/settings.py:20`.
  - `tools/demo_loop_gate/failure_path_reality_gate.py:149` (`_REGION = "us-east-1"`) vs the same
    `backend/src/composition/settings.py:20`.
  - `tools/demo_engine/store.py:22` (`VENDOR_HEALTH_WINDOW = timedelta(hours=2)`) vs
    `backend/src/composition/vendor_health.py:37` (`_HEALTH_CHECK_WINDOW = "2h"`) — the
    cross-representation case; the fix here is either importing and converting
    `_HEALTH_CHECK_WINDOW` at import time, or (refinement's call) parsing it out of the actual query
    string via `query_grammar.py` instead of asserting it as a second constant at all.
- **Context:** see §3c/§3d. None of the four is a live defect today (all values currently agree);
  each is a drift risk the next person to touch the `backend/src/` side would have no way to know
  about from `tools/`'s own code.
- **Acceptance criteria (testable):**
  - AC1: `harness.py`'s two blocklist literals are replaced with
    `Settings.dynamo_observations_table`/`Settings.dynamo_control_table`'s DEFAULT values, read via
    a `Settings()` construction or the imported field defaults — not re-typed strings.
  - AC2: `env_matrix.py`'s `aws_region` default and `failure_path_reality_gate.py`'s `_REGION` both
    import `Settings.aws_region`'s default rather than hardcoding `"us-east-1"` a second and third
    time.
  - AC3: `store.py`'s `VENDOR_HEALTH_WINDOW` is derived from `_HEALTH_CHECK_WINDOW`
    (`backend/src/composition/vendor_health.py`) at import time (parsed once, e.g. via a small
    `"Nh"` -> `timedelta` helper), rather than declared as an independent literal — refinement
    decides whether that helper lives in `vendor_health.py` (importable) or `tools/demo_engine/`.
  - AC4: Existing tests for all three touched `tools/` files continue to pass unchanged.

### STORY-204 — reuse the adapter's DQL query builder + validation inside `composition/vendor_health.py` (already landed; now `ZR-8` finding 2, not a catalogue gap)

- **Type:** defect (**F1 correction: no longer "catalogue gap, not a `ZR-n`"** — `ZR-8` landed this
  fix round covers it directly, see §4 Finding 2).
- **Estimate:** 2 (fibonacci) — unchanged.
- **Offending citation:** `backend/src/composition/vendor_health.py:40-53`
  (`build_vendor_health_query`), which does not call or reuse
  `backend/src/adapters/inbound/dynatrace/query.py:41-49,79-82`'s `InvalidNativeIdError` validation.
- **Context:** see §4 Finding 2 and `zone-rules.md` `ZR-8`. Refinement should decide the shape (a
  small shared validator both builders call, vs. `vendor_health.py` composing its query around a
  shared "quote and validate" helper `query.py` exports) rather than this audit prescribing the fix.
- **Acceptance criteria (testable):**
  - AC1: A `native_id` containing a DQL-breaking character (`"`, `\`, newline, carriage return)
    raises the SAME named error (`InvalidNativeIdError` or an equivalent re-exported from `query.py`)
    from `build_vendor_health_query` that `build_dql_query` already raises, rather than silently
    building a malformed query.
  - AC2: A test constructs `build_vendor_health_query` with a breaking-character `native_id` and
    asserts the named error, mirroring `query.py`'s own existing `InvalidNativeIdError` test.
  - AC3: Existing `test_vendor_health.py` tests continue to pass unchanged for well-formed ids.

### STORY-205 — `composition/seed_dynamo.py` must call the two persistence adapters' key schema, not re-implement it (`ZR-8` finding 1, `MAJOR`)

- **Type:** defect (`ZR-8`, `MAJOR` — a persistence key schema declared a third time, on the boot
  path of both composition roots, which has already drifted once elsewhere in this repo).
- **Estimate:** 3 (fibonacci) — touches three seed operations (apps, components, signals) plus a
  regression test proving the schema now comes from the adapters, not re-typed here.
- **Offending citations:** `backend/src/composition/seed_dynamo.py:29-30` (app key),
  `:43` (component key, via `table.update_item`), `:58-59` (signal key, via `table.put_item`) — vs
  `backend/src/adapters/persistence/dynamo_component_repository.py:39-40,53-54` and
  `backend/src/adapters/persistence/dynamo_signal_repository.py:41-42`.
- **Context:** see §4 Finding 1 and `zone-rules.md` `ZR-8`. `DynamoComponentRepository`/
  `DynamoSignalRepository` do not currently expose an upsert/write method shaped for bulk topology
  seeding (their `set_status`/`get` are single-item, request-scoped operations) — refinement must
  decide whether to add a seed-shaped method to each repository (preferred, keeps the schema in
  ONE place) or export the key-building helper alone for `seed_dynamo.py` to call (a smaller change,
  but leaves the WRITE call itself duplicated). No repository currently owns `AppConfig`-shaped
  writes (the `pk=TOPOLOGY, sk=APP#<id>` items) at all — this may need a THIRD adapter method or a
  small new `TopologyRepository` port, which refinement should size before estimating further.
- **Acceptance criteria (testable):**
  - AC1: `seed_topology_dynamo` no longer constructs `{"pk": ..., "sk": ...}` dicts itself for
    components or signals — it calls a method on `DynamoComponentRepository`/`DynamoSignalRepository`
    (or an equivalent shared helper those adapters expose) that encodes the SAME schema.
  - AC2: A regression test changes the key schema INSIDE one of the two repositories (e.g. adds a
    version-suffix to `sk`) and asserts `seed_topology_dynamo` follows it automatically (writes
    readable by `list_components`/`get`) WITHOUT `seed_dynamo.py`'s own code changing — the exact
    drift class `tools/demo_loop_gate/failure_path_reality_gate.py:163-172` already hit once.
  - AC3: `tools/demo_loop_gate/failure_path_reality_gate.py`'s own hand-rolled-key incident (its
    docstring) is cited in the story as the motivating precedent, not re-litigated as a new defect.
  - AC4: Existing `test_dynamo_seed.py` (per `docs/scrum/wiki/persistence-adapters.md`'s History)
    continues to pass unchanged for the app-seed path, or is updated to match the new call shape if
    AC1 changes it.

## 7. `CLEARED` entries, summarized (AC6 — STORY-195 AC4's rule)

Every `CLEARED` entry above is recorded with its reason in place (§3c, §3d, §3e, §5) rather than
left silent. **Counts reconciled this fix round (F3): the original list here said "six" while
enumerating seven and omitting `tools/demo_loop_gate/harness.py:964` and
`tools/demo_engine/store.py:22` — corrected below against the
final, re-derivable ledger balance in §3c (21 total collisions = 6 `MUST-IMPORT-FROM-SRC` + 15
`INDEPENDENT`).** Summarized for the record:

1. NINE coincidental numeral/int `ZR-3` sweep hits from the ORIGINAL tree (`tools/demo_engine/server.py:244`;
   `parents[2]` in four files, one bullet; `tools/demo_loop_gate/harness.py:903`'s slice bound;
   `tools/demo_loop_gate/harness.py:964`'s `indent=2` keyword argument (misread as `"=" * 78` in the
   original pass — reason corrected, verdict unchanged); `tools/demo_loop_gate/
   failure_path_reality_gate.py:390`'s self-test fixture value; `tools/demo_engine/store.py:22`'s
   own `timedelta(hours=2)` numeral, previously unadjudicated) — coincidental int collisions with
   `FreshnessConfig.reentry_cycles`/`stale_after_cycles`, unrelated in meaning. `INDEPENDENT`.
2. SIX new coincidental numeral hits from committing the sweep scripts under `tools/` this fix round
   (F5) — `tools/citation_sweep.py:125,127,129` (argv-length comparisons, an exit code) and
   `tools/zr3_duplicate_sweep.py:160,161,182` (tuple-index literals) — same class as (1),
   self-referential rather than pre-existing. `INDEPENDENT`.
3. `tools/demo_engine/rows.py`'s `STATUS_CODE_HEALTHY`/`STATUS_MESSAGE_HEALTHY` vs
   `health_mapping.py`'s inline OR-rule literals. Out of `ZR-3`'s pinned scope (neither shape on the
   `backend/src/` side) AND semantically safer than a true duplicate (an OR-rule, not a sole source
   of truth). `INDEPENDENT`.
4. `tools/demo_loop_gate/failure_path_reality_gate.py`'s `_DUMMY_LOCAL_CREDENTIAL = "test"` vs
   `composition/dynamo.py`'s inline `"test"`/`"test"` literals. Out of `ZR-3`'s pinned scope
   (function-body literal on the `backend/src/` side, neither declared shape), and independently
   documented in the citing file's own docstring. `INDEPENDENT`.
5. `composition/sample_mode.py::SampleModeIngest` forcing `Health.DOWN` — a domain-shaped decision
   living in `composition/`, not `core/services/`. `CLEARED`: a first-class, documented, PO-approved
   TEMPORARY design (STORY-048), tracked for removal (STORY-155), inert since the trial expired.
6. `api/dependencies.py` as a THIRD shared location every `api/v1/*` feature reaches into, beyond
   the brief's literal "core and `api/v1/_shared`" — see §8. `CLEARED`: pure FastAPI DI accessor
   functions typed against `src.core.ports`, no business logic, no cross-feature reach.
7. `tools/demo_engine/query_grammar.py:26`/`tools/demo_engine/store.py:14`'s private `_assembly.parse_ns_timestamp`
   import — added this fix round (F2). `CLEARED` for both (direction-legal, reuse-not-reimplement);
   `store.py`'s own docstring does not state the reuse rationale `query_grammar.py`'s does, noted as
   a documentation-completeness candidate, not a finding.
8. `composition/dynamo.py`'s description as "pure wiring" — corrected, not cleared: it routes to
   `boto3.resource`, not a core type, but is NOT a finding (it is the sole constructor of the
   DynamoDB resource; every adapter RECEIVES it rather than building its own). See §5 (F1).

## 8. `api` feature-shape report (AC4)

**Five-file convention, per feature, by name:**

```
$ ls backend/src/api/v1/*/  (excluding __pycache__)
approvals:    __init__.py  controller.py  models.py  service.py  validation.py   (5)
availability: __init__.py  controller.py  models.py  service.py  validation.py   (5)
components:   __init__.py  controller.py  models.py  service.py  validation.py   (5)
decisions:    __init__.py  controller.py  models.py  service.py  validation.py   (5)
health:       __init__.py  controller.py                                        (2 -- documented exception)
history:      __init__.py  controller.py  models.py  service.py  validation.py   (5)
maintenance:  __init__.py  controller.py  models.py  service.py  validation.py   (5)
publications: __init__.py  controller.py  models.py  service.py  validation.py   (5)
sample_mode:  __init__.py  controller.py  models.py  service.py  validation.py   (5)
topology:     __init__.py  controller.py  models.py  service.py  validation.py   (5)
```

**Nine of ten features are exactly five files.** `health` is the ONE documented deviation
(`backend/src/api/v1/health/controller.py`'s own docstring: "a minimal liveness probe; it also
gives the `api-feature-independence` import-linter contract a second feature so the contract is
non-vacuous") — matching `zone-rules.md` `ZR-4`'s own count exactly, re-verified independently this
story rather than re-cited and stopped.

**Does any feature module reach outside its own directory other than to `core` and
`api/v1/_shared`?** Re-derivable command:

```
$ cd backend/src && grep -rn "^from src\.\|^import src\." api/ \
    | grep -v "from src.core" | grep -v "from src.api.v1._shared" | grep -v "from src.api.v1 import"
```

Every remaining line (full output in §1's evidence-basis discussion) resolves to one of: the
feature's OWN `models.py`/`service.py`/`validation.py`/`controller.py`, or
`src.api.dependencies` — **never** another feature, and never `src.adapters`/`src.composition`
directly. **Precision note, stated explicitly rather than folded silently into "core":**
`src.api.dependencies` (`backend/src/api/dependencies.py`) is a THIRD shared location, at the `api/`
package ROOT (not `api/v1/_shared`), that every one of the nine five-file features' `service.py`
imports from. Read in full (§1): it is nine one-line FastAPI dependency-provider functions, each
`return request.app.state.<x>`, typed exclusively against `src.core.ports` interfaces — no business
logic, no cross-feature reach, no adapter import. `CLEARED`, not a violation — but the brief's
literal two-name list ("core and `api/v1/_shared`") does not name this file, so it is called out
here rather than silently absorbed into "core."

**Zero `ZR-n` findings in `api/`.**

## 9. Citation-resolution sweep (AC re-derivation requirement)

Built fresh for this report (STORY-195's own `citation_sweep_story195_v2.py` was a scratchpad file,
never committed to the repo — confirmed by a repo-wide search finding no `*sweep*.py` under version
control). Same design STORY-195 describes: for every `` `path:line` `` citation immediately followed
by a parenthesized backtick excerpt, extract the excerpt and confirm it is a substring of the actual
file's cited line range (not merely that the file is long enough); citations with no such excerpt
fall back to a line-count-only check, reported as such rather than silently upgraded to false
confidence. Citations are EXTRACTED from this report's own Markdown text via regex, never a
hand-typed manifest (A9).

**Proof the check discriminates (shown failing before being trusted, mirroring STORY-195's own
proof), run against an isolated scratch file:** a deliberately wrong citation
(`backend/src/composition/vendor_health.py:36` claiming the anchor `_HEALTH_CHECK_WINDOW`, one line
before its real location) alongside the correct one on the following line:

```
FAIL backend/src/composition/vendor_health.py:36 (anchor '_HEALTH_CHECK_WINDOW' NOT found in lines 36-36)
OK   backend/src/composition/vendor_health.py:37 (file has 133 lines) [anchor matched: '_HEALTH_CHECK_WINDOW']

Extracted 2 citation occurrence(s), 2 distinct (path, line-spec) pair(s) checked -- 1 content-anchor-verified, 0 line-count-only (no anchor present), 1 failure(s).
```

The wrong citation fails, the right one passes — the check discriminates.

**Real run against this report, POST fix round** (`tools/citation_sweep.py`, committed this fix
round — F5):

Command: `python tools/citation_sweep.py docs/scrum/sprints/2026-07-31-sprint-66/audit-api-composition-tools.md .`

```
OK   tools/demo_engine/store.py:22 (file has 83 lines) [line-count only, no anchor]
OK   tools/demo_loop_gate/harness.py:964 (file has 971 lines) [line-count only, no anchor]
OK   backend/src/composition/orchestrate.py:95-98 (file has 159 lines) [line-count only, no anchor]
OK   backend/src/composition/settings.py:21-22 (file has 119 lines) [line-count only, no anchor]
OK   backend/src/adapters/inbound/dynatrace/health_mapping.py:35 (file has 88 lines) [line-count only, no anchor]
OK   backend/src/adapters/inbound/dynatrace/query.py:38 (file has 102 lines) [line-count only, no anchor]
OK   backend/src/adapters/outbound/statuspage/status_mapping.py:5 (file has 27 lines) [line-count only, no anchor]
OK   backend/src/core/domain/status.py:63 (file has 78 lines) [line-count only, no anchor]
OK   backend/src/adapters/inbound/dynatrace/adapter.py:23 (file has 43 lines) [line-count only, no anchor]
OK   backend/src/core/services/ingest_service.py:37 (file has 144 lines) [line-count only, no anchor]
OK   backend/src/composition/config.py:31 (file has 725 lines) [line-count only, no anchor]
OK   backend/src/adapters/inbound/dynatrace/dispatch.py:45 (file has 149 lines) [line-count only, no anchor]
OK   backend/src/adapters/inbound/dynatrace/health_mapping.py:27 (file has 88 lines) [line-count only, no anchor]
OK   backend/src/api/v1/_shared/errors.py:24 (file has 50 lines) [line-count only, no anchor]
OK   backend/src/core/services/pipeline.py:190-191 (file has 239 lines) [line-count only, no anchor]
OK   backend/src/core/domain/verdict.py:43 (file has 75 lines) [anchor matched: 'under_maintenance: bool = False']
OK   backend/src/composition/settings.py:22 (file has 119 lines) [line-count only, no anchor]
OK   tools/demo_loop_gate/harness.py:750 (file has 971 lines) [line-count only, no anchor]
OK   tools/demo_engine/server.py:244 (file has 254 lines) [line-count only, no anchor]
OK   tools/demo_loop_gate/backfill_reality_gate.py:30 (file has 114 lines) [line-count only, no anchor]
OK   tools/demo_loop_gate/failure_path_reality_gate.py:65 (file has 556 lines) [line-count only, no anchor]
OK   tools/demo_loop_gate/guard_reality_gate.py:23 (file has 132 lines) [line-count only, no anchor]
OK   tools/demo_loop_gate/harness.py:49 (file has 971 lines) [line-count only, no anchor]
OK   tools/demo_loop_gate/harness.py:903 (file has 971 lines) [line-count only, no anchor]
OK   tools/demo_loop_gate/failure_path_reality_gate.py:390 (file has 556 lines) [line-count only, no anchor]
OK   tools/citation_sweep.py:125 (file has 135 lines) [anchor matched: 'if len(sys.argv) < 2:']
OK   tools/zr3_duplicate_sweep.py:160 (file has 203 lines) [line-count only, no anchor]
OK   tools/demo_loop_gate/harness.py:747 (file has 971 lines) [anchor matched: '"uptime-observations"']
OK   backend/src/composition/settings.py:21 (file has 119 lines) [anchor matched: 'dynamo_observations_table: str = "uptime-observations"']
OK   tools/demo_loop_gate/env_matrix.py:39 (file has 79 lines) [anchor matched: 'aws_region: str = "us-east-1"']
OK   backend/src/composition/settings.py:20 (file has 119 lines) [anchor matched: 'aws_region: str = "us-east-1"']
OK   tools/demo_loop_gate/failure_path_reality_gate.py:149 (file has 556 lines) [anchor matched: '_REGION = "us-east-1"']
OK   tools/demo_loop_gate/env_matrix.py:75 (file has 79 lines) [anchor matched: 'env["STATUSPAGE_PAGE_ID"] = statuspage_page_id']
OK   backend/src/composition/settings.py:49 (file has 119 lines) [anchor matched: 'STATUSPAGE_PAGE_ID_VAR = "STATUSPAGE_PAGE_ID"']
OK   backend/src/composition/settings.py:79-90 (file has 119 lines) [line-count only, no anchor]
OK   tools/demo_loop_gate/harness.py:73 (file has 971 lines) [line-count only, no anchor]
OK   tools/demo_loop_gate/env_matrix.py:77 (file has 79 lines) [anchor matched: 'env["STATUSPAGE_API_KEY"] = statuspage_api_token']
OK   backend/src/composition/settings.py:50 (file has 119 lines) [anchor matched: 'STATUSPAGE_API_KEY_VAR = "STATUSPAGE_API_KEY"']
OK   tools/demo_loop_gate/env_matrix.py:64-68 (file has 79 lines) [line-count only, no anchor]
OK   tools/demo_loop_gate/env_matrix.py:64 (file has 79 lines) [anchor matched: 'env["CONFIG_DIR"] = config_dir']
OK   backend/src/composition/settings.py:32 (file has 119 lines) [anchor matched: 'os.environ.get("CONFIG_DIR", "config/apps")']
OK   config/apps/httpcheck.yaml:8 (file has 11 lines) [line-count only, no anchor]
OK   tools/demo_loop_gate/env_matrix.py:65 (file has 79 lines) [anchor matched: 'env["AWS_REGION"] = aws_region']
OK   backend/src/composition/settings.py:33 (file has 119 lines) [anchor matched: 'os.environ.get("AWS_REGION", "us-east-1")']
OK   tools/demo_loop_gate/env_matrix.py:66 (file has 79 lines) [anchor matched: 'env["DYNAMO_ENDPOINT_URL"] = dynamo_endpoint_url']
OK   backend/src/composition/settings.py:38 (file has 119 lines) [anchor matched: 'os.environ.get("DYNAMO_ENDPOINT_URL") or None']
OK   tools/demo_loop_gate/env_matrix.py:67 (file has 79 lines) [anchor matched: 'env["DYNAMO_OBSERVATIONS_TABLE"] = observations_table']
OK   backend/src/composition/settings.py:34-36 (file has 119 lines) [anchor matched: '"DYNAMO_OBSERVATIONS_TABLE", "uptime-observations"']
OK   tools/demo_loop_gate/env_matrix.py:68 (file has 79 lines) [anchor matched: 'env["DYNAMO_CONTROL_TABLE"] = control_table']
OK   backend/src/composition/settings.py:37 (file has 119 lines) [anchor matched: 'os.environ.get("DYNAMO_CONTROL_TABLE", "uptime-control")']
OK   backend/src/composition/vendor_health.py:37 (file has 133 lines) [anchor matched: '_HEALTH_CHECK_WINDOW = "2h"']
OK   tools/demo_engine/store.py:20-21 (file has 83 lines) [line-count only, no anchor]
OK   tools/demo_engine/store.py:73-83 (file has 83 lines) [line-count only, no anchor]
OK   tools/demo_engine/rows.py:33-34 (file has 93 lines) [anchor matched: 'STATUS_CODE_HEALTHY = "0"']
OK   backend/src/adapters/inbound/dynatrace/health_mapping.py:73 (file has 88 lines) [anchor matched: 'if code == "0" or message == "HEALTHY":']
OK   tools/demo_engine/rows.py:26-32 (file has 93 lines) [line-count only, no anchor]
OK   tools/demo_loop_gate/failure_path_reality_gate.py:148 (file has 556 lines) [anchor matched: '_DUMMY_LOCAL_CREDENTIAL = "test"']
OK   backend/src/composition/dynamo.py:23-24 (file has 26 lines) [anchor matched: 'resource_kwargs["aws_access_key_id"] = "test"']
OK   tools/demo_loop_gate/failure_path_reality_gate.py:138-147 (file has 556 lines) [line-count only, no anchor]
OK   tools/demo_engine/query_grammar.py:26 (file has 100 lines) [line-count only, no anchor]
OK   tools/demo_engine/store.py:14 (file has 83 lines) [line-count only, no anchor]
OK   tools/demo_engine/query_grammar.py:54-66 (file has 100 lines) [anchor matched: 'parse_watermark_bound']
OK   tools/demo_engine/store.py:1-7 (file has 83 lines) [line-count only, no anchor]
OK   backend/src/composition/seed_dynamo.py:29-30 (file has 69 lines) [anchor matched: '"pk": "TOPOLOGY",']
OK   backend/src/adapters/persistence/dynamo_signal_repository.py:41-42 (file has 48 lines) [line-count only, no anchor]
OK   tools/demo_loop_gate/failure_path_reality_gate.py:163-172 (file has 556 lines) [line-count only, no anchor]
OK   docs/scrum/wiki/persistence-adapters.md:36 (file has 55 lines) [line-count only, no anchor]
OK   backend/src/composition/vendor_health.py:40-53 (file has 133 lines) [line-count only, no anchor]
OK   backend/src/adapters/inbound/dynatrace/query.py:52-102 (file has 102 lines) [line-count only, no anchor]
OK   backend/src/composition/vendor_health.py:96-133 (file has 133 lines) [line-count only, no anchor]
OK   backend/src/composition/run.py:182 (file has 223 lines) [anchor matched: 'settings = load_settings()']
OK   backend/src/composition/run.py:184 (file has 223 lines) [anchor matched: 'config = load_config(settings.config_dir)']
OK   backend/src/composition/settings.py:26-39 (file has 119 lines) [line-count only, no anchor]
OK   backend/src/composition/app.py:97 (file has 228 lines) [anchor matched: 'settings = load_settings()']
OK   backend/src/composition/app.py:137 (file has 228 lines) [anchor matched: 'cfg_dir = config_dir or settings.config_dir']
OK   backend/src/composition/run.py:121-128 (file has 223 lines) [line-count only, no anchor]
OK   backend/src/composition/app.py:176-183 (file has 228 lines) [line-count only, no anchor]
OK   backend/src/composition/publish_helper.py:183-234 (file has 234 lines) [line-count only, no anchor]
OK   backend/src/composition/settings.py:63-73 (file has 119 lines) [line-count only, no anchor]
OK   backend/src/composition/settings.py:49-50 (file has 119 lines) [line-count only, no anchor]
OK   backend/src/composition/sample_mode.py:53-72 (file has 72 lines) [line-count only, no anchor]
OK   backend/src/composition/vendor_health.py:36 (file has 133 lines) [line-count only, no anchor]

Extracted 127 citation occurrence(s), 82 distinct (path, line-spec) pair(s) checked -- 32 content-anchor-verified, 50 line-count-only (no anchor present), 0 failure(s).
```

**Self-referential note, carried forward from the original pass and still true:** this report
cites its OWN sweep output inside a fenced code block; the embedded block above is the sweep's
final, stable re-run AFTER every citation this fix round introduced was fixed to a full
repo-relative path and every anchor mismatch was corrected against the real cited line (F3's
`tools/demo_loop_gate/harness.py:964` misread, and several new anchor mismatches this fix round's additions introduced,
were all found and fixed by running this exact sweep against the draft, iteratively, before this
final embed) — never silently re-adjusted to match a stale number.

**0 failures on the real, final run** — every one of this report's 82 distinct `path:line` citations
resolves, 32 of them content-anchor-verified (not merely line-count-checked, nearly double the
original pass's 19, since this fix round's additions (F1-F5) carry more single-line literal
excerpts). The 50 line-count-only entries are mostly multi-line ranges (e.g.
`backend/src/composition/settings.py:79-90`, `backend/src/composition/vendor_health.py:40-53`)
where the report's own prose does not carry a literal single-line excerpt to check against —
consistent with STORY-195's own experience that most citations in a report like this are ranges or
symbol references, not single-line literal quotes.

## 10. Gate — real output

`REQUIRE_DYNAMO=1 DYNAMO_ENDPOINT_URL=http://127.0.0.1:8021`, the five backend DoD commands via
`yt_gate.py --only` (confirmed with `--list` first that each selector matched exactly its intended
command and nothing else, per STORY-178):

```
$ python .claude/skills/yourteam/scripts/yt_gate.py --only "pytest" --only "lint_imports_command" --only "ruff check" --only "ruff format" --only "cfn-lint" --list
Tests pass: pytest
Import boundary holds: python -c "from importlinter.cli import lint_imports_command; lint_imports_command()"
Code linting check: ruff check .
Code formatting check: ruff format --check .
CloudFormation template lint: cfn-lint infra/stack.yaml

$ python .claude/skills/yourteam/scripts/yt_gate.py --only "pytest" --only "lint_imports_command" --only "ruff check" --only "ruff format" --only "cfn-lint"
[1/5] pytest -> PASS (685 passed, 0 skipped, in 59.61s)
[2/5] python -c "from importlinter.cli import lint_imports_command; lint_imports_command()" -> PASS
      (Analyzed 150 files, 429 dependencies. Contracts: 8 kept, 0 broken.)
[3/5] ruff check . -> PASS (All checks passed!)
[4/5] ruff format --check . -> PASS (242 files already formatted)
[5/5] cfn-lint infra/stack.yaml -> PASS
```

**5/5 PASS, 685 passed / 0 skipped** (matches the sprint's V7 baseline exactly — expected, since
this story's own diff touches no file under `backend/src/`).

## 11. Diff-scope proof (C1) — real output

**F5 correction: the original pass checked only the SPRINT-START base (`d4ad03e`); the coordinator
asks for the base this story's own commit range names.** Both stated, both empty — `tools/` is
correctly OUTSIDE C1's restriction (`backend/src/ frontend/ config/` only), so committing the two
sweep scripts under `tools/` this fix round does not touch it:

```
$ git diff --name-only d4ad03e..HEAD -- backend/src frontend config
$ echo "sprint-start-base exit=$?"
sprint-start-base exit=0
$ git diff --name-only d0019f8..HEAD -- backend/src frontend config
$ echo "commit-range-base exit=$?"
commit-range-base exit=0
```

Both empty (a `git diff --name-only` with no output and exit 0 means no files matched, per Git's own
convention — confirmed, not merely assumed). Every commit this story has made across BOTH its
original pass and this fix round (`cf6042f`, `5407a40`, `6ece7f8`, and this report's own upcoming
commit) touches only: this report, `docs/scrum/wiki/zone-rules.md`, `tools/zr3_duplicate_sweep.py`,
`tools/citation_sweep.py` — none under `backend/src/`, `frontend/`, or `config/`. C1 holds.

## 12. Wiki

**F1/general correction: `docs/scrum/wiki/zone-rules.md` IS edited by this story's fix round** — the
original pass's "NOT edited... concurrent-edit reason" no longer applies; the coordinator: "the file
is now free." `ZR-8` landed there (§4), with `code_refs` widened to include the four new citations
(`backend/src/composition/seed_dynamo.py`, `backend/src/composition/vendor_health.py`,
`backend/src/adapters/inbound/dynatrace/query.py`,
`tools/demo_loop_gate/failure_path_reality_gate.py`) and `verified_sha` re-stamped to `ca0cd37`
(this fix round's starting HEAD, after an actual re-read of every newly-cited file — not a
mechanical bump). `yt_wiki.py`'s default checks (`sweep facts links refs integrity`), re-run after
the `ZR-8` edit:

```
$ python .claude/skills/yourteam/scripts/yt_wiki.py
== sweep: CLEAN ==
== facts: CLEAN ==
== links: CLEAN ==
== refs: 2 note(s) ==
  amplifier: `backend/src/composition/run.py` is a code_ref in 5 articles ... narrow it to the article(s) actually ABOUT it
  amplifier: `pyproject.toml` is a code_ref in 5 articles ... narrow it to the article(s) actually ABOUT it
== integrity: CLEAN ==
```

Same two PRE-EXISTING advisory `refs` notes as the sprint-66 baseline (neither names a file this
story touched — `refs` is advisory only, never blocking, per V5); `sweep`/`facts`/`links`/`integrity`
all CLEAN. No other wiki article's `code_refs` overlap this story's diff (checked: `zone-rules.md`
is the only wiki file touched), so no further wiki blast radius applies.

## History

- 2026-07-31: STORY-196 findings report authored. 85/85 modules enumerated and accounted for
  (`api` 55, `composition` 13, `tools` 17). Zero `ZR-1..ZR-7` findings in `api`/`composition`. Six
  `ZR-3` findings in `tools/` (2 MAJOR, 4 MINOR), found via a purpose-built AST sweep shown capable
  of catching the AC3 reference case (`tools/demo_loop_gate/harness.py:747` and `:750` vs
  `backend/src/composition/settings.py:21-22`) before any
  `CLEARED` result was accepted, plus one cross-representation `ZR-3` finding the sweep's own
  literal-equality design cannot catch (found by direct reading, stated as such). One catalogue-gap
  observation (composition/adapters DQL-builder duplication) left unscored and uncatalogued,
  mirroring `GAP-1`'s own precedent, with a draft `ZR-8` proposed in prose only. Three stories filed
  (`STORY-202` MAJOR pair, `STORY-203` batched MINORs, `STORY-204` the catalogue gap). Five `CLEARED`
  entries recorded with reasons. `api`'s five-file convention re-verified independently (nine
  features + `health`'s documented exception), plus a precision note on `api/dependencies.py` as a
  third shared location the brief's two-name list did not anticipate. `composition`'s two roots
  re-verified to agree on every `CONFIG_DIR`-adjacent setting, independently of `zone-rules.md`'s
  existing `ZR-5` Fact.

- 2026-07-31 (quality-review fix round): spec PASS on all six AC (independently re-implemented the
  `ZR-3` sweep from this report's prose and got byte-identical output). Quality `FIX_REQUIRED`, 4
  MAJOR + 7 minor, from an independent re-audit of all 13 `composition/` modules,
  `api/dependencies.py`, the six `service.py` files, and the `tools/` boundary crossers. Corrected:
  (F1) `composition/seed_dynamo.py` — the biggest miss — verdicted `CLEAN` while it hand-builds a
  DynamoDB key schema two persistence adapters already own, raw `boto3` persistence on the boot path
  of both composition roots, which had already drifted once
  (`tools/demo_loop_gate/failure_path_reality_gate.py:163-172`) and which
  `docs/scrum/wiki/persistence-adapters.md` already treated as adapter-adjacent; the false "pure
  wiring" generalisation that hid it (also wrong for `dynamo.py`, loose for `backend/src/composition/orchestrate.py:95-98`)
  corrected in §5; landed as `ZR-8` finding 1 (`MAJOR`) in `zone-rules.md`, widening `GAP-2`
  (finding 2) into the same rule now that the concurrent-edit deferral has expired; filed
  `STORY-205`. (F2) the `_assembly.parse_ns_timestamp` private-module import
  (`query_grammar.py`/`store.py`) adjudicated explicitly (`CLEARED` for both, `store.py` flagged for
  a missing reuse-rationale docstring), and the one-way direction itself verified with a recorded
  command (new §3e) rather than left implied by the report's own title. (F3) §3c's ledger corrected
  to balance (21 collisions = 6 `MUST-IMPORT-FROM-SRC` + 15 `INDEPENDENT`, `tools/demo_engine/store.py:22`'s own
  numeral hit newly adjudicated) and `tools/demo_loop_gate/harness.py:964`'s misread reason fixed (real content is
  `indent=2`, not `"=" * 78`) — verdict unchanged, evidence corrected; §7's count reconciled.
  (F4) five more `env_matrix.py` env-var key-name literals (`CONFIG_DIR`, `AWS_REGION`,
  `DYNAMO_ENDPOINT_URL`, `DYNAMO_OBSERVATIONS_TABLE`, `DYNAMO_CONTROL_TABLE`) added to §3c —
  `CONFIG_DIR` graded `MAJOR` (the actual publish guard, more severe than the credential pair it sits
  five lines above), the other four MINOR; `STORY-202`'s description widened to all seven (the landed
  backlog entry itself is the orchestrator's to reconcile). (F5) the sweep's real blind-spot class
  stated honestly (12 of 20 module-level UPPER_CASE constants under `backend/src/` are
  non-`ast.Constant`-valued, including `ZR-3`'s own compliant reference
  `PROVISIONAL_STATUS_MAPPING`); the shape-(ii) tree-wide count corrected to 6 (not 5), with the 6th
  (`backend/src/core/domain/verdict.py:43`) confirmed out of scope by definition rather than miscounted; both
  sweep scripts (`tools/zr3_duplicate_sweep.py`, `tools/citation_sweep.py`) committed under `tools/`
  (making the sweep self-referential — six new coincidental hits inside its own source, adjudicated
  in §3c); §5's "five" keyword arguments to `build_publisher` corrected to six; §11's diff-scope
  proof stated against both the sprint-start base and this story's own commit-range base;
  `backend/src/composition/orchestrate.py:95-98` excluded from the "routes and returns unchanged" generalisation. Citation
  sweep re-run against the fully-edited, final report text (82 distinct pairs, 32
  content-anchor-verified, 0 failures) — every bare-filename citation this fix round's own new prose
  introduced was caught by the sweep itself and fixed before this final embed, the same
  self-inflicted-defect class STORY-195's fix round found in itself.
