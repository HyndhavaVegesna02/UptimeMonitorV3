---
id: STORY-218
title: Settings declares every default TWICE — and the ZR-3 sweep is structurally blind to it
type: chore
points: null
status: draft
filed: 2026-08-04
sprint: null
---

## Context

**Found by STORY-203's quality review, as a narrowing of a claim that story made.** STORY-203 pointed
`tools/demo_loop_gate/harness.py`'s defensive table-name blocklist at
`Settings.dynamo_observations_table` / `Settings.dynamo_control_table` instead of re-declaring those
literals, and its comment claims the blocklist therefore *"follows a future rename automatically."*

**That claim is true only of the declared field default — which is not what production resolves.**

Verified at HEAD 2026-08-04, `backend/src/composition/settings.py`:

- `:20-22` declares the defaults as dataclass field defaults (`:19` is `config_dir: str`, which has NO class default):
  `aws_region: str = "us-east-1"`, `dynamo_observations_table: str = "uptime-observations"`,
  `dynamo_control_table: str = "uptime-control"`.
- `:47-51` **re-declares all three as `os.environ.get(..., "<literal>")` fallbacks** inside
  `load_settings()`.
- `load_settings()` is the **only** construction site of `Settings`, and it passes **every** field
  explicitly. So the class-level defaults are never the value production resolves — they are
  reachable only by constructing `Settings` directly, which nothing in `backend/src` does.
- `backend/tests/test_settings.py:64-66` pins the **`load_settings()`** fallbacks, not the class
  defaults.

## Why this is a real drift path, not a tidiness complaint

Someone renaming the live default edits `load_settings()`'s fallback and the test that pins it, and
has no reason to touch line 20. Result: **the full suite stays green**, `Settings.dynamo_observations_table`
still returns the OLD name, and `harness.py`'s blocklist now guards a name nothing resolves to while
**permitting the real production default** — the precise failure the blocklist exists to prevent.
STORY-203's fix is correct today and its own guard tests are load-bearing (proven by mutation in two
independent reviews); this story is about the foundation it stands on.

## Why no existing guard catches it

