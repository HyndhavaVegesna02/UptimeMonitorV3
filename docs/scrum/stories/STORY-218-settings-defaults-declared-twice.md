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

- [x] **AC1 — each default literal is declared exactly ONCE, and the DATACLASS FIELD DEFAULT is the
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
- [x] **AC2 — the falsiness decision is made PER FIELD and recorded in the code**, not in the story
      only. `Settings` has **five** fields (`settings.py:19-23`) and all five are covered by name:
      `config_dir`, `aws_region`, `dynamo_observations_table`, `dynamo_control_table`,
      `dynamo_endpoint_url`. For each, a comment or docstring states what an explicitly-set EMPTY env
      var resolves to and why. Two carry specific hazards: `dynamo_endpoint_url`'s deliberate
      `or None` (`:52`) is preserved or its change justified in the same place; and **`config_dir` is
      the risky one** — `os.environ.get(CONFIG_DIR_VAR, "config/apps")` (`:46`) resolves
      `CONFIG_DIR=""` to `""`, not to the default, and `CONFIG_DIR` is the entire publish guard, so
      changing its empty-string behaviour changes which Statuspage a demo loop can reach.
- [x] **AC3 — a test pins the empty-string behaviour** decided in AC2, one case per field, against
      `load_settings()` — the only construction site and the only path production resolves.
- [x] **AC4 — shown RED, the rename-drift direction (A9).** This is the defect, so it is the proof:
      rename the single surviving default to a new literal and demonstrate that
      `harness.py`'s table-name blocklist **follows it** and that the suite reflects the rename.
      Before this story, renaming the `load_settings()` fallback while leaving the class default
      alone kept the suite GREEN with the blocklist guarding a dead name. Record both output tails.
- [x] **AC5 — shown RED, the vacuity direction (A9).** Delete the single declaration entirely and
      show at least one AC3 test goes RED, proving the tests pin the live path rather than a
      constant they also define.
- [x] **AC6 — STORY-203's comment in `harness.py` is revisited in this change.** "Follows a future
      rename automatically" is unconditionally true only after this lands; the wording is corrected
      to say what is now true, and cites this story.
- [x] **AC7 — the ZR-3 blind spot is STATED, not silently left.** `zr3_duplicate_sweep.py` compares
      `src` against `tools`, so it is structurally blind to this `src`-internal case. Widening the
      sweep is OUT of scope (see Not in scope); a docstring or catalogue line must say the sweep
      does not cover `src`-internal duplication, so a clean sweep is never read as covering it.
- [x] **AC8** — full 8/8 DoD gate green at the final HEAD.

---

## History — 2026-08-13 (STORY-218 execution, sprint-70)

### AC1 — single canonical declaration, grep-count evidence

