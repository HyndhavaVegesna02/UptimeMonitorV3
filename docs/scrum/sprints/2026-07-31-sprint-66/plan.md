# Sprint 66 — Plan

**Date:** 2026-07-31 · **Branch:** `sprint-66` (off `sprint-65`, which stays unmerged) ·
**Start tag:** `sprint-66-start` · **Mode:** `in-process` · **Committed:** 11 points / 4 stories

## Goal

**Find the boundary violations the eight contracts cannot see, and turn as many as possible into
contracts that can.**

This is the audit sprint the PO asked to be reminded about at every planning until it was scheduled
or dropped (memory `wanted-architecture-audit-sprint`, raised at sprint-65 planning, scheduled here).
Its deliverable is **findings plus mechanical guards**, with every non-trivial fix filed as its own
story rather than done inline. The motivating fact: an inbound adapter persisting through a core port
passes all eight `lint-imports` contracts while being architecturally wrong (STORY-190). If one such
gap exists, others are probably already in the tree.

## Mode and ceremony

`in-process`. Audit work is judgement-heavy reading with no crisp hand-off surface, and sprint 65's
external delivery self-reported "verified" while `ruff` was RED with 22 errors — after which the PO
directed the whole fix round in-process. Per-story ceremony by points: 3-pointers get
implementer → spec-review ∥ quality-review → DoD gate → reality gate; the 2-pointer (STORY-196) is
scoped as a 3 for ceremony purposes anyway, because its duplicated-declaration sweep is the sprint's
only *novel* mechanical claim and needs the second reviewer.

## Plan verification

**yt-plan-verifier NOT dispatched.** Recorded per the token-economy amendment (2026-07-15): the
sprint is purely internal — three of four stories are docs-only, the fourth touches
`pyproject.toml`'s contract block and a test. No story consumes another component's output, no
adapter or vendor path is touched, there is no units/scale-sensitive logic, and the mode is not
`external`. The probe evidence a verifier would have checked was gathered directly at planning and is
recorded below, with the command that produced each number, so it is re-derivable rather than
asserted. **Two blocking gaps were found by that self-probe and are already folded into the AC**
(V4 and V5 below) — the plan would otherwise have shipped an unsatisfiable AC1 on STORY-194.

## Verified facts at planning (2026-07-31, at `d4ad03e`)

Every one of these is a command result, not a recollection. The audit's AC depend on them.

- **V1 — module counts** (`find <zone> -name "*.py" -not -path "*__pycache__*" | wc -l`, from
  `backend/src`): `core` **31**, `adapters` **27**, `api` **55**, `composition` **13**; `tools`
  **17** (from repo root). These are the denominators STORY-195 AC1 and STORY-196 AC1 must match.
  Sub-breakdown of the two zones in STORY-195: `core/domain` 9, `core/ports` 13, `core/services` 6,
  `core/queries` 2, `core` root 1; `adapters/inbound/dynatrace` 9, `adapters/persistence` 11,
  `adapters/outbound/statuspage` 3, package roots 4.
- **V2 — the cheap violations are absent.** `grep -rn "from src.adapters\|import adapters" api/`
  → **no matches**. `grep -rn "^from src\.\|^import src\." core/ | grep -v src.core` → **no
  matches**. The only `adapters/` modules importing `src.core.ports` are the 11 under
  `persistence/` plus `outbound/statuspage/__init__.py` — i.e. classes *implementing* the port they
  import, which is the compliant direction. **No inbound adapter holds a port.** The audit's yield is
  therefore in the subtle cases, which is slower reading, not faster.
- **V3 — vendor words inside `core/`: ~20 occurrences, every one in a docstring or comment.**
  Compliant examples to be named as such by STORY-194 AC5: `backend/src/core/domain/publication.py`
  (Statuspage named while explaining what an attempt records), `backend/src/core/domain/signal.py`
  ("a reader who has never heard of Dynatrace"), `backend/src/core/ports/__init__.py`. This is the
  single largest false-positive source in the sprint — un-adjudicated, it becomes ~20 bogus findings.
- **V4 — `docs/scrum/wiki/architecture-boundary.md` already owns the eight contracts**, each with a
  citation, `code_refs: [pyproject.toml, the four zone __init__.py]`, `verified_sha: b272c32`
  (sprint-63), `status: verified`. Its header records the sprint-5 retro amendment that narrowed
  those refs to boundary-*defining* files so in-zone additions do not falsely flag it stale.
  **Consequence, folded into STORY-194 AC1:** the catalogue **links** to that article for the
  "already mechanical" section instead of restating the contracts, and adopts the same narrow-refs
  discipline.
