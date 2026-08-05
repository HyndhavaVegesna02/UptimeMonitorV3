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

- `:19-21` declares the defaults as dataclass field defaults:
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
   at `:51` already uses `or None` deliberately. Decide per field rather than applying one pattern
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
declares three literals twice — `:19-21` as dataclass field defaults (`"us-east-1"`,
`"uptime-observations"`, `"uptime-control"`) and `:46-49` again as `os.environ.get(..., "<literal>")`
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
