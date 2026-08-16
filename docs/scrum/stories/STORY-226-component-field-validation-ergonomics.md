---
id: STORY-226
title: ComponentConfig validation ergonomics — the error names a value the author never typed, and "" is legal for one field but not the other
type: defect
points: null
status: draft
refined: null
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

## Open Questions — THE PO MUST ANSWER BEFORE THIS IS ESTIMATED

1. **Item 1:** show the authored value only, or authored + normalized?
2. **Item 2:** which way should the asymmetry resolve?
   - reject `description: ""` (symmetric with `group`, strictest, may break an existing config), or
   - normalize `description: ""` → `None` at load (lenient, one representation of "nothing"), or
   - leave it and make the UI special-case it (zero backend change, cost moves to the frontend).

## Acceptance Criteria

*(Not written — this story is `draft` and cannot be refined until the Open Questions are answered.
Writing AC now would encode a guess at the PO's intent as a contract, which is the failure the
Definition of Ready exists to prevent.)*

## Not in scope

Anything about `group`'s slug rule itself, which STORY-147 established and the PO accepted.