`tools/zr3_duplicate_sweep.py` compares `backend/src/` declarations against `tools/` literals. **This
duplication is `src`-internal — both declarations are in the same file** — so the sweep is
*structurally* blind to it, the same class of blind spot already documented for the
cross-representation `store.py` case (STORY-203's "the fifth case"). A clean ZR-3 sweep says nothing
about it, which is exactly why it survived the sprint-66 audit and three ZR-3 stories.

## Refinement should settle

1. **Which declaration is canonical?** The obvious shape is
   `os.environ.get(VAR) or Settings.<field>` — or a module-level `_DEFAULTS` mapping both sides read
   — so the literal exists once. Confirm this keeps `load_settings()` readable; it is the
   most-read function in the composition zone.
2. **Careful with falsiness.** `os.environ.get(VAR) or <default>` treats an explicitly-set EMPTY
   string as absent. That is arguably right for a table name and arguably wrong; `dynamo_endpoint_url`
   at `:52` already uses `or None` deliberately. Decide per field rather than applying one pattern
   blindly, and record the reasoning.
3. **Does the guard extend?** Consider whether `zr3_duplicate_sweep.py` (or a sibling) should detect
   `src`-internal duplication of a settings default. That may be a separate, larger story — the
   sweep's whole design is `src`-vs-`tools`. Do not let scoping that block fixing the duplication.
4. **Re-check STORY-203's comment.** `harness.py`'s "follows a future rename automatically" becomes
   unconditionally true once this lands, and its wording should be revisited in the same change.

## Not in scope

STORY-203's blocklist fix itself (correct, reviewed, and passed). The env-var-NAME duplications
(STORY-215). Widening the ZR-3 sweep to cross-representation cases.

---

## Planning re-check, 2026-08-05 (sprint-69 planning) — **estimate 2, NOT in sprint 69**

**Re-verified at HEAD; the finding is unchanged and exact.** `backend/src/composition/settings.py`
declares three literals twice — `:20-22` as dataclass field defaults (`"us-east-1"`,
`"uptime-observations"`, `"uptime-control"`) and `:47`/`:49`/`:51` again as `os.environ.get(..., "<literal>")`
fallbacks inside `load_settings()`, which is still the only construction site and still passes every
field explicitly. `config_dir` is the one field with **no** class default, so it is declared once —
worth noting because it is the shape the other three should converge on.

**Sized 2.** One field-by-field decision (question 2, falsiness) is the only real thinking; the edit
is small and `test_settings.py` already pins the resolved values, so the regression surface is
covered before the change starts.

**Question 3 splits out.** Extending `zr3_duplicate_sweep.py` to see `src`-internal duplication is a
redesign of a sweep built around `src`-vs-`tools`, and this story's own text says not to let that
block the fix. If a guard is wanted, it is a separate story — file it when this one lands, sized
against what the fix actually looks like.

Deliberately NOT pulled into sprint 69: it is a duplication fix, not an audit-closure guard, and
sprint 69 is already at its committed size.

---

## Refinement, 2026-08-13 (sprint-70 planning) — **estimate 2, AC authored**

The one piece of real thinking is question 2 (falsiness), and AC2 forces it to be decided per field
and written down rather than pattern-applied. `config_dir` — the one field already declared once — is
the shape the other three converge on.

## Proposed Acceptance Criteria

- [ ] **AC1 — each default literal is declared exactly ONCE, and the DATACLASS FIELD DEFAULT is the
      canonical location.** The three duplicated literals (`"us-east-1"`, `"uptime-observations"`,
      `"uptime-control"`) appear one time each; `load_settings()` reads `Settings.<field>` instead of
      re-typing them. Asserted by grep-count in the story's History, with the count shown.
      **The `_DEFAULTS`-mapping and the "converge on `config_dir`'s no-class-default shape" options
      are FORBIDDEN, and this is the reason:** `tools/demo_loop_gate/harness.py:763` and `:770` read
      `Settings.dynamo_observations_table` / `Settings.dynamo_control_table` **as class attributes**,
      which works only because they are dataclass field defaults. Either alternative shape removes the
      class attribute and raises `AttributeError` there — making AC4 unsatisfiable and turning AC6
      into a rewrite. The earlier "converge on `config_dir`" note in this file is superseded by this
      clause.
- [ ] **AC2 — the falsiness decision is made PER FIELD and recorded in the code**, not in the story
      only. `Settings` has **five** fields (`settings.py:19-23`) and all five are covered by name:
      `config_dir`, `aws_region`, `dynamo_observations_table`, `dynamo_control_table`,
      `dynamo_endpoint_url`. For each, a comment or docstring states what an explicitly-set EMPTY env
      var resolves to and why. Two carry specific hazards: `dynamo_endpoint_url`'s deliberate
      `or None` (`:52`) is preserved or its change justified in the same place; and **`config_dir` is
      the risky one** — `os.environ.get(CONFIG_DIR_VAR, "config/apps")` (`:46`) resolves
      `CONFIG_DIR=""` to `""`, not to the default, and `CONFIG_DIR` is the entire publish guard, so
      changing its empty-string behaviour changes which Statuspage a demo loop can reach.
- [ ] **AC3 — a test pins the empty-string behaviour** decided in AC2, one case per field, against
      `load_settings()` — the only construction site and the only path production resolves.
- [ ] **AC4 — shown RED, the rename-drift direction (A9).** This is the defect, so it is the proof:
      rename the single surviving default to a new literal and demonstrate that
      `harness.py`'s table-name blocklist **follows it** and that the suite reflects the rename.
      Before this story, renaming the `load_settings()` fallback while leaving the class default
      alone kept the suite GREEN with the blocklist guarding a dead name. Record both output tails.
- [ ] **AC5 — shown RED, the vacuity direction (A9).** Delete the single declaration entirely and
      show at least one AC3 test goes RED, proving the tests pin the live path rather than a
      constant they also define.
- [ ] **AC6 — STORY-203's comment in `harness.py` is revisited in this change.** "Follows a future
      rename automatically" is unconditionally true only after this lands; the wording is corrected
      to say what is now true, and cites this story.
- [ ] **AC7 — the ZR-3 blind spot is STATED, not silently left.** `zr3_duplicate_sweep.py` compares
      `src` against `tools`, so it is structurally blind to this `src`-internal case. Widening the
      sweep is OUT of scope (see Not in scope); a docstring or catalogue line must say the sweep
      does not cover `src`-internal duplication, so a clean sweep is never read as covering it.
- [ ] **AC8** — full 8/8 DoD gate green at the final HEAD.
