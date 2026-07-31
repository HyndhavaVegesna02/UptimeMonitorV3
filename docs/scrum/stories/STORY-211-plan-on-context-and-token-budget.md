---
id: STORY-211
title: Plan sprints on context and token budget instead of story points
type: chore
---

## Context

Sprint planning currently sizes work in fibonacci story points, with `velocity.json`
as a "sanity reference". Two problems, both observable in this repo's own record:

1. **Points measure a constraint that does not bind here.** Points exist in human
   Scrum to manage human time and social commitment. `SKILL.md` already concedes
   velocity is "a record, not a planning input" — an artifact that is written every
   sprint and read by nothing. Sprint 38 recorded 31 points against a 5-point norm
   and nothing reacted, because no mechanism consumes the number.
2. **The constraint that DOES bind was bolted on separately as prose.** The
   2026-07-29 "Window Check" agreement exists because session rate limits actually
   stop work: sprint 46 was pushed to an external agent by a limit, sprint 45
   consumed two full 5-hour windows, STORY-149's first implementer died mid-story.
   The 2026-07-15 token audit recorded a $22 session that changed 9 lines and 1.7M
   cache-write tokens traced to subagent prefix re-writes.

So the process carefully estimates something that cannot run out, and informally
tracks the one thing that can.

Filed 2026-08-01 out of the YourTeam process-analysis session that also produced
the ratchet-brake changes (rule expiry, freeze exemption, evidence-rule collapse,
CLAUDE.md prune). PO deferred this one deliberately: it is the largest of the five
and it changes a planning ceremony, so it wants its own sprint rather than riding
along with the checklist edits.

## Description

Replace story points and velocity as the planning unit with two measured numbers
per story, and make sprint capacity a function of the session budget that actually
binds.

**Number 1 — dispatches (cost).** One agent run is the unit that burns budget:
- 1–2 pt story → 1 dispatch (implementer) + gate
- 3+ pt story → 3 dispatches (implementer + spec reviewer + quality reviewer)
- plus observed fix-round rate

A sprint is then "roughly N dispatches", not "11 points".

**Number 2 — brief load (feasibility).** Each subagent starts with a fresh window
holding: the fixed prefix (system prompt + tool schemas), the brief (story file,
plan steps, checklist, wiki Facts), the files it must read, and then everything it
accumulates while working — test output, its own edits, re-reads, one cycle per
green TDD step. If the starting load leaves too little working room, the agent
compacts mid-story and the earliest-loaded material is what gets dropped: the
checklist. A story whose projected working room does not fit gets split. This
replaces "an 8 must be split" with a rule expressed in the currency that decides
whether the dispatch actually succeeds.

**Threshold must be measured, not guessed.** Do not ship a bare fraction ("half
the window") — that is a voodoo constant of exactly the kind
`.scrum/checklists/implementer.md` and Anthropic's skill guidance both reject. The
story's job is to derive it from this repo's observed numbers.

Note the highest-leverage input is likely the **fixed prefix**, not the brief: the
2026-07-15 audit found an unrestricted implementer re-writing a ~125k cached prefix
per dispatch purely from inherited MCP tool schemas. Measure that first; if it
dominates, the threshold question is secondary to keeping tool allowlists tight.

## Acceptance Criteria

- [ ] AC1: The fixed per-dispatch prefix is measured for each of the five `yt-*`
      agent definitions, from a real dispatch on a trivial task, and recorded with
      the raw figures (cache-write / input tokens per dispatch).
- [ ] AC2: Per-green-step working cost is measured on at least three real stories
      of differing size, and the observed cost per step recorded with its spread.
- [ ] AC3: A split threshold is derived from AC1 + AC2 and stated as a formula over
      measured inputs, never a bare fraction. The derivation shows its own inputs.
- [ ] AC4: `.claude/skills/yourteam/references/ceremonies.md` §3 (Sprint Planning)
      sizes stories in dispatches + brief load. Kept project-GENERIC per the
      2026-07-13 PO directive: no repo-specific numbers in the skill; measured
      constants live in project state.
- [ ] AC5: Sprint capacity is expressed as `projected dispatches × observed cost
      per dispatch ≤ budget headroom`, and the Window Check (2026-07-29 agreement)
      is named as the instrument that reads it, rather than being a separate rule.
- [ ] AC6: Points, fibonacci estimation and `velocity.json` are either removed or
      explicitly retained with a stated reason. If retained, the reason names what
      consumes the number — "a record" is not a reason.
- [ ] AC7: The change is applied to at least one real planning session and the
      predicted vs actual dispatch count and budget consumption are both recorded.
      A prediction that cannot be compared to an outcome is not evidence.
- [ ] AC8: Backward compatibility with existing history: past `velocity.json`
      entries remain readable and their meaning is documented, so sprint history
      does not become uninterpretable.

## Open Questions

- Does the effort cap ("3× estimate → auto-Blocked") survive the removal of
  estimates, and if so what does it become — 3× projected dispatches?
- Do the two reviewers count as one dispatch or two for budgeting? They run
  concurrently but bill separately; the sprint-66 review explicitly warns against
  trimming the two-reviewer ceremony to save budget, so this must not become an
  argument for cutting it.

## History
- 2026-08-01: drafted from the YourTeam process-analysis session. DRAFT — needs
  refinement, AC review and an estimate before it may enter a sprint.
