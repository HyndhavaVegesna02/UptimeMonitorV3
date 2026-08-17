---
id: STORY-226
title: ComponentConfig validation ergonomics — the error names a value the author never typed, and "" is legal for one field but not the other
type: defect
points: 3          # RE-PRICED 2 -> 3 at pre-lock verification: composition/config.py is a
                   # code_ref of config-layer.md (tier: map / status: verified), which A18 forces
                   # re-verified IN-STORY. The 2 priced that at zero -- sprint 73's exact habit.
status: ready
refined: 2026-08-16   # sprint-74 refinement, AFTER the PO answered both Open Questions
sprint: null
---

## Where this came from

Filed at the **sprint-73 review** on PO instruction ("file for fixing the minors"). Both items are
quality-review findings against **STORY-147**, deliberately not fixed mid-sprint because they are
**product decisions, not defects in the delivered work** — the reviewer flagged behaviour that is
working as written, where "as written" may not be what we want.

This story needs a PO answer on the intended behaviour before it can be estimated.

## Item 1 — the validation error quotes the NORMALIZED group

`backend/src/composition/config.py:756-762` raises `InvalidComponentFieldError` naming the component
and field, and quotes `comp.group` — which STORY-147's AC2 has **already lowercased at construction**
(`config.py:249-256`, `field_validator("group", mode="after")`).

So an author who wrote `group: "Not Valid!"` in their YAML is shown `not valid!` in the error. The
message is not *wrong* — the AC's "after normalization" wording keeps it honest — but the author
**cannot grep their own config for the string the error shows them**, which is the one thing an
error message exists to enable.

The fix is to echo the authored value. The open question is whether to show both (`"Not Valid!"
normalized to "not valid!"`), which is more informative and more verbose.

## Item 2 — `description: ""` is accepted, `group: ""` is rejected

Measured at sprint-73 review:

- `group: ""` fails the slug regex → `InvalidComponentFieldError`.
- `description: ""` passes (`len("") == 0 <= 80`) and reaches `ComponentDTO` as `""`.

So the API can return `{"group": null, "description": ""}` — two different representations of
"nothing", one per field, on the same object. **STORY-147's AC3 is not violated**: that clause is
about *absence* yielding `null`, and absence does yield `null` for both. This is about an author
explicitly writing an empty string.

The cost lands on the consumer: the operator cockpit must special-case `""` separately from `null`
for description but not for group, or it renders an empty label.

## PO rulings — both answered at sprint-74 refinement, 2026-08-16

1. **Item 1 → show BOTH the authored and the normalized value.**
2. **Item 2 → normalize `description: ""` to `None` at load.** One representation of "nothing"
   reaches the DTO; the UI checks only for `null`.

## Acceptance Criteria

- [x] **AC1 (the error names the value the author actually typed)** — when a `group` fails the slug
      rule, `InvalidComponentFieldError`'s message contains **the authored string AND the normalized
      one**, per the PO ruling. Given `group: "Not Valid!"`, the message contains both `Not Valid!`
      and `not valid!`.
      ⚠ **The authored value is not currently available where the error is raised.**
      `config.py:249-256`'s `field_validator("group", mode="after")` lowercases at *construction*, so
      by the time `load_config` (`:756-762`) raises, `comp.group` is already normalized. The
      implementer must carry the original through — and **the check must stay in `load_config`,
      outside the `try/except`**. STORY-147's story file documents why at length: a `ValueError`
      subclass raised inside a pydantic validator becomes a `ValidationError` and is re-raised bare,
      losing the subclass. **Do not move the check into the validator to get easy access to the raw
      value.** That is the trap that nearly shipped twice in STORY-147.
      ✅ **AC1 IS satisfiable without the validator, and pre-lock verification found the mechanism —
      use it rather than reaching for a private field on a `frozen=True` model:** the parsed YAML is
      assigned to `raw` at `config.py:669-671` and **is still in scope at the `:755` raise site**, so
      `raw["components"]` carries the authored `group` verbatim. `_derive_signals_from_monitors`
      (`:386-438`) neither reorders nor drops components, so `app.components` aligns with it — but
      **join on `comp.id`** (never normalized), not on list position, which is the robust key.
