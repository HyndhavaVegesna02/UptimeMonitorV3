# STORY-196 — Audit findings: `api` + `composition` + the `tools/` -> `backend/src/` one-way boundary

Point-in-time findings report. Sprint history, **not** the wiki — this describes the codebase at
`sprint-66` HEAD `10ee45aee4ceb44a11597a2ec6d481724f922ab7` (short `10ee45a`) and must never be
re-stamped later as if still current. Yardstick: `docs/scrum/wiki/zone-rules.md` (`ZR-1..ZR-7` as
landed by STORY-194/195) plus the eight `lint-imports` contracts it links to
(`docs/scrum/wiki/architecture-boundary.md`). Same report contract as
`docs/scrum/sprints/2026-07-31-sprint-66/audit-core-adapters.md` (STORY-195), reused per this
story's own instruction — this report does not edit that file or `zone-rules.md`'s `ZR-1..ZR-5` text
(a concurrent re-review of STORY-195 was in flight while this story ran).

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

Verdict legend: `CLEAN` — no finding. `ZR-n` — violates that catalogue rule (§2). `GAP-2` — an
unscored catalogue-gap observation (no `ZR-n` fits it), see §4.

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
| 5 | `composition/dynamo.py` | CLEAN |
| 6 | `composition/orchestrate.py` | CLEAN |
| 7 | `composition/publish_helper.py` | CLEAN (the shared `build_publisher` both roots use) |
| 8 | `composition/pull_loop.py` | CLEAN |
| 9 | `composition/run.py` | CLEAN (ZR-5 side A — see §5) |
| 10 | `composition/sample_mode.py` | CLEAN (see §4 CLEARED — temporary, documented, out-of-core by design) |
| 11 | `composition/seed_dynamo.py` | CLEAN |
| 12 | `composition/settings.py` | CLEAN (the ZR-3 compliant declaration source — see §3) |
| 13 | `composition/vendor_health.py` | CLEAN against `ZR-1..ZR-7`; `GAP-2` catalogue-gap observation, unscored — see §4 |

13 files listed, 13 read in full, 0 `ZR-n` findings; one unscored catalogue-gap observation.

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
| 9 | `tools/demo_loop_gate/env_matrix.py` | **ZR-3** ×3 (2 MAJOR, 1 MINOR) |
| 10 | `tools/demo_loop_gate/evidence.py` | CLEAN |
| 11 | `tools/demo_loop_gate/publisher_chain.py` | CLEAN |
| 12 | `tools/demo_loop_gate/backfill_reality_gate.py` | CLEAN |
| 13 | `tools/demo_loop_gate/failure_path_reality_gate.py` | **ZR-3** (`_REGION`) — MINOR |
| 14 | `tools/demo_loop_gate/fleet_coverage.py` | CLEAN |
| 15 | `tools/demo_loop_gate/guard_reality_gate.py` | CLEAN |
| 16 | `tools/demo_loop_gate/harness.py` | **ZR-3** (the AC3 reference/demonstration case) — MINOR |
| 17 | `tools/import_provenance.py` | CLEAN |

17 files listed, 17 read in full, 6 `ZR-3` findings across 4 files (2 MAJOR, 4 MINOR), 13 files
with no finding.

## 2. `ZR-1..ZR-7` findings against `api/` and `composition/` (AC2)

**Zero** violations of any `ZR-n` rule were found in `api/` or `composition/`. This is not a bulk
assertion: `api/`'s zero rests on the per-file-type evidence in §1 (every `service.py`/`validation.py`
read in full and judged translation-only; every import edge grepped and confirmed to stay inside
{own feature, `core`, `_shared`, `api/dependencies.py`}). `composition/`'s zero rests on a full read
of all 13 files against the specific ZR-5 parity question (§5) plus the three harder questions the
brief poses (decide-vs-wire, root-vs-root duplication, config-path divergence) — all three answered
"no" with citations in §5.

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

