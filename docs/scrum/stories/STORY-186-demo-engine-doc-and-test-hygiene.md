---
id: STORY-186
title: Demo-engine doc and test hygiene batch (wiki prose, parametrised rejection tests, minors)
type: chore
points: 1
status: ready
refined: 2026-07-30   # PO-approved `ready` at the sprint-64 refinement ("approve all five"); the
                      # frontmatter was never updated to match, which the sprint-65 plan-verifier
                      # caught as a Definition-of-Ready failure. Recorded here, not re-approved.
---

> **CUT FROM SPRINT 65 at plan verification (2026-07-30), PO-approved.** The conflict that caused
> the cut is **DISCHARGED**: STORY-191 and STORY-184 both landed (sprint 65 / sprint 66), so
> nothing else is extending these files.
>
> ## *** CITATIONS RE-VERIFIED 2026-08-14 at sprint-72 planning — the body below is stale, this table is not ***
>
> The story's own cut-note demanded this before any dispatch. Every citation in the body was
> re-derived at HEAD `fa5507d`. **Use these, not the line numbers written inline below.**
>
> | Body says | Actually, at `fa5507d` |
> | --- | --- |
> | `scenario.py:57` (`load_scenario_file` is ~90 lines) | **`tools/demo_engine/scenario.py:116`** |
> | `scenario.py:84-87` (`{path!r}`) | **`scenario.py:121`**; the "filename-prefixed convention" docstring is **`scenario.py:173`** |
> | `test_scenario.py:295-405`, **seven** rejection tests | **nine** functions at **`test_scenario.py:331, 340, 366, 380, 394, 408, 423, 444, 458`** (file is 469 lines) |
> | `test_scenario.py:180` (recomputes the `(max_threshold + 2) * interval` formula) | **`test_scenario.py:259, 269, 272`** |
> | `test_scenario.py:283` (`import yaml` mid-body) | **`test_scenario.py:347`** |
> | `demo-engine.md:231` ("rather than the rows") | **`docs/scrum/wiki/demo-engine.md:352`** |
> | `test_scenario_coverage.py:235` (same claim) | **not present** — the claim survives only in the wiki article above; the file is 295 lines |
> | `test_scenario_coverage.py:73-76` ("a port signature change would be caught here too") | **`test_scenario_coverage.py:74`** |
> | `test_scenario_coverage.py:107` (coherence test vs docstring) | docstring claim is **`test_scenario_coverage.py:5`** |
> | `test_scenario_coverage.py:79 / :94 / :56` (`saved`, "above", `rejected_repo_result`) | **`:79, :82` / `:94` / `:59`** — all still live |
>
> **Two scope changes fall out of that re-verification, and they are why this stays a 1:**
>
> 1. **The `CLAUDE.md:142` item is DISCHARGED.** The `interval_seconds` / "land in the future"
>    sentence **no longer exists anywhere in `CLAUDE.md`** (grep, 2026-08-14) — STORY-184 removed
>    it, exactly as this story predicted it might. Do not re-add it; do not go looking for it.
> 2. **The `dev-setup-and-dod.md:237` item needs a decision, not an edit.** That article now lives
>    in **`docs/scrum/wiki/archive/`**. The protocol treats `archive/` as history. See AC1a.

## Context

The STORY-176 fix-round quality re-review (2026-07-30, PO-authorised after sprint-63 acceptance)
returned no critical and one major — filed as
[STORY-184](STORY-184-scenario-interval-invariant-on-the-type.md) — plus twelve minors. Round 1 had
also produced five minors that were deliberately deferred mid-sprint and confirmed **not worse** at
re-review.

None is a defect. All are accuracy or shape, in the same few files, which is why they are one story
rather than four: at 1 point each, four separate stories would be ceremony overhead on work a single
pass closes.

Two of these matter more than "hygiene" suggests, because they are **claims that are wrong** in
documents whose purpose is to be trusted — the same class STORY-181 spent a sprint retiring.

## Description

One pass over `tools/demo_engine/scenario.py`, `backend/tests/demo_engine/test_scenario.py`,
`backend/tests/demo_engine/test_scenario_coverage.py`, `docs/scrum/wiki/demo-engine.md`,
`docs/scrum/wiki/dev-setup-and-dod.md` and `CLAUDE.md`. No behaviour change. `tools/`, tests and docs
only — no file under `backend/src/`.

### Wrong claims (fix the claim, not just the wording)

- **`docs/scrum/wiki/demo-engine.md:231` and `test_scenario_coverage.py:235`** say the old staggered
  test compared buckets "built from the `since`/`interval` the test itself supplied **rather than the
  rows**". That misdescribes the mechanism: the rows *did* enter `bucket_into_cycles` — their
  timestamps were **washed out by bucketing**. The conclusion (the assertion could not have caught
  the false claim) is right; the reason given is not.
- **`test_scenario_coverage.py:73-76`** says subclassing the port means "a port signature change
  would be caught here too". An ABC catches an **added or renamed** abstract method at instantiation;
  a changed **signature** is caught by nothing in this repo — there is no mypy in the 8-command gate.
- **`CLAUDE.md:142`** says a non-positive `interval_seconds` is "the one input that would otherwise
  make expansion land in the future". True only relative to `end_time`: a caller passing a future
  `end_time` also lands rows in the wall-clock future. `scenario.py`'s "at or before `end_time`" is
  the precise phrasing. (Coordinate with STORY-184, which may change this text anyway.)