`Settings` (`backend/src/composition/settings.py`) keeps its three dataclass field
defaults (`aws_region`, `dynamo_observations_table`, `dynamo_control_table`) as the
CANONICAL declaration; `load_settings()` now reads `Settings.<field>` instead of
re-typing the literal. `config_dir` is unchanged (no class default, by design — see
AC1's forbidden-shape clause). The `_DEFAULTS`-mapping and "converge on `config_dir`'s
shape" alternatives were NOT built, per AC1's own reasoning: both would delete the
class attribute `tools/demo_loop_gate/harness.py:773,780` reads directly.

Grep count, excluding build artifacts (measured fresh at the final HEAD, see the
implementer's report for the re-run):

```
grep -rn --include="*.py" --exclude-dir=__pycache__ -F "\"us-east-1\"" backend/src/
  -> backend/src/composition/settings.py:56   (1 hit)
grep -rn --include="*.py" --exclude-dir=__pycache__ -F "\"uptime-observations\"" backend/src/
  -> backend/src/composition/settings.py:57   (1 hit)
grep -rn --include="*.py" --exclude-dir=__pycache__ -F "\"uptime-control\"" backend/src/
  -> backend/src/composition/settings.py:58   (1 hit)
```

Each of the three literals appears exactly once under `backend/src/`.

### AC2 — falsiness decided per field, in the code

Recorded in `Settings`'s own docstring and `load_settings()`'s docstring
(`settings.py`), not only here:

- `config_dir` (the risky one): an explicitly-set empty `CONFIG_DIR=""` is preserved
  verbatim, NOT folded to `"config/apps"`. Changing this would mean an operator who
  emptied the publish-guard var got silently redirected to `config/apps`'s REAL
  `statuspage_component_id` — worse than a loud downstream failure on an empty path.
  Unchanged from before this story.
- `aws_region`, `dynamo_observations_table`, `dynamo_control_table`: empty is likewise
  preserved verbatim, for the analogous reason — an empty region/table name fails
  loudly against AWS/DynamoDB rather than silently substituting the production
  default. This was already the behaviour (`os.environ.get(VAR, default)` only
  substitutes on ABSENCE, never on falsiness); AC1's refactor does not change it,
  since `Settings.<field>` reads back the identical literal.
- `dynamo_endpoint_url`: kept exactly as it was — `or None` — because `None` means "no
  local override, talk to real AWS" for BOTH unset and explicitly-empty. No hazard
  symmetric to the other four; not changed.

### AC3 — one test per field pinning the decision

`backend/tests/test_settings.py`, five new tests appended after the existing ones (so
the anchor-checked `:30` citation in `zone-rules-history.md:185` is untouched):
`test_load_settings_empty_config_dir_is_preserved_verbatim`,
`..._aws_region_...`, `..._observations_table_...`, `..._control_table_...`, and
`test_load_settings_empty_dynamo_endpoint_url_resolves_to_none`. All pass against
`load_settings()` — the only construction site.

### AC4 — shown RED, rename-drift direction

Temporarily renamed the surviving `dynamo_observations_table` default to
`"uptime-observations-story218-renamed"`:

```
python -m pytest backend/tests/test_settings.py backend/tests/demo_loop_gate/test_harness_assertions.py backend/tests/test_zr3_duplicate_declarations.py -q
-> 1 failed, 28 passed
   FAILED backend/tests/test_settings.py::test_app_settings_dynamodb_defaults
   AssertionError: assert 'uptime-obser...ry218-renamed' == 'uptime-observations'
```

`test_app_settings_dynamodb_defaults` (an existing, un-touched test) goes RED because
`load_settings()`'s resolved value followed the renamed class default — **the suite
reflects the rename**, the assertion-VALUE branch.

Isolated re-run of the blocklist tests, same mutation still in place:

```
python -m pytest backend/tests/demo_loop_gate/test_harness_assertions.py -q -k blocklist
-> 3 passed, 15 deselected
```

`test_assert_ac1_preconditions_blocklist_fires_on_production_observations_table` (and
its two siblings) still PASS unedited — the blocklist's right-hand side
(`Settings.dynamo_observations_table`) and the resolved production value both read the
SAME renamed class attribute, so no test edit is required.

**CORRECTED 2026-08-13 after quality review (m2). This tail is a NO-REGRESSION
OBSERVATION, not a second branch of the proof.** The blocklist tests read
`Settings.<attr>` on BOTH sides (`test_harness_assertions.py:184`, `:196` against
`harness.py:773`), so they pass identically under this rename **pre-fix as well** —
which makes them non-discriminating about whether the fix worked. The evidence
discipline rejects a two-sided proof whose sides came back identical, and that is
what this is. The claim "the blocklist follows the rename automatically" is carried
ENTIRELY by the first tail above (the resolved value followed the rename and the
value assertion went RED). Recorded here because it is worth knowing the blocklist
did not regress — not because it proves anything the first tail does not.

Before this story (verified at HEAD 2026-08-04, unchanged fact restated, not
re-measured against the pre-fix code in this run): the equivalent rename on the OLD
two-declaration shape edited only `load_settings()`'s own literal fallback, leaving
`Settings.dynamo_observations_table` (the class attribute the blocklist reads) at the
OLD name — the suite stayed green and the blocklist guarded a dead name. That is the
defect this story fixes; AC4's mutation above is that same rename run forwards,
post-fix, showing it now propagates.

Reverted (`cp` from a pre-mutation backup); `git diff backend/src/composition/settings.py`
empty; full relevant suite back to green (see AC5's tail below, which re-confirms the
clean baseline immediately before its own mutation).

### AC5 — shown RED, vacuity direction

Temporarily removed `aws_region`'s class default entirely (`aws_region: str =
"us-east-1"` -> `aws_region: str`; legal field ordering, since `config_dir` already
has no default and precedes it):

```
python -m pytest backend/tests/test_settings.py -q
-> 9 failed
   AttributeError: type object 'Settings' has no attribute 'aws_region'
   (backend/src/composition/settings.py:97, inside load_settings())
```

All nine `test_settings.py` tests go RED, including every AC3 empty-string test — with
an `AttributeError`, a DIFFERENT failure class than AC4's `AssertionError` (a different
branch: "the value read does not exist" vs. "the value read is wrong").

**NARROWED 2026-08-13 after quality review (m1).** The "proves the tests pin the live
resolution" claim is scoped to `test_app_settings_dynamodb_defaults`. It does NOT
follow from this mutation for the five AC3 empty-string tests: `Settings.aws_region`
is evaluated EAGERLY as a default argument, so deleting the class attribute raises
`AttributeError` before any assertion runs — those five would go RED **regardless of
what they assert**, which is precisely a non-discriminating observation.
The property is nonetheless TRUE, and the quality reviewer proved it with the
mutation that DOES discriminate: flipping each field's fallback from
`os.environ.get(V, D)` to `os.environ.get(V) or D`, one field at a time, yields
`1 failed, 8 passed` five times over — each flip reds exactly its own field's test and
nothing else — and `5 failed, 4 passed` when all five are flipped together. THAT is
the evidence for the AC3 five; this AttributeError tail is the evidence for the
defaults test only.

Reverted; `git diff backend/src/composition/settings.py` empty; full relevant suite
(`test_settings.py`, `demo_loop_gate/test_harness_assertions.py`,
`test_zr3_duplicate_declarations.py`) confirmed green again, 29 passed, before moving
on.

### AC6 — `harness.py`'s STORY-203 comment corrected

`tools/demo_loop_gate/harness.py:755-771` (was `:755-761`): the "follows a future
rename automatically" sentence now states explicitly that this was true only of the
declared field default before STORY-218 — `load_settings()` never actually read it —
and is unconditionally true now that the field default is canonical and
`load_settings()` reads it back. Cites STORY-218/STORY-203 by number.

This edit shifted `Settings.dynamo_observations_table`/`dynamo_control_table`'s lines
in `harness.py` from `:763`/`:770` to `:773`/`:780`. Re-keyed in the same commit:
`backend/tests/test_zr3_duplicate_declarations.py`'s `_ADJUDICATED` entries at
`harness.py:928`/`:989` -> `:938`/`:999` (the sweep's own re-measured coordinates);
`settings.py`'s own AC1 docstring citation of the same `harness.py` lines.
`test_zr3_sweep_finds_no_unadjudicated_collision` /
`test_zr3_adjudications_are_still_current` both re-verified green after the re-key.

### AC7 — ZR-3 blind spot stated in the sweep's own docstring

`tools/zr3_duplicate_sweep.py`'s module docstring gained a "Structural blind spot"
paragraph: `collect_src_declarations`/`collect_tools_literals` compare `backend/src/`
against `tools/` only, so a `src`-internal duplicate (exactly this story's defect) is
invisible by construction; widening the sweep is out of scope; a `0` collision count
says nothing about `src`-internal duplication. No line-numbered citation elsewhere in
the wiki or test suite depends on this file's line numbers (checked: `grep -rn
"zr3_duplicate_sweep\.py:[0-9]" .` — the only hits are in `zone-rules-history.md`
(`tier: reference`, not swept) and story-file prose describing past states), so this
addition required no re-keying.

### AC8 — full DoD gate

Full 8/8 gate output recorded in the implementer's final report to the orchestrator
(this file does not duplicate the raw gate transcript, following STORY-220's
precedent).

### Wiki

`zone-rules.md` (`tier: map`) cites `settings.py:21-22` (now `:57-58`) at two Facts
(ZR-3's Statement and its Measurement note) and does not cite exact lines inside
`harness.py`'s blocklist block or inside `zr3_duplicate_sweep.py`, so those needed no
line-citation update. Both Facts were re-read and their line citations corrected to
the new `settings.py:57-58`, and the article was re-verified (touched) in the same
commit as this story's last code commit, per A18/the wiki-discipline checklist item.
`zone-rules-history.md` is `tier: reference` (no `code_refs`, exempt from the sweep and
from citation resolution per this sprint's plan) and was left untouched — its entries
are citations INTO history, not claims about HEAD.