Script: `zr3_sweep.py` (repo-relative AST walk, no dependency beyond the stdlib; full text in this
story's session, reproducible from the description above). Command and full output:

```
$ python zr3_sweep.py .
backend/src/ declarations collected: 13 (8 shape-i, 5 shape-ii)
tools/ literal occurrences collected: 911

Colliding pairs (backend/src declared value == tools/ literal), noise excluded: 15

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
- `tools/demo_loop_gate/harness.py:964` — `print("=" * 78)` inside a different call than the
  `parents[2]` one above; the `2` the sweep actually matched here is elsewhere in the same file
  (already covered by the `tools/demo_loop_gate/harness.py:49` entry — the AST walk visits every
  `Constant`, so a file with more than one coincidental `2` can appear more than once; both resolve
  to the same `parents[2]` idiom). **INDEPENDENT.**
- `tools/demo_loop_gate/failure_path_reality_gate.py:390` — `("poison took good rows", {**good,
  "poison_signal_locations": 3})`, a self-test fixture value, unrelated to
  `FreshnessConfig.stale_after_cycles`. **INDEPENDENT.**

None of the six `2`/`3` coincidences shares any semantic relationship with `FreshnessConfig`; the
sweep correctly reports them as candidates (that is its job — prove absence of a PATTERN, never
absence of a problem, per the brief) and adjudication rules them out by reading the surrounding
code, exactly as required.

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

## 4. Catalogue-gap observation (unscored — `GAP-2`)

**`composition/vendor_health.py::build_vendor_health_query`
(`backend/src/composition/vendor_health.py:40-53`) re-implements a DQL-query-building
responsibility `adapters/inbound/dynatrace/query.py::build_dql_query`
(`backend/src/adapters/inbound/dynatrace/query.py:52-102`) already owns, WITHOUT reusing that
function's `InvalidNativeIdError` breaking-character validation (STORY-021,
`backend/src/adapters/inbound/dynatrace/query.py:41-49,79-82`).** Both functions interpolate the
SAME trusted `native_id` config value into a DQL string literal; only `build_dql_query` checks it
for characters (`"`, `\`, newline, carriage return) that would break out of the `"{native_id}"`
literal. A `native_id` containing such a character would be rejected loudly, with a named error,
the moment `build_dql_query` runs (inside the ingest path) — but `check_vendor_id_health`
(`backend/src/composition/vendor_health.py:96-133`) runs FIRST, at loop startup, and would instead silently
build a malformed query, send it, and (at best) log a generic "Vendor-id health probe FAILED"
WARNING from the resulting Grail-side syntax error, rather than the loud, specific,
`InvalidNativeIdError`-named failure the ingest path would raise moments later for the identical
root cause.

**No existing `ZR-n` fits this.** `ZR-1` is about an inbound ADAPTER holding a persistence port —
not applicable (this is composition duplicating an adapter's TRANSLATION logic, the opposite
direction). `ZR-2` is about vendor vocabulary inside `core/` — not applicable (`composition/` is
allowed to see vendor vocabulary by design). `ZR-3` is the `tools/`<->`backend/src/` boundary
specifically — not applicable (this is entirely within `backend/src/`, between two zones
`lint-imports` already permits to see each other: `composition` importing/duplicating `adapters`
logic is legal by the eight contracts, exactly the shape the brief's Context section names as "the
motivating fact" for this whole sprint). `ZR-6`/`ZR-7` are about port signatures and pagination
completeness respectively — not applicable.

**Proposed rule (zone-shaped, stated here per C5 — NOT added to `docs/scrum/wiki/zone-rules.md` by
this story).** Deliberately not catalogued inline: `zone-rules.md` was under a concurrent
quality-review re-read for the whole of this story's session (this story's own brief: "a concurrent
re-review of it is running"), and STORY-195's own precedent is exactly this shape — its original
audit pass reported `GAP-1` as an unscored observation WITHOUT touching `zone-rules.md`; the
promotion to a formal, catalogued rule (`ZR-6`) happened only in a LATER, separate quality-review fix
round. This report follows that same precedent rather than editing a file under active review.

> **Draft `ZR-8` (proposed, not landed).** *Statement:* composition-zone code that constructs a
> vendor-specific artifact (a query string, a request payload shape) that an adapter under
> `backend/src/adapters/` already owns the construction AND validation of must call the adapter's
> builder, not re-implement a parallel version that silently drops part of its validation. *Source:*
> the PO's general "adapters translate, they don't decide" principle, applied to the specific case
> where TWO modules both translate the same vendor concept and only one does it completely — the
> `composition`/`adapters` pairing specifically, since `lint-imports`'s `adapters-independence`
> contract cannot see a composition-side REIMPLEMENTATION (as opposed to an import) of adapter
> logic at all. *Compliant counter-pattern already in this codebase:* `tools/demo_engine/
> assumed_failure_codes.py` importing `PROVISIONAL_STATUS_MAPPING` rather than re-declaring it — the
> same reuse-not-reimplement discipline `ZR-3` already enforces one zone-pair over. *Coverage
> verdict:* `GUARDABLE` only as a reviewed lint warning (an AST check for "two functions in
> different files both build a query/payload for the same vendor concept" is a semantic judgement,
> not a clean import-edge check), similar in spirit and in stated limitation to `ZR-6`.

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
  with the same five keyword arguments, sourced from `config.statuspage_mapping()` and either
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

- **Does anything in `composition/` make a decision that belongs in a core service?** No, with one
  documented and deliberately-scoped exception. `orchestrate.py`, `pull_loop.py`, `seed_dynamo.py`,
  `dynamo.py` are pure wiring — every branch in them routes to a named core service/query/domain
  type and returns its result unchanged. `sample_mode.py::SampleModeIngest.ingest_observations`
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
  `build_publisher` functions). The one genuine duplication this audit found in `composition/` —
  `vendor_health.py` re-implementing a fragment of `adapters/inbound/dynatrace/query.py`'s
  query-building — is a `composition`<->`adapters` duplication, not a `run.py`<->`app.py` one, so it
  is reported separately as `GAP-2` (§4), not as a `ZR-5` finding.
- **Does either root read configuration through a path the other does not?** No — both resolve
  `config_dir`, `dynamo_observations_table`/`dynamo_control_table`, and the Statuspage credential
  pair through the identical `Settings`/`StatuspageSecrets` dataclasses, as cited above.

## 6. Filed stories (AC2 — MAJORs as their own stories; MINORs batched)

`STORY-202` and `STORY-203` below are proposed, not written to `.scrum/backlog.yaml` by this report
(the orchestrator is its sole writer, per this story's own operating constraints).

### STORY-202 — `env_matrix.py` must import the Statuspage secret env-var names from `settings.py`, not re-declare them (2 `ZR-3` MAJORs)

- **Type:** defect (`ZR-3`, `MAJOR` ×2 — a credential-safety-relevant duplicated declaration).
- **Estimate:** 1 (fibonacci) — a two-line import-and-use change in one file.
- **Offending citations:** `tools/demo_loop_gate/env_matrix.py:75`
  (`env["STATUSPAGE_PAGE_ID"] = statuspage_page_id`) and `tools/demo_loop_gate/env_matrix.py:77`
  (`env["STATUSPAGE_API_KEY"] = statuspage_api_token`), duplicating
  `backend/src/composition/settings.py:49` (`STATUSPAGE_PAGE_ID_VAR`) and
  `backend/src/composition/settings.py:50` (`STATUSPAGE_API_KEY_VAR`).
- **Context:** see §3c. A rename of either constant in `settings.py` would silently defeat this
  harness's fake-credential injection into the credentialed API subprocess, letting
  `composition/asgi.py`'s `load_dotenv()` fill the gap with REAL repo-root `.env` Statuspage
  credentials instead — the exact risk CLAUDE.md's demo-engine section and this harness's own
  docstrings both treat as load-bearing.
- **Acceptance criteria (testable):**
  - AC1: `tools/demo_loop_gate/env_matrix.py` imports `STATUSPAGE_PAGE_ID_VAR` and
    `STATUSPAGE_API_KEY_VAR` from `src.composition.settings` and uses them as the two `env[...]`
    dict keys in `build_child_env`, in place of the two literal strings.
  - AC2: A test asserts `build_child_env(...)`'s returned dict has keys equal to
    `settings.STATUSPAGE_PAGE_ID_VAR`/`settings.STATUSPAGE_API_KEY_VAR` — pinned via the imported
    symbols, not re-typed literals, so a future rename of either constant would move this test's
    own expectation with it, not silently pass a now-wrong key.
  - AC3: Existing `demo_loop_gate` tests exercising `build_child_env` continue to pass unchanged.

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

### STORY-204 — reuse the adapter's DQL query builder + validation inside `composition/vendor_health.py` (catalogue gap, unscored)

- **Type:** chore (catalogue gap, not a `ZR-n` — draft `ZR-8` above; no live-observed vendor error
  has ever exercised this path, per CLAUDE.md's "two things to know").
- **Estimate:** 2 (fibonacci).
- **Offending citation:** `backend/src/composition/vendor_health.py:40-53`
  (`build_vendor_health_query`), which does not call or reuse
  `backend/src/adapters/inbound/dynatrace/query.py:41-49,79-82`'s `InvalidNativeIdError` validation.
- **Context:** see §4. Refinement should decide the shape (a small shared validator both builders
  call, vs. `vendor_health.py` composing its query around a shared "quote and validate" helper
  `query.py` exports) rather than this audit prescribing the fix.
- **Acceptance criteria (testable):**
  - AC1: A `native_id` containing a DQL-breaking character (`"`, `\`, newline, carriage return)
    raises the SAME named error (`InvalidNativeIdError` or an equivalent re-exported from `query.py`)
    from `build_vendor_health_query` that `build_dql_query` already raises, rather than silently
    building a malformed query.
  - AC2: A test constructs `build_vendor_health_query` with a breaking-character `native_id` and
    asserts the named error, mirroring `query.py`'s own existing `InvalidNativeIdError` test.
  - AC3: Existing `test_vendor_health.py` tests continue to pass unchanged for well-formed ids.

## 7. `CLEARED` entries, summarized (AC6 — STORY-195 AC4's rule)

Every `CLEARED` entry above is recorded with its reason in place (§3c, §3d, §5) rather than left
silent. Summarized for the record:

1. Six numeric ZR-3 sweep hits (`tools/demo_engine/server.py:244`; `parents[2]` in four files;
   `tools/demo_loop_gate/harness.py:903`'s slice bound; a self-test fixture value) — coincidental int collisions with
   `FreshnessConfig.reentry_cycles`/`stale_after_cycles`, unrelated in meaning. `INDEPENDENT`.
2. `tools/demo_engine/rows.py`'s `STATUS_CODE_HEALTHY`/`STATUS_MESSAGE_HEALTHY` vs
   `health_mapping.py`'s inline OR-rule literals. Out of `ZR-3`'s pinned scope (neither shape on the
   `backend/src/` side) AND semantically safer than a true duplicate (an OR-rule, not a sole source
   of truth). `INDEPENDENT`.
3. `tools/demo_loop_gate/failure_path_reality_gate.py`'s `_DUMMY_LOCAL_CREDENTIAL = "test"` vs
   `composition/dynamo.py`'s inline `"test"`/`"test"` literals. Out of `ZR-3`'s pinned scope
   (function-body literal on the `backend/src/` side, neither declared shape), and independently
   documented in the citing file's own docstring. `INDEPENDENT`.
4. `composition/sample_mode.py::SampleModeIngest` forcing `Health.DOWN` — a domain-shaped decision
   living in `composition/`, not `core/services/`. `CLEARED`: a first-class, documented, PO-approved
   TEMPORARY design (STORY-048), tracked for removal (STORY-155), inert since the trial expired.
5. `api/dependencies.py` as a THIRD shared location every `api/v1/*` feature reaches into, beyond
   the brief's literal "core and `api/v1/_shared`" — see §8. `CLEARED`: pure FastAPI DI accessor
   functions typed against `src.core.ports`, no business logic, no cross-feature reach.

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

**Real run against this report** (final version, after all sections above):

Command: `python citation_sweep_story196.py docs/scrum/sprints/2026-07-31-sprint-66/audit-api-composition-tools.md`

```
OK   backend/src/composition/settings.py:21-22 (file has 119 lines) [line-count only, no anchor]
OK   backend/src/composition/settings.py:22 (file has 119 lines) [line-count only, no anchor]
OK   tools/demo_loop_gate/harness.py:750 (file has 971 lines) [line-count only, no anchor]
OK   tools/demo_engine/server.py:244 (file has 254 lines) [line-count only, no anchor]
OK   tools/demo_loop_gate/backfill_reality_gate.py:30 (file has 114 lines) [line-count only, no anchor]
OK   tools/demo_loop_gate/failure_path_reality_gate.py:65 (file has 556 lines) [line-count only, no anchor]
OK   tools/demo_loop_gate/guard_reality_gate.py:23 (file has 132 lines) [line-count only, no anchor]
OK   tools/demo_loop_gate/harness.py:49 (file has 971 lines) [line-count only, no anchor]
OK   tools/demo_loop_gate/harness.py:903 (file has 971 lines) [line-count only, no anchor]
OK   tools/demo_loop_gate/harness.py:964 (file has 971 lines) [line-count only, no anchor]
OK   tools/demo_loop_gate/failure_path_reality_gate.py:390 (file has 556 lines) [line-count only, no anchor]
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
OK   tools/demo_engine/store.py:22 (file has 83 lines) [anchor matched: 'VENDOR_HEALTH_WINDOW = timedelta(hours=2)']
OK   backend/src/composition/vendor_health.py:37 (file has 133 lines) [anchor matched: '_HEALTH_CHECK_WINDOW = "2h"']
OK   tools/demo_engine/store.py:20-21 (file has 83 lines) [line-count only, no anchor]
OK   tools/demo_engine/store.py:73-83 (file has 83 lines) [line-count only, no anchor]
OK   tools/demo_engine/rows.py:33-34 (file has 93 lines) [anchor matched: 'STATUS_CODE_HEALTHY = "0"']
OK   backend/src/adapters/inbound/dynatrace/health_mapping.py:73 (file has 88 lines) [anchor matched: 'if code == "0" or message == "HEALTHY":']
OK   tools/demo_engine/rows.py:26-32 (file has 93 lines) [line-count only, no anchor]
OK   tools/demo_loop_gate/failure_path_reality_gate.py:148 (file has 556 lines) [anchor matched: '_DUMMY_LOCAL_CREDENTIAL = "test"']
OK   backend/src/composition/dynamo.py:23-24 (file has 26 lines) [anchor matched: 'resource_kwargs["aws_access_key_id"] = "test"']
OK   tools/demo_loop_gate/failure_path_reality_gate.py:138-147 (file has 556 lines) [line-count only, no anchor]
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

Extracted 67 citation occurrence(s), 47 distinct (path, line-spec) pair(s) checked -- 19 content-anchor-verified, 28 line-count-only (no anchor present), 0 failure(s).
```

**Note on the two extra occurrences (65 -> 67):** this report cites its OWN sweep output inside a
fenced code block (self-referential by construction — the report describes the sweep that checks the
report). The first embed (65 occurrences) was captured before the summary sentence below it named two
more citations by example; both were bare filenames at first (a self-inflicted defect of exactly the
kind this section exists to catch), fixed to full repo-relative paths, and the count above is the
sweep's OWN final re-run AFTER that fix — not silently re-adjusted to match a stale number.

**0 failures on the real, final run** — every one of this report's 47 distinct `path:line` citations
resolves, 19 of them content-anchor-verified (not merely line-count-checked). The 28 line-count-only
entries are mostly multi-line ranges (e.g. `backend/src/composition/settings.py:79-90`,
`backend/src/composition/vendor_health.py:40-53`) where the
report's own prose does not carry a literal single-line excerpt to check against — consistent with
STORY-195's own experience that most citations in a report like this are ranges or symbol references,
not single-line literal quotes.

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

```
$ git diff --name-only d4ad03e..HEAD -- backend/src frontend config
```

Empty. Confirmed at HEAD `10ee45a` (the two commits landed on `sprint-66` since STORY-196 was
dispatched — `d0019f8` and `10ee45a` — touch only `docs/scrum/sprints/2026-07-31-sprint-66/
audit-core-adapters.md` and `docs/scrum/stories/STORY-199-paginate-persistence-list-methods.md`,
neither under `backend/src/`, `frontend/`, or `config/`; verified via `git show --stat` on both).
C1 holds for this story's own commits, which touch only this report and `.scrum/sprint-current.yaml`
(orchestrator-owned, not written by this story).

## 12. Wiki

`docs/scrum/wiki/zone-rules.md` is NOT edited by this story (see §4 — the catalogue-gap observation
is deliberately left unscored/uncatalogued, mirroring `GAP-1`'s own original-pass precedent, and the
file was under a concurrent quality-review re-read for this story's duration per the brief). No other
wiki article's `code_refs` overlap this story's diff (this report + the story file only), so no wiki
blast radius applies. `yt_wiki.py`'s default checks (`sweep facts links refs integrity`) were CLEAN
before this story started and are unaffected by a docs-only diff outside `docs/scrum/wiki/`.

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
