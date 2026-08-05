# Sprint 68 — Review

**Branch:** `sprint-68` (UNMERGED, per the standing directive — sprints 66, 67 and 68 all stay off main)
**Start:** `a270c29` (tag `sprint-68-start`) · **Head at review:** `f9c578c` · **99 commits**
**Goal:** close the sprint-66 audit's LIVE boundary violations — the code that is wrong today, not
guards for code that is already clean.

**Delivered: 10 of 10 points. All four stories code-complete, gated, and reality-gated.**

---

## Demo — evidence re-run live at review, not quoted from the board

| Claim | Command | Result |
| --- | --- | --- |
| Sprint goal's mechanical measure | `tools/zr3_duplicate_sweep.py` + AST-parse of `_ADJUDICATED` | **9 colliding pairs, 9 entries, `MUST-IMPORT-FROM-SRC` = 0** (was 4) |
| ZR-8 F1 — topology key schema | `grep -rln '"TOPOLOGY"' backend/src/` | **one file**: `adapters/persistence/topology_keys.py` (was 3, on both boot paths) |
| ZR-8 F2 — DQL in composition | `grep -c "fetch \|\| filter \|\| summarize " …/vendor_health.py` | **0** |
| Full DoD gate | `yt_gate.py` | **8/8 PASS** — 714 passed / 0 skipped, 8 contracts kept, ruff + cfn-lint clean, frontend 363 passed + build + lint |
| Wiki | `yt_wiki.py sweep facts links integrity` | **all four CLEAN** |

Test count moved 696 → 714 across the sprint. The known 1-in-11 `list_components` pagination flake
**did not fire once**, across every gate and reviewer run.

---

## Story-by-story

### STORY-205 — `seed_dynamo.py` must not own the key schema (3 pts) — ZR-8 Finding 1

The audit's biggest single miss: the DynamoDB topology key schema was hand-built three times, on the
boot path of **both** composition roots. Extracted to one module both repositories and the seed now
import.

- Both reviews clean (spec PASS, quality APPROVE); four minor findings all fixed rather than deferred.
- **Reality gate:** the real `scripts/seed_topology.py` run as a subprocess against real DynamoDB,
  read back through the real repositories. Persisted `pk='TOPOLOGY'` with `APP#httpcheck` /
  `COMPONENT#http-check` / `SIGNAL#http-check`; `list_components()`, `list_signals()` and
  `get('http-check')` all returned the seeded rows — exercising **both** AC1 key shapes.
- The quality reviewer enumerated the new AST guard against seven construction shapes and found it
  narrow — but `zone-rules.md` **says** it is narrow, in both the Coverage verdict and the row. Claim
  matches check; sprint 67's headline defect did not recur.
- AC6 required a follow-up story filed. The implementer **refused** — `.scrum/` is the orchestrator's
  ledger — and flagged the gap rather than marking AC6 satisfied. **STORY-217** filed before review ran.

### STORY-204 — vendor-health DQL builder into the adapter (2 pts) — ZR-8 Finding 2

`composition/vendor_health.py` built DQL without the adapter's breaking-character validation, and the
probe it feeds runs **first**, at loop startup. The builder moved into the adapter; no re-export shim.

- **Failed both reviews initially**, took three fix rounds.
- **Reality gate:** a real demo-engine HTTP server on a real socket, the real unmodified
  `make_grail_executor`, through the real `check_vendor_id_health` — the same call `run.py::main`
  makes. The relocated builder's DQL was answered (`[{'count()': 3}]`); all four breaking characters
  raised `InvalidNativeIdError`, each naming the offending value. Pre-fix that path silently built a
  malformed query.
- A real behaviour change surfaced honestly by the implementer: the probe now **aborts the loop
  process** on a bad `native_id`, where the ingest path degrades one signal per cycle. The call-site
  comment said the opposite and was corrected.
- ⚠ **AC7b NOT MET — see PO adjudication below.**

### STORY-203 — `tools/` imports shared literals (2 pts) — ZR-3 values

Four duplicated values closed; the `MUST-IMPORT-FROM-SRC` ledger reaches zero.

- Spec FAIL (AC7 only) → fixed; quality APPROVE with six minors (three fixed, one filed as
  **STORY-218**, one declined, one taken by the orchestrator).
- The implementer **exceeded its brief**: told to replace the blocklist's right-hand side and prove
  the blocklist still fires, it also deliberately committed the *forbidden* left-hand mistake and
  showed its own discrimination test go RED — converting "I avoided the trap" into "here is the test
  that would have caught me." Both reviewers reproduced it.
