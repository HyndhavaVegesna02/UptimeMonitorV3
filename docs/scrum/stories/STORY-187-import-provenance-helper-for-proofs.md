---
id: STORY-187
title: An import-provenance helper so a proof can prove WHICH code it ran
type: chore
---

## Context

This is the **mechanical rung that working agreements A1, its 2026-07-29 refinement, and A3 have all
declined to take**, each time for a defensible reason and each time leaving a checklist line to do a
script's job. It has now been proposed at two retros (sprint 62 and sprint 63). The sprint-63 retro
records that a third slip would itself be the finding — so it is filed rather than proposed again.

**What the checklist lines currently ask a human (or an agent) to remember:**

> Before reporting either score, print the imported module's `__file__` and the value under test and
> confirm the path lies inside the worktree.

That instruction exists because of a real, repeated failure. This repo is installed **editable**
(`package-dir = {"" = "backend"}` in `pyproject.toml`), so setuptools' finder resolves `src.*` to
`<repo>/backend/src` — the **main tree** — from inside *any* git worktree, whatever pytest's cwd is.
A discrimination proof run in a worktree therefore executes the same code on both sides and comes
back identical. Sprint 63 hit this on STORY-180's proof: it reported 4/4 on **both** sides, and
"green both sides" reads as *"this constant does not matter"* — the proof would have argued
**against** a correct fix.

The same sprint then produced a **second** provenance-shaped failure with a different mechanism: the
orchestrator's own publish-guard harness walked a `delegate` attribute where the layers store
`_delegate` (`publish_helper.py:51/:96/:169`), so it reported a one-element chain on both sides — the
safe side green for the wrong reason and the unsafe side falsely looking safe. A3 was written because
the *symptom* (both sides agreeing) generalises even though the mechanisms do not.

**Why a script can hold this even though A1/A3 concluded a script cannot.** Those conclusions are
about the *whole* proof — a reality-gate harness is bespoke per story, so nothing can judge whether a
given pair of assertions could have diverged. But **import provenance is not bespoke.** "Which file
did this module actually come from, and is it the tree I think I am testing?" is the same question
every time, and it is exactly the part that silently failed.

## Description

A small dev-only helper that a proof calls **before** it reports anything, which answers "which code
am I running?" and fails loudly when the answer is not the tree under test.

Placement: `tools/`, alongside the demo engine — dev-only, never in the production image, and free to
import `src.*`. **Not** `.claude/skills/yourteam/scripts/` (that is shared skill tooling, frozen
outside a story by the 2026-07-15 agreement, and this helper is project-specific) and **not** under
`backend/src/`.

Sketch, not a specification — the implementer decides the shape:

```python
assert_import_root("src.composition.vendor_health", expected_root=Path.cwd())
# -> raises with BOTH paths in the message when the module resolved elsewhere
```

It must be usable from a bare `python -c` one-liner, since that is how these proofs are actually run.

## Acceptance Criteria

- [ ] **AC1 (it reports provenance)** — Given a module name, the helper returns/prints the resolved
      `__file__` and the root it was resolved under, so a proof can put that line in its own output.
- [ ] **AC2 (it FAILS when provenance is wrong)** — When the module resolves outside the expected
      root, it raises a **named** error whose message contains both the expected root and the actual
      resolved path. A test proves the raise; the message content is asserted, not just the type.
- [ ] **AC3 (the editable-install trap is the regression test)** — A test reproduces the actual
      sprint-63 failure: a module resolvable from two roots, where the editable finder wins, is
      caught. If a real second worktree is impractical in a test, simulate it via `sys.path` /
      finder ordering and say so explicitly in the test's docstring — a simulation labelled as one is
      fine; a simulation passing as the real thing is not.
- [ ] **AC4 (usable from a one-liner)** — Evidence in the story: the actual `python -c "..."`
      invocation, with output, that a future proof would paste.
- [ ] **AC5 (the checklist lines point at it)** — The A1-refinement line in
      `.scrum/checklists/implementer.md` and A3's lines in `implementer.md` /
      `quality-review.md` are updated to name the helper as the way to satisfy them, with the manual
      `__file__` print kept as the fallback. **The prose rung is not deleted** — a script that exists
      but is not called is worse than a rule, so the rule stays and gains a tool.
- [ ] **AC6 (dev-only, production untouched)** — `git diff` touches no file under `backend/src/`, and
      nothing under `backend/src/` imports the helper.
- [ ] **AC7** — The DoD gate commands the diff can affect exit 0.

## Open Questions

None. Whether it is a module, a `pytest` fixture, or both is the implementer's call — AC4 forces the
one-liner path to work either way.

## History

- 2026-07-30: filed at the sprint-63 retro, after the retro entry for A3 observed that this rung had
  been proposed and skipped at two consecutive retros. Skipping was correct both times — the sprint-62
  proposal predated the failure that motivates it, and the sprint-63 refinement landed mid-sprint,
  when tooling is frozen by the 2026-01-01 agreement and ad-hoc skill-script edits outside a story are
  forbidden by the 2026-07-15 entry. Neither reason applies to a filed, planned story. Estimated
  1 point.
