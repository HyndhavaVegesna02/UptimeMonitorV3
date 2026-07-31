---
id: STORY-210
title: Device Guard blocks pytest.exe and cfn-lint.exe — two of the eight DoD commands cannot run
type: defect
points: 2
status: draft
filed: 2026-07-31
---

> **DRAFT — needs a refinement pass before it may enter a sprint** (Definition of Ready: approved AC
> + estimate + no open questions). The estimate below is the audit's or the orchestrator's first cut,
> not a refined one.

## Context

Filed during sprint 66, the boundary/code-discipline audit. **Authoritative detail:**
This story file; the evidence is in `.scrum/sprint-current.yaml`'s `dod_evidence` (both the RED and the green runs are kept).

This file exists so the story is visible in `docs/scrum/stories/` alongside every other story —
it was originally landed as a `.scrum/backlog.yaml` entry only, which made it findable at planning
but invisible here.

## The finding, as recorded when it was filed

```
*** THIS BLOCKS THE DOD GATE ITSELF, SO IT BLOCKS EVERY FUTURE STORY. Fix it
before the next sprint starts. ***
SYMPTOM: `python .claude/skills/yourteam/scripts/yt_gate.py` exits 1 with
pytest -> FAIL (4551) and cfn-lint -> FAIL (4551). The pytest output_tail reads
"...\.venv\Scripts\pytest.exe was blocked by your organization's Device Guard
policy."
PROVEN ENVIRONMENTAL, NOT CODE (per the 2026-07-06 agreement that a RED gate
must be PROVEN environmental before being discounted):
  - pytest PASSES in isolation via the MODULE form:
    .venv/Scripts/python.exe -m pytest -q  ->  689 passed, 0 skipped
    (the 685 baseline + the 4 new STORY-197 guard tests).
  - cfn-lint is blocked even via `python -m cfnlint`, one level deeper:
    "ImportError: DLL load failed while importing _regex: An Application
    Control policy has blocked this file." So the module form is NOT a
    workaround for cfn-lint the way it is for pytest.
  - infra/ is UNTOUCHED for the whole sprint (git diff sprint-66-start..HEAD
    -- infra/ is empty), so cfn-lint's input is byte-identical to runs that
    passed GREEN earlier the same day (baseline d4ad03e and the STORY-194/195/196
    scoped gates).
  - Reproduced twice back to back. Not intermittent.
  - The other six commands PASS, including all three frontend ones.
REGRESSED MID-SESSION: the sprint-66 baseline at d4ad03e was a full 8/8 GREEN
with this same runner, so the policy tightened during the sprint.
THERE IS DIRECT PRECEDENT FOR THE FIX ALREADY IN THIS REPO: the same policy
blocked .venv/Scripts/lint-imports.exe, and the DoD's import-boundary command
was changed to the python -c "from importlinter.cli import ..." module form
(CLAUDE.md Key commands records exactly this). The analogous change is
python -m pytest. cfn-lint needs more thought because its own DLL is blocked --
options include reinstalling regex, obtaining a policy exemption, or running
cfn-lint in Docker/CI rather than locally.
*** CHANGING .scrum/definition-of-done.md IS A PO DECISION -- it is the
mechanical contract the whole method rests on. Do not edit it unilaterally.
Raise at the sprint-66 review with the recommendation above. ***
```

## Acceptance Criteria

- [ ] To be lifted from the source above and approved at refinement. The source already states
      testable AC for this story; refinement's job is to confirm they are still accurate against the
      code, not to invent new ones.

## Open Questions

Refinement must confirm the estimate (2 points) and check
every `file:line` citation still resolves — this sprint repeatedly found citations that had drifted.