- **V5 — `yt_wiki.py` has FIVE checks, not four, and one is advisory.** Default set is
  `sweep facts links refs integrity`; `refs` (the code_ref *amplifier*) is advisory unless
  `--strict-refs` and can never fail the gate. `AMPLIFIER_THRESHOLD = 4` and **`pyproject.toml` is
  already a `code_ref` in 5 articles** — so an article adding it as a 6th widens a known amplifier.
  Also verified: `check_facts` requires every `` `path` `` cited in the **Facts** section to be
  covered by `code_refs` (`covered()` is prefix-based, so a directory ref covers everything beneath
  it), and `check_integrity` **rejects a 40-char `verified_sha`** — it must be 7–12 hex.
  STORY-194 AC1 was corrected against all of this before the sprint locked.
- **V6 — `lint-imports` structurally cannot see `tools/`.** `pyproject.toml`
  (`[tool.importlinter]`) sets `root_package = "src"`. The `tools/` → `backend/src/` one-way rule and
  the no-duplicated-constant rule therefore have **zero** mechanical coverage today, which is why
  STORY-196 calls that surface the sprint's highest-yield target and why STORY-197 expects a *test*
  rather than a contract for it.
- **V7 — baseline is green.** Full 8/8 gate at `d4ad03e`: `pytest` **685 passed, 0 skipped**,
  frontend `npm test` 363 passed (51 files), all eight commands exit 0. `yt_selftest` 32/32.
  Container `uptime_dynamo_8021` up on `127.0.0.1:8021`; `REQUIRE_DYNAMO=1` on every run so a
  Docker-less run fails loudly instead of silently skipping ~53 tests.

## Constraints

- **C1 — nothing is fixed inline.** Stories 195 and 196 produce findings and *filed stories*. Their
  diffs touch no file under `backend/src/`, `frontend/` or `config/`. This is a PO ruling, not a
  preference: an audit that fixes as it goes yields one unreviewable mega-diff and no backlog.
- **C2 — every count and every citation is re-derivable by command.** A docs sprint's only defence
  against hand-waving is that its claims can be re-run. Reports record the command *and* its output;
  reviewers re-run them. "I read the zone" is not evidence (this is the sprint's reality gate — see
  below).
- **C3 — a guard that has only ever been green is not a guard** (A7 + A9). Every new contract or test
  in STORY-197 is shown RED first, against the real violation or a deliberate mutation that is then
  reverted, with the command and its output recorded. A9 makes this a spec-review **verdict**
  condition: if the reviewer cannot answer "would this go red if I broke the guarded behaviour?",
  the AC is `NOT_MET`, not `MET`-with-a-note.
- **C4 — no new DoD gate command.** A ninth command changes `.scrum/definition-of-done.md`'s
  contract and needs its own PO decision. Guards ride inside the existing eight (an import-linter
  contract runs inside command 2; a test runs inside command 1). A rule guardable *only* by a new
  command is filed, not smuggled in.
- **C5 — the catalogue is the yardstick, and it is normative.** STORY-195/196 findings cite `ZR-n`
  ids. A finding with no rule id is either a new rule (amend the catalogue in the same sprint and say
  so) or an opinion (drop it). Rules that contradict `.scrum/working-agreements.md` lose: PO-stated
  rules outrank observed codebase patterns wherever they conflict.
- **C6 — env for every gate run:** `REQUIRE_DYNAMO=1`,
  `DYNAMO_ENDPOINT_URL=http://127.0.0.1:8021`, Docker Desktop up. Record pass/skip **counts** on
  every backend gate record; a nonzero skip count is an incomplete gate, not a pass.

## The reality gate for this sprint

An audit has no running surface, so the usual "exercise the live path" gate is replaced by a
**re-derivation** gate, which is executable and therefore real:

1. **Coverage is counted, not claimed.** Re-run each report's own enumeration command; the number of
   files it lists must equal the output. A mismatch fails the story.
2. **Every citation resolves.** Sweep every `path:line` in the catalogue and both reports: the path
   exists and the file has at least that many lines at the sprint HEAD. Recorded output, per story.
3. **Every filed story is real.** Each `MAJOR` finding's filed story id exists in
   `.scrum/backlog.yaml`, is `draft`, and carries at least one testable AC.
4. **STORY-196's sweep is shown capable of finding something** before its "no duplicates" result is
   accepted (AC3) — a sweep that has only ever returned empty proves nothing, the same failure shape
   as a green-only guard.
5. **STORY-197's guards are shown RED** (C3). This is the sprint's one true execution gate.

## Stories, in execution order

### 1 · STORY-194 — Zone-intent rule catalogue (3 pts)

`docs/scrum/stories/STORY-194-zone-intent-rule-catalogue.md`

- [x] Read the sources in priority order: `.scrum/working-agreements.md` (PO-stated rules first),
      memory `code-boundary-discipline`, `CLAUDE.md` "The four backend zones", dossier §4/§6 in
      `uptime-monitor-v3-design.html`, `pyproject.toml` `[tool.importlinter]`, and
      `docs/scrum/wiki/architecture-boundary.md` (V4 — do not restate its eight contracts).
