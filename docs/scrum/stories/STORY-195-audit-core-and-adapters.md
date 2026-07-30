---
id: STORY-195
title: Audit the core and adapters zones against the rule catalogue
type: chore
points: 3
status: ready
refined: 2026-07-31
---

## Context

The first of two measuring passes in the sprint-66 audit. `core` and `adapters` go first because they
are where the motivating defect lived (STORY-190: an inbound adapter persisting through a core port,
legal under every contract) and because `core`'s independence is the invariant the whole hexagon rests
on — a violation there is worth more than one anywhere else.

Depends on **STORY-194**: findings cite `ZR-n` rule ids from `docs/scrum/wiki/zone-rules.md`. Without
the catalogue this story degrades into unfalsifiable opinion, which is the specific failure the PO
asked to avoid.

## Description

Read **every** module under `backend/src/core/` (31 files) and `backend/src/adapters/` (27 files),
excluding `__pycache__`, and judge each against the catalogue. Produce a point-in-time findings report
at `docs/scrum/sprints/2026-07-31-sprint-66/audit-core-adapters.md` — sprint history, not the wiki,
because a findings list describes a moment and must not be re-stamped later as if still current.

**The report is the deliverable; fixes are not.** Anything above MINOR becomes its own backlog story.
An audit that fixes as it goes produces one unreviewable mega-diff and no backlog, which is the exact
shape the PO ruled out.

Files-under-audit include the zone `__init__.py` files and `core/queries/` — the `layers` contract
names `src.core.queries` as the outermost core layer, so it is in scope like any other.

## Acceptance Criteria

- [ ] **AC1** — The report accounts for **every** module in both zones with no gaps: each file is
      listed exactly once with a verdict of `CLEAN` or one-or-more finding ids. The file-enumeration
      command and its output are recorded in the report, and the number of files listed equals that
      output's count. (Coverage that cannot be counted is coverage that cannot be trusted — "I read
      the zone" is not evidence.)
- [ ] **AC2** — Every finding carries all four of: the `ZR-n` rule id it violates; a `file:line` that
      resolves at the sprint HEAD; a severity of `MAJOR` (a real boundary breach in shipping code) or
      `MINOR` (shape, naming, or docstring); and one sentence naming **why the eight contracts pass
      it** — if the answer is "they don't, it would fail", it is not a finding for this audit, it is a
      broken build and must be reported as such immediately.
- [ ] **AC3** — Nothing is fixed inline. Every `MAJOR` finding is filed in `.scrum/backlog.yaml` as its
      own `draft` story with a title, the offending `file:line`, and at least one testable AC; `MINOR`
      findings may be batched into a single filed story. This story's diff touches **no** file under
      `backend/src/`, `frontend/` or `config/`.
- [ ] **AC4** — Candidates considered and rejected are recorded as `CLEARED` with the reason, not
      silently dropped — at minimum the vendor-prose-in-`core` case that STORY-194 AC5 rules
      compliant. A future audit must be able to see what was already adjudicated.
- [ ] **AC5** — Every claim is checked against code at the sprint HEAD, never against wiki or
      `CLAUDE.md` prose. Where the report contradicts an existing wiki article, the contradiction is
      named in the report with both addresses and the article is filed for update (a wiki claim that
      survives an audit unexamined is exactly the "trusted-and-wrong" state the protocol forbids).
- [ ] **AC6** — The five backend DoD commands exit 0, with pass/skip counts recorded and a zero skip
      count (`REQUIRE_DYNAMO=1`, `DYNAMO_ENDPOINT_URL=http://127.0.0.1:8021`).

## Open Questions

None.

## History

- 2026-07-31: drafted and refined in sprint-66 planning. 3 points: 58 modules read with judgement
  applied per file, plus backlog authoring for each finding. The planning probe already established
  the cheap violations are absent, so the yield here is in the subtle cases — which is slower reading,
  not faster.