- **Reality gate:** tested the story's *claim*, not just its code. Renaming the declared default made
  the blocklist block the **new** name and release the old one — the drift-following property,
  demonstrated. Bounded honestly by STORY-218.
- ⚠ **AC7 NOT MET — see PO adjudication below.**

### STORY-215 — env-var NAME drift remainder (3 pts) — ZR-3 names

Two `DYNATRACE_*` names promoted to constants (nine total), `tools/` and the publish-guard tests
pointed at them, and `scripts/seed_topology.py` stopped resolving config on its own.

- Spec **PASS** (all 8 AC). Where the implementer's AC5 worktree had been cleaned up, the reviewer
  **built its own**, forced `PYTHONPATH`, printed `module.__file__`, and reproduced both halves
  itself rather than accepting inference.
- Quality FIX_REQUIRED with two MAJOR — **both inside the bullet written to document C3's third
  failure.** Three fix rounds; each found more than the last.
- **Reality gate:** the real `create_app()` under `CONFIG_DIR=config/demo` yielded
  `statuspage_mapping() == {}` — the publish guard holding, so no live publisher can be built. Then a
  rename of the constant's value propagated through `load_settings`, and the value-asserting pin
  survived untouched.
- **No AC unmet.** STORY-215's AC7 carries no same-commit clause, so this sprint's C3 misses here are
  constraint violations on the board, not AC failures. That distinction is not blurred.

---

## ⚠ Two items needing a PO verdict

Both are the **same constraint** (C3: the catalogue moves in the same commit as the code it
describes), in **STORY-204** and **STORY-203**, where AC7 explicitly required it.

- **Both final states are correct.** These are commit-sequencing misses: for a window of two commits,
  `zone-rules.md` described a violation the tree had already fixed.
- **Neither can be closed by any further work.** Only rewriting landed history would do it, and that
  was refused deliberately: those SHAs are cited in eight review reports and on the board, and
  squashing would destroy the TDD commit cadence — the mechanism that carried this sprint through
  **four** session-limit deaths with zero lost work.
- Both are recorded in the story files' own History rather than absorbed silently.

**Options:** accept as filed exceptions, or require a follow-up story recording the precedent.

---

## What the sprint produced beyond the points

**RC-2 — C3 failed five times, and the fifth settled how to fix it.** The count went 3 → 4 → 5 as
reviewers and the sprint-end compile pass each corrected the previous accounting, twice correcting
the orchestrator. The five split:

| # | Occurrence | A per-commit staleness sweep |
| --- | --- | --- |
| i | STORY-204: prose landed after its code | catches |
| ii | STORY-203: same | catches |
| iii | STORY-215: `verified_sha` bumped over a Fact not re-read | **misses** |
| iv | STORY-203: stamp over Facts displaced by its own import line | **misses** |
| v | citation into a file absent from the citing article's `code_refs`, plus a **source docstring** | **misses — structurally** |

**Only citation resolution catches all five**, and `tools/citation_sweep.py` already exists, already
resolves, and reports 126 findings while enforcing nothing. Filed as **STORY-219**, with the
false-positive backlog sized honestly so it cannot become the reason enforcement never lands.

**RC-1 — concurrent reviewers raced on the working tree** (the quality reviewer mutates to probe; the
spec reviewer cleaned that mutation out from under it). Mitigation applied from STORY-204 onward and
proven across four stories: every reviewer confirmed it touched no tracked file **and still produced
its sharpest findings**.

**Three stories filed from review findings:** STORY-217 (topology write port), STORY-218 (`Settings`
declares every default twice — invisible to the ZR-3 sweep because it is `src`-internal), STORY-219.

**An orchestrator error worth recording:** a fix-round brief asserted a CRLF trigger that does not
exist; the implementer wrote it into a `verified`-stamped wiki Fact in good faith, and the quality
reviewer disproved it end-to-end. Corrected in the wiki **and** in the board — the ledger enforcing
"never trusted-and-wrong" does not get an exemption.

---

## Closure map status

Sprint 68 was half of the PO-approved two-sprint plan to land all sprint-66 audit debt.
**Sprint 69 takes the second half** — STORY-206/207/208/209/216 (10 pts), all clean-tree rules proven
by mutation. When it closes, every ZR-1..ZR-8 rule has a terminal verdict.