- **`docs/scrum/wiki/dev-setup-and-dod.md:237`** — the re-verification entry enumerates `CLAUDE.md`
  and `conftest.py` as the flagged `code_refs`, but `.scrum/definition-of-done.md` also changed in
  that range (`e107811`, "five contracts" → "eight"). The omitted change *confirms* the article's
  Fact, so nothing stale was stamped — but the entry cannot be **audited** as complete, which is the
  whole point of recording a re-verification.

### Prose and structure

- **`docs/scrum/wiki/demo-engine.md:224-234`** — the bolded M1 Correction block is wedged into the
  middle of the five-case enumeration; the closing paren at `"could not have caught the false
  claim),"` balances only by accident, and the list reads as broken. Lift the correction into its own
  bullet or a History line.
- **`scenario.py:84-87`** uses `{path!r}` (which prints `WindowsPath('...')`) while every message
  added in the fix round uses plain `{path}`. Also the docstring's "matching the filename-prefixed
  convention `composition/config.py::load_config` uses" is inaccurate in detail — `config.py` prints
  `yaml_path.name`, not the full path.
- **`scenario.py:57`** — `load_scenario_file` is ~90 lines. Lift the per-block checks into a
  `_validated_block(path, signal_key, block)` helper so the loop stays readable. **The reviewer
  explicitly advised against table-ifying the checks themselves**: each carries a distinct, tested
  message, so a table would need a per-field message column *and* a per-field predicate — the same
  volume plus an indirection. Do not "simplify" them.

### Tests

- **`test_scenario.py:295-405`** — seven near-identical rejection tests, each with its own inline
  YAML, all matching only on the signal key (`"demo-signal"`), which every message contains. So none
  pins the rejection **reason**. Parametrise over `(yaml_body, expected_message_fragment)` and add the
  currently unpinned `interval_seconds: true` case (a `bool` is an `int` subclass; the code handles it,
  no test proves it).
- **`test_scenario_coverage.py:107`** — the coherence test is not driven through the ingest chain,
  contradicting the module docstring's "Every case is driven through the REAL production ingest
  chain". Either reword the docstring or move the test. It also loops instead of parametrising, so the
  first failing file hides the rest, and `assert scenario_paths` guards that files exist but not that
  any signal was actually checked.
- Smaller: the fake names its list `saved` while both peer fakes it cites name it `rejected`
  (`test_scenario_coverage.py:79`); `:94` says "Every `_ingest_scenario` call **above**" when the
  calls are below; `:56` names an `IngestResult` `rejected_repo_result`.
- **Deferred from round 1:** hardcoded `timedelta(seconds=30)` and `30 * 7` instead of reading
  `cfg.signal(...).interval_seconds` and the thresholds block; `test_scenario.py:180` recomputing
  `orchestrate.py:98`'s `(max_threshold + 2) * interval` formula, so a change there leaves the test
  green while its claim goes stale; `import yaml` mid-body at `test_scenario.py:283`; and the
  identical four-entry `expected_locations` repeated on all 41 monitors plus the identical
  `locations:` block in all three fleet files (YAML anchors would remove ~40 lines per file).

## Acceptance Criteria

- [ ] **AC1 (every LIVE wrong claim above is corrected, and each correction is checked against the
      code)** — the items under "Wrong claims" **that the 2026-08-14 re-verification left standing**:
      the `demo-engine.md:352` mechanism claim and the `test_scenario_coverage.py:74` signature
      claim. The `CLAUDE.md` item is discharged and must not be re-opened. A behavioural wiki Fact
      that changes cites the test that pins it (working agreement A2).
- [ ] **AC1a (the archived article is a decision, recorded — not a silent skip)** — the
      `dev-setup-and-dod.md:237` item targets a file now in `docs/scrum/wiki/archive/`. Either
      correct it and say why an archived tombstone was edited, or leave it and say why. State which,
      in one sentence, in the report. Editing `docs/scrum/wiki/` proper is what the sweep watches;
      `archive/` is history and is not swept — that asymmetry is the reason this needs a sentence
      rather than a judgement call made in silence.
- [ ] **AC2 (the rejection tests pin reasons)** — the **nine** loader rejection tests
      (`test_scenario.py:331, 340, 366, 380, 394, 408, 423, 444, 458`) become a parametrised table
      asserting a message fragment identifying the **specific** rejection, not just the signal key,
      and the `interval_seconds: true` case is added. A wrong-reason rejection must now fail.
- [ ] **AC3 (the coherence test's home matches its docstring)** — either the module docstring stops
      claiming every case runs through the ingest chain, or the test does. Parametrised per scenario
      file so one bad file does not hide the others.
- [ ] **AC4 (`load_scenario_file` is readable)** — per-block checks live in a helper; the individual
      checks and their messages are **unchanged in behaviour**. Every existing rejection test still
      passes.
- [ ] **AC5 (no behaviour change anywhere)** — proven mechanically, in the manner STORY-181 used: for
      each changed `.py` file, the docstring-stripped AST is identical before and after, **except**
      the files where AC2/AC3/AC4 deliberately restructure tests, which are listed explicitly with
      their reason.
- [ ] **AC6 (production untouched)** — `git diff` touches no file under `backend/src/`.
- [ ] **AC7** — the DoD gate commands the diff can affect exit 0. The test count may drop where seven
      tests become one parametrised case: state the arithmetic so the drop is visibly intentional.

## Open Questions

None.

## History

- 2026-07-30: filed from the STORY-176 fix-round quality re-review (12 minors) plus the five round-1
  minors deferred during sprint 63. Batched deliberately. Estimated 1 point. Coordinate with
  [STORY-184](STORY-184-scenario-interval-invariant-on-the-type.md), which touches the same docstring
  and the same `CLAUDE.md` sentence.