- [x] Draft rules `ZR-1..ZR-n` covering at minimum the PO's five areas (AC4), each with statement,
      source, a compliant `file:line`, and a coverage verdict from the three-value set.
- [x] Draw the vendor-vocabulary line explicitly (AC5) using V3's citations as the compliant side.
- [x] Write `docs/scrum/wiki/zone-rules.md` with narrow `code_refs` = exactly the files its Facts
      cite, a short `verified_sha`, and a link to `architecture-boundary.md` for the mechanical set.
- [x] Run the citation-resolution sweep; record command + output in the story History (AC3).
- [x] `yt_wiki.py` CLEAN on the four blocking checks, no new `refs` note (AC1).
- [x] Scoped DoD gate, then commit.

### 2 · STORY-195 — Audit `core` + `adapters` (3 pts)

`docs/scrum/stories/STORY-195-audit-core-and-adapters.md`

- [x] Record the enumeration command and its output; build the file list (58 files per V1).
- [x] Read every module; verdict `CLEAN` or finding ids, one line per file.
- [x] For each finding: `ZR-n`, resolving `file:line`, `MAJOR`/`MINOR`, and why the contracts pass
      it — if the answer is "they don't", stop and report a broken build. (Zero `ZR-n` findings;
      one catalogue gap `GAP-1` reported separately, not scored MAJOR/MINOR.)
- [x] Record `CLEARED` entries with reasons, V3's vendor-prose case at minimum.
- [x] Name any contradiction with an existing wiki article, both addresses, and file the article for
      update (AC5). (None found — checked `persistence-adapters.md` directly.)
- [x] File every `MAJOR` as its own `draft` story; batch `MINOR`s into one. (No MAJOR/MINOR `ZR-n`
      findings to file; `GAP-1`'s fix filed as STORY-198 anyway, independent of catalogue status.)
- [x] Reality gate items 1–3; scoped DoD gate; commit.

### 3 · STORY-196 — Audit `api` + `composition` + the `tools/`→`src/` boundary (2 pts)

`docs/scrum/stories/STORY-196-audit-api-composition-tools-boundary.md`

- [ ] Same enumeration discipline over 85 files (V1).
- [ ] `api`: feature shape and whether any feature reaches outside its own dir / `_shared` (AC4).
- [ ] `composition`: whether the two roots (`run.py::main`, `app.py::create_app`) agree wherever
      disagreement changes behaviour, `CONFIG_DIR` included — a divergence is `MAJOR` (AC5).
- [ ] The duplicated-declaration sweep across the one-way boundary, **demonstrated capable** against
      the known-shared failure-code mapping before any empty result is accepted (AC3, gate item 4).
- [ ] File findings; reality gate items 1–4; scoped DoD gate; commit.

### 4 · STORY-197 — Land the guards, adjudicate every rule (3 pts)

`docs/scrum/stories/STORY-197-land-the-guards-the-audit-earned.md`

- [ ] Pick the two highest-severity `GUARDABLE` findings; state the stopping rule's outcome (AC5).
- [ ] Implement each guard at its rung — import-linter contract preferred, pytest test where
      `lint-imports` cannot see the surface (V6). No new gate command (C4).
- [ ] **Show each guard RED** (C3): real violation, or mutate → RED → revert, all recorded.
- [ ] Update every statement of the contract count (`CLAUDE.md` ×2, `.scrum/definition-of-done.md`,
      any wiki article), with `grep -rn` output before and after (AC4).
- [ ] Adjudicate every catalogue rule to a final verdict; re-stamp `verified_sha` only after an
      actual re-read (AC6).
- [ ] **Full** 8/8 gate on the final HEAD — not `--only`, because STORY-178 means a `--only` matching
      nothing exits 0 (AC7). Record pass/skip counts, skips at zero.

## Order, dependencies, drop order

194 → 195 → 196 → 197. Hard dependency: 195 and 196 cite the catalogue's rule ids, and 197 needs
both audits' severities. 195 and 196 are file-disjoint and could run in parallel, but 196 reuses the
report contract 195 establishes, so serial costs nothing and keeps the two reports identical in shape.

**Drop order if the session runs short: 196 first, then 197's second guard.** Never 194 (everything
depends on it) and never 197 entirely — a sprint that produces only reports fails the PO's stated
deliverable ("findings *plus* mechanical guards"). If 197 must shrink, one guard shown RED plus every
rule adjudicated is the minimum acceptable outcome, with the rest filed.

## Sizing note

11 points, deliberately at the top of the PO's stated ~9–11 baseline rather than above it. Sprint 65
ran 13 and the retro's honest read was that the size was absorbable but "bought less margin than it
looked" — three of five stories needed a fix round. The two 1-point doc chores carried out of
sprint 65 (STORY-186, STORY-189) are therefore **not** in this sprint, though both are now unblocked;
they are the first candidates for sprint 67.
