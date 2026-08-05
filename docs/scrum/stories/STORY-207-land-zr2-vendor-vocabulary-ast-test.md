---
id: STORY-207
title: Land ZR-2's guard — an AST test that vendor vocabulary never becomes an identifier inside core/
type: chore
points: 2
status: draft
filed: 2026-07-31
refined: 2026-08-05
sprint: 69
---

> **REFINED at sprint-69 planning (2026-08-05).** AC lifted from `docs/scrum/wiki/zone-rules.md`
> ZR-2's Coverage verdict and re-verified against HEAD. PROPOSAL until the PO approves the sprint.
> **Estimate confirmed at 2.**

## Context

Filed during sprint 66. **Authoritative detail:** `docs/scrum/wiki/zone-rules.md` ZR-2
(`:141-244`) — it names the exact AST node types, the two compliant prose forms, the `Provenance`
carve-out, and the residue.

The rule is a FORM distinction, not a word list: inside `core/`, a vendor name is compliant in
exactly three forms — a `#` comment, a formal docstring, and the attribute-docstring idiom (a bare
string-literal statement following a class-level field assignment, e.g.
`backend/src/core/domain/publication.py:66`) — and in no other, **except** as a value inside
`Provenance` (`backend/src/core/domain/signal.py:26-39`), the one field the domain itself
designates for vendor identifiers.

## Re-verification at HEAD (2026-08-05, planning)

A throwaway prototype of the exact walk ZR-2 specifies was run over `backend/src/core/`:
**31 modules scanned, 0 hits.** The tree is clean, confirming the guard will be green on arrival
and that AC5's mutation is the only possible red. The prototype also confirms the `Expr`-sole
`Constant` exclusion is what keeps the two prose forms compliant — without it,
`publication.py:66` and the six docstring citations ZR-2 adjudicates would all flag.

## Acceptance Criteria

- [ ] **AC1 — the walk covers the six node classes ZR-2 names, and no fewer.** A test parses every
      module under `backend/src/core/` (`domain`, `ports`, `services`, `queries`, and the package
      root `core/__init__.py` — 31 modules at HEAD) with `ast` and asserts no detection-seed token
      appears in: (1) `FunctionDef`/`AsyncFunctionDef`/`ClassDef` names; (2) `arg` names;
      (3) `Name` ids; (4) `Attribute.attr`; (5) `keyword.arg`; (6) `Constant` string/number values
      that are NOT the sole value of an `Expr` statement.
- [ ] **AC2 — both prose forms stay compliant, proven in the compliant direction too.** A test
      asserts the guard does NOT flag: a module/class/function docstring containing a vendor word,
      and the attribute-docstring idiom (`publication.py:66`'s shape). This is a real failure mode,
      not ceremony — an over-triggering guard would flag the six citations ZR-2 already adjudicated
      COMPLIANT and would be reverted rather than obeyed.
- [ ] **AC3 — the `Provenance` carve-out is NOT implemented, and the guard says so.** Corrected at
      plan verification: `Provenance(system="dynatrace")` written inside `core/` **would be flagged**
      by AC1's rule (6) — it is a `Constant` that is not the sole value of an `Expr`. That
      contradicts ZR-2, which calls the carve-out *"compliant BY DESIGN … not an exception carved
      out of it"* (`zone-rules.md:153-160`). The contradiction is moot today (`core/` holds no such
      literal, and the `Provenance` definition itself contains no vendor token, so a test asserting
      it is unflagged would be vacuous). **AC3 is therefore met by stating the residue, not by
      faking coverage:** the docstring records that the carve-out is unimplemented, that a future
      `Provenance(system="…")` literal inside `core/` will false-positive, and that the correct
      response then is a narrow exemption for `Constant` arguments to a `Provenance(...)` call —
      never deleting the domain's sanctioned channel to satisfy a guard. AC8 carries this into the
      row.
- [ ] **AC4 — the residue is stated in the guard's own docstring, and it is the TRUE residue.**
      Corrected at plan verification: ZR-2's stated residue is **false** for the six-rule walk AC1
      specifies. Both of its examples ARE caught — `def f(x: "DynatraceRow")` hits as
      `Constant 'DynatraceRow'`, and `getattr(obj, "dynatrace_" + suffix)` hits as
      `Constant 'dynatrace_'`. That text was written when the verification walk covered only
      names/`arg`/`Name` (`zone-rules.md:218-220`) and was carried into the six-rule verdict without
      re-derivation. **Do not copy it verbatim.** The true residue: the walk sees these only as
      string constants, never in their real form — so it cannot tell a forward-reference annotation
      from a comment-like string — and an identifier assembled from fragments carrying no seed token
      (`"dyna" + "trace_id"`) is invisible. `zone-rules.md`'s own ZR-2 residue paragraph is corrected
      in the same commit. **ZR-2 may not be described anywhere — row, docstring, or commit message —
      as fully enforced.**
- [ ] **AC5 — shown RED by mutation (A9).** Add `dynatrace_code: str` to a `core/domain` model;
      the test fails naming the file, the line and the node class; revert; the test passes and
      `git diff` is empty. Recorded verbatim in the board's `reality_gate` block.
- [ ] **AC6 — the word list is declared once, and declared a recall aid.** The detection seed
      (`Dynatrace`, `Grail`, `DQL`, `Statuspage`, `DynamoDB`, plus the `Dynamo*Repository` /
      `Statuspage*` class-name families, case-insensitive) lives in exactly one module-level
      constant with a comment stating it is explicitly NON-EXHAUSTIVE and that the RULE is the form
      distinction. It is not re-declared under `tools/` (ZR-3).
- [ ] **AC7 — runs inside the existing gate.** A `backend/tests/` test collected by the existing
      `python -m pytest` command. No ninth DoD command.
- [ ] **AC9 — non-vacuity floor.** The test asserts module discovery returned a non-empty set
      (≥ 25 modules), so a wrong root or a moved package goes RED instead of silently iterating over
      nothing and passing. **Do not hardcode 31** — STORY-206 AC6's own mutation adds a 32nd module,
      and STORY-220's adds another.
- [ ] **AC8 — the catalogue row flips honestly, in a shape STORY-216 can parse.** ZR-2's
      adjudication row moves from `GUARDABLE-DEFERRED (STORY-207)` to `ENFORCED-BY` with the test
      path as a backtick code span in the **Verdict** cell (`path.py::test_name` form). The Detail
      column records the AC5 mutation, the AC4 true residue, and the AC3 unimplemented carve-out —
      the row states the guard's extent, not more. `verified_sha` bumped in the same commit
      (A18 / C3).

## Not in scope

Widening the seed to future vendors (a new integration adds its own tokens; that does not change
the rule). Closing the residue — string annotations and dynamic identifiers stay unguarded, stated.
Anything outside `core/`: the same shape inside an adapter is compliant by design
(`adapters/outbound/statuspage/__init__.py:23`).
