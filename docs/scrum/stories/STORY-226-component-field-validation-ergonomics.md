---
id: STORY-226
title: ComponentConfig validation ergonomics — the error names a value the author never typed, and "" is legal for one field but not the other
type: defect
points: 2
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

- [ ] **AC1 (the error names the value the author actually typed)** — when a `group` fails the slug
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
- [ ] **AC2 (a test proves the authored value survives)** — a test asserts the message contains the
      pre-normalization string for a `group` that differs from its normalized form. Shown-RED
      against the current behaviour (today the message contains only the normalized value), so the
      test is known to fail before it passes.
- [ ] **AC3 (`description: ""` becomes `None` at load)** — a component declaring `description: ""`
      loads successfully and yields `description=None`, not `""`. Verified **through
      `load_config`**, not only on the model.
- [ ] **AC4 (`""` never reaches the API)** — `GET /api/v1/components` returns `"description": null`
      for a component whose config declared `description: ""`. Asserted at the HTTP boundary, so the
      guarantee holds for the operator cockpit, which is the consumer this ruling was made for.
      ⚠ STORY-147's own HTTP tests use `FakeComponentRepository`; that is fine for this AC, but it
      means the fake-repo seam is where this is proven — say so rather than implying end-to-end.
- [ ] **AC5 (whitespace-only is decided, not left to chance)** — `description: "   "` must behave
      the same as `""` (strip, then treat as empty) or explicitly not. State which and test it. The
      PO ruled on `""`; whitespace-only is the adjacent case a config author will actually hit, and
      leaving it undecided reintroduces the same two-representations problem this story closes.
- [ ] **AC6 (`group: ""` is UNCHANGED, and the reason is recorded)** — `group: ""` continues to
      raise. **Assumption stated rather than silently taken:** the PO's ruling was scoped to
      `description`, and `group` is a slug identifier used for grouping — an empty slug is
      meaningless, so an error is the right signal, whereas an empty description simply means "none
      given". After this story **neither field can carry `""` into the DTO**, so the asymmetry the
      PO objected to is gone at the boundary that mattered. A regression test pins that `group: ""`
      still errors, so this is a decision, not a gap.
- [ ] **AC7 (gate)** — the DoD commands the diff can affect exit 0 at the final HEAD, counts
      recorded. Run the wiki sweep after the last commit and take what it returns.

## Estimate: 2

Both changes live in one file (`backend/src/composition/config.py`) with tests beside them. AC1's
"carry the authored value to the raise site" is the only non-trivial mechanical part, and STORY-147
already established exactly where that check must live.

## Not in scope

`group`'s slug rule itself, which STORY-147 established and the PO accepted at the sprint-73 review
(see AC6 for the one deliberate consequence).
