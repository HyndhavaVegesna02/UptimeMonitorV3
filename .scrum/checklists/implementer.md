# Implementer Checklist — Uptime Monitor V3

> YourTeam v2. Migration map PO-approved 2026-07-12 — this checklist is the BINDING home for
> these items; dates cite the original motivating agreement (full text in git history). New
> items enter via retro (enforcement-ladder routing) or immediate PO direction.
>
> **Amendments are audited for expiry at every retro** (2026-08-01 agreement). An item here
> earns its place by firing; one that has not fired in six sprints is proposed for DELETION,
> not relocation. Motivating incidents live in the originating sprint's `retro.md` — this file
> carries the RULE, not the story behind it.

## Process discipline

- [ ] Commit after every green TDD step; the wiki blast-radius pass commits **article-by-article** (2026-07-03). Keep uncommitted work under ~30 minutes, always.
- [ ] Scoped staging only — never `git add -A` / `git add .` (2026-06-24; hook-enforced).
- [ ] Current branch equals the sprint branch before every commit (edge-case #12; hook-enforced). Worktree dispatch: `git merge <sprint-branch>` FIRST (2026-07-08).
- [ ] Never write `.scrum/` state — report; the orchestrator records (2026-06-25).
- [ ] Report green only from a CLEAN committed tree — a gate result over uncommitted changes does not count (2026-06-29).
- [ ] A story that changes DoD/build/test/run commands updates CLAUDE.md in the same commit (2026-06-23).
- [ ] A story that deletes code records the why in the story file History — it feeds the wiki tombstone.
- [ ] Any server/container/process you spawn ends with an OS-level teardown VERIFICATION — process gone by PID (taskkill/kill + re-check) and port freed (netstat or equivalent). A wrapper-job kill alone is not evidence (2026-07-17).

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

## Evidence discipline

- [ ] **Any evidence artifact must be demonstrated FAILING before it is trusted.** Proof, gate,
      discrimination check, or a test that is a defect fix's primary evidence: before you report
      it, make it fail on purpose and record that it failed. A green result proves the code passes
      the check; it never proves the check could detect the defect. Five mechanics, all of which
      have shipped broken here at least once:
      - **Exit code, not stdout.** The artifact ends in an explicit verdict and a NON-ZERO exit on
        failure. Printing correct numbers while exiting 0 unconditionally is a report, not a gate,
        and a reader of its stdout cannot tell the difference. A polling timeout is a FAILURE, never
        partial evidence. The board records the EXIT CODE.
      - **Two sides must DIFFER.** A two-sided or discrimination proof records both outcomes and
        asserts they diverge. Identical outcomes is a FAILED proof whatever value appeared — "green
        both sides" reads as "the thing under test does not matter", so the proof argues AGAINST a
        correct fix.
      - **Mutate a computational deliverable.** If the headline claim is arithmetic, spacing,
        ordering, thresholds or windowing: mutate the computation, record which tests go RED,
        restore, confirm `git diff` is empty. Zero RED means UNPINNED — at full coverage, and with
        every AC traced to a test. Scoped to computational deliverables so it is not a tax on
        every story.
      - **Prove which tree ran.** For any check in a git worktree, call
        `tools/import_provenance.py::assert_import_root` for the module under test, per side,
        BEFORE reporting either score. This repo is installed EDITABLE — the `.pth` file is a plain
        absolute `sys.path` entry to `backend`, so `src.*` resolves to the MAIN tree from inside any
        worktree. Force `PYTHONPATH=<worktree>/backend` (it precedes that entry), or patch the main
        tree in place and restore it with `git diff` verified empty.
      - **Read back through the PRODUCTION interface.** If a proof sets up state, write it and read
        it back through the same interface the system under test uses — never a parallel hand-rolled
        one. A precondition that writes and re-reads its own wrong key passes VACUOUSLY and then
        reports a working feature as broken.
      Two smells to check your own test against before reporting: (a) does every fixture it
      constructs actually reach the code under test — a fake that is built, never wired up, then
      asserted on is asserting on a value the test itself supplied; (b) if you changed the guarded
      behaviour to something plainly WRONG, would this test go red? If you cannot say yes, it is
      decoration.
      (Collapsed 2026-08-01 from SIX amendments — A1 sprint-62; A1-refinement, A3 and A4 sprint-63;
      A7 sprint-64; A9 sprint-65 — which were six statements of one idea, each landed because the
      previous one had not held. Incidents in each sprint's `retro.md`. The mechanical half of this
      rule is STORY-212; six retros named the script rung and declined it.)

- [ ] **LAST STEP BEFORE YOU REPORT: re-run every command your story records, and paste the FRESH
      output.** Not the output you captured while working — the output as of the final commit. Every
      recorded command without exception: greps, counts, sweeps, gates, diff-scope checks. If a
      number changes, say so and explain why rather than substituting it quietly; if a command no
      longer runs at all, that is a finding about your own story. Do this AFTER your last edit,
      because the thing being measured is often the text you just edited.
      (2026-07-31, A13, PO-directed. Every story in sprint 66 shipped at least one recorded command
      whose output no longer reproduced, and NOT ONE was a wrong conclusion — every measurement was
      true when taken and stale when read. That is the point: this defect is invisible to the author
      precisely because it was correct when written. Re-running costs ~90 seconds.)

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
      is a paraphrase of the code's own docstring is marked as such or dropped — it is a
      restatement, not a verification (2026-07-29; the anti-flap article mirrored `pipeline.py`'s
      own docstring, which WAS the defect, and survived from sprint-8 to sprint-62 because article
      and code AGREED: git arithmetic detects divergence, never shared error).
