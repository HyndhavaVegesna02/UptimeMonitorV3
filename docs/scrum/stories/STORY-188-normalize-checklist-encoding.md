---
id: STORY-188
title: Normalize the .scrum/checklists encoding — they are a live corruption landmine
type: defect
points: 1
status: ready
refined: 2026-07-30
---

## Context

`.scrum/checklists/` holds the four role checklists loaded by every implementer, reviewer and
plan-verifier dispatch. Some of them are **not valid UTF-8**, and some already contain permanently
lost characters.

**The landmine fired once during sprint 64** (STORY-187): an edit pipeline reading one of these files
silently corrupted text it had never been asked to touch, and it was caught only because the diff was
read before committing. The sprint-64 board recorded the workaround still in force today — *"EDIT
THOSE TWO FILES BYTE-SAFELY (read/write via latin-1, append additions as UTF-8) until 188 lands."*

Sprint-65 refinement re-measured the damage and it is **about double what the retro recorded**:

| File | Invalid UTF-8 bytes | Existing `U+FFFD` (already-lost characters) |
| --- | --- | --- |
| `implementer.md` | 0 | 3 |
| `plan-verification.md` | **2** — `0x97` at byte 3492, 3640 | **2** |
| `quality-review.md` | **3** — `0x97` at byte 2833, 2883, 3007 | **3** |
| `spec-review.md` | 0 | 0 |

The retro named only `quality-review.md` (3 bytes) and `implementer.md` (3 FFFD).
**`plan-verification.md` was missed entirely** — and it is the checklist the plan-verifier reads,
which sprint 65 dispatches.

**The whole defect is one character.** `0x97` is cp1252 EM DASH; all 5 invalid bytes are em-dashes
written as cp1252 instead of UTF-8, and all 8 `U+FFFD` are em-dashes already destroyed by an earlier
bad round-trip. Every one sits in the same prose shape (`"VERIFICATION — process gone by PID"`,
`"sprint-50 CloudFront CachePolicyId — two failed stack creates"`). So reconstruction is **certain,
not guesswork**: all 13 sites become `U+2014`.

**The templates are clean.** All four files under
`.claude/skills/yourteam/templates/checklists/` are valid UTF-8 with zero `U+FFFD`, confirming the
corruption happened after generation, in the project instances. (The affected lines are
retro-routed, project-specific additions that were never in the templates, so the templates are
confirmation of the cause, not a recovery source.)

## Who executes this

**The orchestrator, not the sprint's external implementer**, even though sprint 65 runs in external
mode. YourTeam's *What You Never Do* list includes letting a subagent write `.scrum/` state, and an
external agent sits further outside than a subagent. This story is process infrastructure; it is
handed to nobody.

It is sequenced **first** in the sprint, because until it lands every later dispatch that reads or
edits a checklist carries the same corruption risk that already fired once.

## Acceptance Criteria

- [ ] **AC1** — All four files in `.scrum/checklists/` decode as valid UTF-8 with **zero** invalid
      bytes, verified by a byte-level check (not by an editor opening them successfully).
- [ ] **AC2** — All 13 damaged sites (5 invalid `0x97` + 8 existing `U+FFFD`) are `U+2014` EM DASH.
      **Zero** `U+FFFD` remain in any of the four files.
- [ ] **AC3** — **No other byte changes.** The diff touches only those 13 sites. Every checklist item,
      its date and its motivating-incident citation survive verbatim — these are retro-landed process
      rules and losing one silently loses a rule. Verified by reading the diff, per the sprint-64
      incident where the corruption was caught exactly that way.
- [ ] **AC4** — `python .claude/skills/yourteam/scripts/yt_selftest.py` still exits 0 (28/28). It is
      green today *with* the corruption present, so template/instance parity is not byte-comparing
      this content — but it is asserted after the change rather than assumed.
- [ ] **AC5** — The sprint-64 byte-safe-editing workaround is **retired**: the board note instructing
      latin-1 read/write on these files is removed or marked closed, so no future session keeps
      applying a workaround for a fixed defect.
- [ ] **AC6** — A **mechanical guard** is added so this cannot silently recur: a check that fails when
      any file in `.scrum/checklists/` is not valid UTF-8 or contains `U+FFFD`. Prefer the lowest
      available rung — a test or a `yt_selftest` case over a prose note. If it lands in the skill's
      self-test it must stay **project-generic** (PO directive 2026-07-13): no hardcoded project
      names or paths beyond the standard `.scrum/` layout.

## Notes

`ruff`/`pytest`/`lint-imports` do not read `.scrum/`, so no backend gate command can detect this —
which is why AC6 exists. The full eight-command DoD gate still applies to the sprint as a whole.

## History

- 2026-07-30: filed as a sprint-64 follow-up after the corruption fired once during STORY-187 and was
  caught only by a pre-commit diff read.
- 2026-07-30: refined at sprint-65 planning. Scope corrected upward — a **third** affected file
  (`plan-verification.md`) and 5 more damaged sites than recorded. Kept at 1 point: the fix is
  mechanical and the correct replacement character is certain. Assigned to the orchestrator and
  sequenced first.
