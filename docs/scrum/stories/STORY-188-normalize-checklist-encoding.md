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

**FINAL MEASURED DAMAGE — 12 sites across 5 files.** Corrected twice during execution; both
corrections are recorded here rather than tidied away, because each is instructive.

| File | Invalid UTF-8 bytes | Genuine pre-existing `U+FFFD` | Sites |
| --- | --- | --- | --- |
| `.scrum/checklists/implementer.md` | 0 | 3 | 3 |
| `.scrum/checklists/plan-verification.md` | **2** — `0x97` @ 3492, 3640 | 0 | 2 |
| `.scrum/checklists/quality-review.md` | **3** — `0x97` @ 2833, 2883, 3007 | 0 | 3 |
| `.scrum/checklists/spec-review.md` | 0 | 0 | 0 |
| `.scrum/backlog.yaml` | 0 | **2** | 2 |
| `.scrum/working-agreements.md` | 0 | **2** | 2 |
| **Total** | **5** | **7** | **12** |

**Correction 1 — the planning figure of "13 sites" was wrong; it double-counted.** That count was
produced by decoding each file with `errors="replace"` and counting `U+FFFD` — but that decode
*converts every invalid byte into a `U+FFFD`*, so the "existing FFFD" column silently re-counted the
invalid bytes already tallied in the other column. `plan-verification.md` reported 2 invalid **and**
2 FFFD; `quality-review.md` 3 and 3 — identical numbers, which was the tell. Only `implementer.md`'s
3 were genuine, because it had no invalid bytes to manufacture them. The repair script's own
`!= 13` assertion caught this and exited non-zero rather than reporting success — the guard working
as designed. `yt-plan-verifier` had "independently reproduced" the table, almost certainly by
repeating the same `errors="replace"` method, which is a useful reminder that reproducing a
measurement is not the same as validating its method.

**Correction 2 — the defect was never confined to `.scrum/checklists/`.** Scanning all of `.scrum/`
while building AC6's guard found **two more corrupted files nobody had measured**: `backlog.yaml`
(2) and — worse — `working-agreements.md` (2), the retro-landed process rules loaded into every
session. Losing a character there silently loses part of a **rule**. Both are repaired under this
story: the defect class, the blast radius and the fix are identical, and shipping a guard over
`.scrum/` while knowingly leaving two files inside it corrupt would be theatre.

**The whole defect is one character.** `0x97` is cp1252 EM DASH; all 5 invalid bytes are em-dashes
written in the wrong codec, and all 7 `U+FFFD` are em-dashes already destroyed by an earlier lossy
round-trip. Every one sits in the same prose shape (`"VERIFICATION — process gone by PID"`,
`"sprint-50 CloudFront CachePolicyId — two failed stack creates"`, `"sprint-51 redeploy — push
succeeded"`). Reconstruction is **certain, not guesswork**: all 12 sites become `U+2014`.

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

- [ ] **AC1** — Every file under `.scrum/` decodes as valid UTF-8 with **zero** invalid bytes,
      verified by a byte-level check (not by an editor opening them successfully). Scope widened from
      "the four checklists" during execution — see Correction 2.
- [ ] **AC2** — All 12 damaged sites (5 invalid `0x97` + 7 genuine `U+FFFD`) are `U+2014` EM DASH.
      **Zero** `U+FFFD` remain anywhere under `.scrum/`.
- [ ] **AC3** — **No other byte changes.** The diff touches only those 12 sites. Every checklist item,
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
  (`plan-verification.md`). Kept at 1 point: the fix is mechanical and the correct replacement
  character is certain. Assigned to the orchestrator and sequenced first.
- 2026-07-30: **executed by the orchestrator on `sprint-65`.** Two corrections landed during
  execution (both detailed in Context): the "13 sites" planning figure was a **double-count** caused
  by measuring with `errors="replace"`, and the defect was **never confined to
  `.scrum/checklists/`** — `backlog.yaml` and `working-agreements.md` were also corrupt. Final: 12
  sites, 5 files. Repair was byte-precise: only bytes the UTF-8 validity scanner flagged were
  replaced, so a `0x97` appearing as a legitimate continuation byte (e.g. `U+2017` = `E2 80 97`) was
  copied through untouched — a naive `bytes.replace` would have corrupted those.
  AC6's guard landed as `.claude/skills/yourteam/scripts/tests/test_scrum_encoding.py` (the
  `yt_selftest` rung, project-generic, skips cleanly with no `.scrum/`) and was **shown failing
  twice, independently**: probe A injected a raw `0x97` (fails the validity test); probe B injected a
  `U+FFFD` into an otherwise perfectly valid UTF-8 file (fails the replacement-char test). Probe B is
  the one that matters — it proves the two checks are not redundant, since a file can be valid UTF-8
  and still be full of already-destroyed characters.
