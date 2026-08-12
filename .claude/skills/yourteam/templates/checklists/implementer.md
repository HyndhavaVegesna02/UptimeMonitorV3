# Implementer Checklist — <PROJECT>

> YourTeam v2 template (yourteam_version: 2.0.0). Core items apply to every project; the
> project-conventions section starts empty and grows via retro routing (each item lands with
> a date + motivating incident, like a working agreement).

## Process discipline

- [ ] Commit after every green TDD step; multi-part passes (e.g. wiki updates) commit part-by-part. Keep uncommitted work under ~30 minutes, always.
- [ ] Scoped staging only — never `git add -A` / `git add .` (hook-enforced).
- [ ] Current branch equals the sprint branch before every commit (hook-enforced). Worktree dispatch: `git merge <sprint-branch>` FIRST — worktrees are cut from the branch base, not its tip.
- [ ] Never write `.scrum/` state — report; the orchestrator records.
- [ ] Report green only from a CLEAN committed tree — a gate result over uncommitted changes does not count.
- [ ] A story that changes DoD/build/test/run commands updates CLAUDE.md in the same commit.
- [ ] A story that deletes code records the why in the story file History — it feeds the wiki tombstone.

## Test discipline

- [ ] Every function over a collection has an explicit, tested empty-input behavior: a named domain error or a documented default — never a leaked stdlib message.
- [ ] Range/window/interval math tests a NON-aligned boundary case, not just clean inputs.
- [ ] A port's test fake and its real adapter agree on edge behavior — the SAME contract test runs against both; both raise the same named errors, including the lost-race path.
- [ ] Check-then-act across a boundary: the write side raises a NAMED domain error on the 0-row race, the edge maps it, and a test FORCES the race.
- [ ] Composition/assembly tests construct the REAL wired objects — mock only genuine I/O edges; never patch the `__init__` of a thing under assembly.
- [ ] A contract change REWRITES the covering tests; deleting one to a coverage gap is review-blocking.
- [ ] Fixtures derive from a REAL captured sample — never invented at a plausible-looking scale.
- [ ] A story adding side effects to a process entrypoint enumerates every existing test driving that entrypoint and proves each stays hermetic.
- [ ] Resource-lifecycle code tears down on EVERY failure path, including partial setup, with a leak regression test.
- [ ] No module-scope side effects that can crash import/collection — resolve lazily with a guarded default.

## Code conventions (this project)

<!-- Seeded empty at inception. Items enter via retro routing or immediate PO direction,
     each with a date + motivating incident. -->

## Wiki discipline

- [ ] Route new knowledge before writing it: a test/lint first, then CLAUDE.md, then a `tier: reference` article for reasons — a new `tier: map` article is the last resort, because it is the only one with recurring cost.
- [ ] Blast radius is the MECHANICAL sweep over all map articles (`yt_wiki.py sweep`) — never hand-picked. Run it AFTER your last commit; there is no `verified_sha` to bump.
- [ ] Facts cite SYMBOLS (`file.py::name`), not bare line numbers.
- [ ] Every Fact's cited file is covered by the article's `code_refs`; `code_refs` list the files that DEFINE the subject, not everything it touches.