- [x] **AC2 (a test proves the authored value survives)** — a test asserts the message contains the
      pre-normalization string for a `group` that differs from its normalized form. Shown-RED
      against the current behaviour (today the message contains only the normalized value), so the
      test is known to fail before it passes.
- [x] **AC3 (`description: ""` becomes `None` at load)** — a component declaring `description: ""`
      loads successfully and yields `description=None`, not `""`. Verified **through
      `load_config`**, not only on the model.
- [x] **AC4 (the HTTP layer is shown to be a PASSTHROUGH — it is not where this is proven)** —
      ⚠ **The draft AC4 was UNSATISFIABLE-OR-THEATRE and is replaced.** Pre-lock verification showed
      `api/v1/components/service.py:22-29` is an unconditional passthrough
      (`ComponentDTO(..., description=c.description)`), and `FakeComponentRepository` is seeded with
      hand-built `Component` objects — `load_config` is never invoked at that seam. So "a component
      whose config declared `description: \"\"`" **cannot exist** there. Both readings failed: seed
      the fake with `None` and the test passes identically before and after AC3, unable to fail if
      AC3 regresses (theatre); seed it with `""` and the only way to green it is to normalize in the
      service or DTO, which **contradicts AC3 and the PO's ruling** that normalization happens at
      load.
      **What this AC now requires:** state, citing `service.py:28`, that the HTTP layer performs no
      normalization and therefore returns whatever the load seam produced — so AC3 is the guarantee
      and the API inherits it. Do **not** add a normalization step downstream to satisfy a test.
      *(If the PO wants the full chain proven end-to-end — `load_config` → `seed_topology_dynamo` →
      `DynamoComponentRepository` → endpoint, `dynamo_local`-gated — that is a real cost on a small
      story and should be its own AC with its own points, not smuggled in here.)*
- [x] **AC5 (whitespace-only is decided, and the rule is stated AS CODE)** — `description: "   "`
      must behave the same as `""`. ⚠ **"Strip, then treat as empty" is ambiguous in a way that moves
      a pinned boundary**, so state which rule you implement:
      `None if not v.strip() else v` — leaves non-empty values **untouched**, or
      `v.strip() or None` — strips **every** value.
      The second changes which side of `_MAX_DESCRIPTION_LENGTH` (`config.py:47`) a padded value
      lands on, and `backend/tests/test_config.py:953` pins an exactly-80-character description as
      valid. **Recommended: `None if not v.strip() else v`**, which closes the empty case without
      touching the length boundary STORY-147 established.
- [x] **AC6 (`group: ""` is UNCHANGED, and the reason is recorded)** — `group: ""` continues to
      raise. **Assumption stated rather than silently taken:** the PO's ruling was scoped to
      `description`, and `group` is a slug identifier used for grouping — an empty slug is
      meaningless, so an error is the right signal, whereas an empty description simply means "none
      given". After this story **neither field can carry `""` into the DTO**, so the asymmetry the
      PO objected to is gone at the boundary that mattered. A regression test pins that `group: ""`
      still errors, so this is a decision, not a gap.
- [x] **AC7 (gate)** — the DoD commands the diff can affect exit 0 at the final HEAD, counts
      recorded. Run the wiki sweep after the last commit and take what it returns.

## Estimate: 3 (re-priced from 2 at pre-lock verification)

Both code changes live in one file (`backend/src/composition/config.py`) with tests beside them, and
AC1's "carry the authored value to the raise site" is the only non-trivial mechanical part — the
verifier found the mechanism (`raw` at `:669-671`), so it is bounded.

**The +1 is wiki cost that the 2 priced at zero.** `composition/config.py` is a `code_ref` of
`config-layer.md`, which is `tier: map` / `status: verified` — so this diff stales it, and A18 plus
`.scrum/definition-of-done.md:133-136` force it updated or explicitly re-verified **in-story**. That
is the same asymmetry sprint 73's retro praised catching when STORY-155b went 5 → 7.

## Not in scope

`group`'s slug rule itself, which STORY-147 established and the PO accepted at the sprint-73 review
(see AC6 for the one deliberate consequence).
