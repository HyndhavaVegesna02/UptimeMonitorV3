# Implementer Checklist — Uptime Monitor V3

> YourTeam v2. Migration map PO-approved 2026-07-12 — this checklist is the BINDING home for
> these items; dates cite the original motivating agreement (full text in git history). New
> items enter via retro (enforcement-ladder routing) or immediate PO direction.

## Process discipline

- [ ] Commit after every green TDD step; the wiki blast-radius pass commits **article-by-article** (2026-07-03). Keep uncommitted work under ~30 minutes, always.
- [ ] Scoped staging only — never `git add -A` / `git add .` (2026-06-24; hook-enforced).
- [ ] Current branch equals the sprint branch before every commit (edge-case #12; hook-enforced). Worktree dispatch: `git merge <sprint-branch>` FIRST (2026-07-08).
- [ ] Never write `.scrum/` state — report; the orchestrator records (2026-06-25).
- [ ] Report green only from a CLEAN committed tree — a gate result over uncommitted changes does not count (2026-06-29).
- [ ] A story that changes DoD/build/test/run commands updates CLAUDE.md in the same commit (2026-06-23).
- [ ] A story that deletes code records the why in the story file History — it feeds the wiki tombstone.

## Test discipline

- [ ] Every function over a collection has an explicit, tested empty-input behavior: a named domain error or a documented default — never a leaked stdlib message (2026-06-25).
- [ ] Range/window/interval math tests a NON-aligned boundary case (window not an integer multiple, partial trailing bucket), not just clean inputs (2026-06-25).
- [ ] A port's in-memory fake and its real adapter agree on edge behavior — the SAME contract test runs against both; both raise the same named domain errors, including the lost-race path (2026-06-26, 2026-06-28).
- [ ] Check-then-act across a port: the write side raises a NAMED domain error on the 0-row race, the edge maps it (e.g. HTTP 409), and a test FORCES the race (2026-06-28).
- [ ] Composition/assembly tests construct the REAL wired objects and assert actual structure — mock only genuine I/O edges; never patch the `__init__` of a thing under assembly (2026-06-29).
- [ ] A contract change REWRITES the covering tests to the new contract; deleting one to a coverage gap is review-blocking (2026-06-29).
- [ ] Fixtures derive from a REAL captured sample (live call or the producer's own fixtures) — never invented at a plausible-looking scale (2026-07-04).
- [ ] A story adding side effects to a process entrypoint (env loads, file reads, network, seeding) enumerates every existing test driving that entrypoint and proves each stays hermetic, stated in the report (2026-07-06).
- [ ] Resource-lifecycle code tears down on EVERY failure path — including partial setup before any finalizer exists — with a leak regression test (2026-06-25).

## Code conventions (this project)

- [ ] Module + public class/function docstrings citing the relevant dossier §, mirroring the peer modules (2026-06-27).
- [ ] Frozen value/result types enforce cross-field coherence invariants with `model_validator(mode="after")` + tests for both the rejected and valid shapes, in the same story (2026-06-26).
- [ ] N same-shape variants (per-type normalizers/handlers/parsers) share one assembly helper from the start; only genuinely per-variant logic lives per variant (2026-06-25).
- [ ] A new five-file API feature ships its five-file-shape test (set equality on `{__init__, controller, models, validation, service}.py`) in the same story (2026-06-28).
- [ ] Edge DTOs map a persisted entity's id directly — no `else 0` / sentinel fallback (2026-06-28).
- [ ] API endpoints reject tz-naive datetime inputs with 422 at the edge (`validation.py`), with a naive-input regression test (2026-06-28).
- [ ] No module-scope side effects that can crash import/collection (e.g. `float(os.environ[...])` at module scope) — resolve lazily with a guarded default (sprint-43 M1).
- [ ] Config naming a live vendor resource id (monitor id, component id) carries a drift check — probe that it resolves to live data before Done (2026-07-08).

## Wiki discipline

- [ ] Blast radius is the MECHANICAL sweep over all articles (`python .claude/skills/yourteam/scripts/yt_wiki.py sweep`) — never hand-picked; shared `code_refs` files drift multiple articles (2026-06-28).
- [ ] Facts cite SYMBOLS (`file.py::ClassName`, `file.py::function`) — bare line numbers only where no symbol applies (2026-06-27).
- [ ] Every Fact's cited file is covered by the article's `code_refs`; `code_refs` list the files that DEFINE the subject, not everything it touches (2026-06-25 ×2).
- [ ] A Fact asserting BEHAVIOUR (a branch, a threshold, a decision ladder, an error condition)
      cites the TEST that pins it alongside the implementation symbol. A Fact whose only support
      is a paraphrase of the code's own docstring is marked as such or dropped -- it is a
      restatement, not a verification (2026-07-29; sprint-62 STORY-149 -- the anti-flap article
      said `Health.DEGRADED` is "always degraded, regardless of length ... so no length
      comparison applies", which WAS the defect, faithfully mirroring `pipeline.py`'s own
      docstring. It survived from sprint-8 to sprint-62 because article and code AGREED: git
      arithmetic detects divergence, never shared error).

- [ ] A check run in a git WORKTREE must FIRST prove it is executing the worktree's code, not the
      main tree's: call `tools/import_provenance.py::assert_import_root(module_name, expected_root)`
      for the module under test and let it print/raise BEFORE reporting either score — it names both
      the expected root and the actual resolved path when they disagree (STORY-187). The manual
      fallback stays documented for a module the helper cannot import cleanly: print the imported
      module's `__file__` (and the value under test) and confirm the path is inside the worktree. This
      repo is installed EDITABLE (`package-dir = {"" = "backend"}`); the mechanism is a plain absolute
      `sys.path` entry — the `.pth` file `__editable__.uptime_monitor_v3-0.1.0.pth` contains exactly
      one line, the absolute path to `backend` — NOT a setuptools `MetaPathFinder` (corrected
      2026-07-30, STORY-187; the previous wording named "setuptools' finder", which pre-lock
      verification found wrong). That single `sys.path` entry resolves `src.*` to `<repo>/backend/src`
      from inside ANY worktree; force `PYTHONPATH=<worktree>/backend`, which precedes it. Patching the
      MAIN tree in place and restoring it (verifying `git diff` is empty afterwards) is the other
      acceptable route. (2026-07-29; sprint-63 STORY-180 -- the first run of AC2's discrimination proof
      reported GREEN ON BOTH SIDES because both sides were the same main-tree code; "green both sides"
      would have been read as "the constant does not matter", i.e. the proof would have argued AGAINST
      a correct fix. Applies to any worktree check, not just discrimination proofs.)

- [ ] Any server/container/process you spawn for a reality check ends with an OS-level
      teardown VERIFICATION � process gone by PID (taskkill/kill + re-check) and port freed
      (netstat or equivalent) � a wrapper-job kill alone is not evidence (2026-07-17;
      sprint-51 STORY-094 � the bash-job kill left the port-8010 uvicorn worker alive;
      an explicit taskkill /PID /F + netstat confirm was required).

- [ ] **A two-sided / discrimination proof must record BOTH outcomes and assert they DIFFER.** It is
      not enough that each side matches expectation: identical outcomes on both sides is a FAILED
      proof, never a passed one, whatever value appeared. The proof's authority comes from the sides
      diverging, so "green both sides" or "red both sides" means the proof did not discriminate and
      must be fixed before either number is reported. Where the symptom is import provenance
      specifically, call `tools/import_provenance.py::assert_import_root` per side (STORY-187) rather
      than eyeballing it — but the mechanism can differ per proof (attribute names, fixture skips,
      etc.), so the helper closes only the import-provenance case; the manual check (read the test
      body, confirm the sides could actually have diverged) remains the fallback for everything else.
      (2026-07-30, sprint-63 retro amendment A3 -- three proofs in ONE sprint came back identical on
      both sides: STORY-180's discrimination proof (the editable-install/worktree trap, see the A1
      refinement above), and the orchestrator's own publish-guard harness, which walked a `delegate`
      attribute where the layers store `_delegate` and so reported a one-element chain on both sides --
      the safe side green for the wrong reason and the unsafe side falsely looking safe. The A1
      refinement covers IMPORT PROVENANCE only and would not have caught the second: the mechanisms
      differ, the symptom does not. Treat the symptom as the trigger.)

- [ ] **If the story's headline deliverable is COMPUTATIONAL -- arithmetic, spacing, ordering,
      thresholds, windowing -- mutate the computation once and record which tests go RED.** Zero
      tests RED means the behaviour is UNPINNED, even at full coverage and even with every AC traced
      to a test. Restore and confirm `git diff` is empty. (2026-07-30, sprint-63 retro amendment A4
      -- STORY-176 shipped a green, reviewed, fully AC-traced suite in which a mutant
      `expand_scenario` that ignored `interval_seconds` and hardcoded 30s passed ALL THIRTY new
      tests. The story's headline claim -- "expands into rows at each monitor's own
      `interval_seconds`" -- was pinned by nothing. What found it was running the mutant; nothing
      else in the pipeline could have. Scoped deliberately to computational deliverables so this
      does not become a tax on every story.)
