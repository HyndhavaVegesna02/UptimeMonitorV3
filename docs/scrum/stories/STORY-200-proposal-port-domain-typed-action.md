---
id: STORY-200
title: Give ProposalRepository.record_approval_event a domain-typed action parameter (subsumes STORY-198)
type: defect
points: 3
status: ready
refined: 2026-07-31
re_refined: 2026-08-02
subsumes: STORY-198
---

## Context

Filed from the sprint-66 audit's quality-review fix round (STORY-195,
`docs/scrum/sprints/2026-07-31-sprint-66/audit-core-adapters.md` §2b/§3). An independent re-audit
found that STORY-195's original pass adjudicated a hardcoded-literal comparison in
`DynamoProposalRepository.record_approval_event` (`GAP-1`, filed as `STORY-198`) as an unscored
"catalogue gap" while separately verdicting `core/ports/proposal_repository.py` `CLEAN` — having
quoted the very port line (`action: str`) that is the ROOT CAUSE, without recognizing it as one.
This is now catalogued as `ZR-6` in `docs/scrum/wiki/zone-rules.md`.

## Description

`backend/src/core/ports/proposal_repository.py:45` (`action: str`, in `record_approval_event`'s
abstract signature) stands in for `ProposalState` even though `ProposalState` is imported in the SAME
file (`:6`) and used correctly, as the domain type, by the sibling method thirteen lines above:
`:32` (`to_state: ProposalState`, in `resolve`'s signature). The adapter implementing this port,
`backend/src/adapters/persistence/dynamo_proposal_repository.py:286` (`if action == "approved":`),
then compares the resulting bare string against a hardcoded literal rather than an enum member — the
exact shape a correctly-typed port signature would make structurally awkward to get wrong.

**Blast radius, which is why this is a defect and not hygiene.** That literal is the branch that
writes `approved_actor` (`dynamo_proposal_repository.py:292`, `"UpdateExpression": "SET
approved_actor = :actor"`), and `approved_actor` is the *sole* source of `Publication.author`
(`dynamo_publication_repository.py:94-96`). If `ProposalState.APPROVED`'s value ever drifts from the
literal `"approved"`, the author column silently blanks for every row on the Publications tab. It
does not raise.

## The design decision, settled at refinement (was the Open Question)

The filing left a genuine choice open: `action`'s legal set is a 2-member subset
(`APPROVED`/`REJECTED`) of `ProposalState`'s 5 members, so the port could take either **(a)**
`ProposalState` directly or **(b)** a narrower purpose-built 2-member type.

**Decision: (a) `ProposalState`.** Three reasons, in order of weight:

1. **The sibling method in the same port already takes `ProposalState` for the same two values.**
   `resolve(..., to_state: ProposalState)` at `:32` and `record_approval_event(..., action)` at `:45`
   describe one transition from two angles. ZR-6 asks that a port express its parameters in domain
   types; expressing this one in a *different* domain type from its sibling would satisfy the letter
   of ZR-6 while introducing a fresh inconsistency in the same eight lines of interface.
2. **Option (b) buys type precision with a duplicated declaration.** A separate `ApprovalAction`
   enum needs a mapping back to `ProposalState` (the caller has a `ProposalState` in hand —
   `approval.py:62`/`:85` — and the stored value must stay `"approved"`/`"rejected"`). That mapping
   is a second declaration of the approved/rejected vocabulary, which is exactly the ZR-3/ZR-8
   duplicated-declaration class this sprint exists to remove. Trading a typing weakness for a
   duplication weakness is not progress.
3. **The "3 invalid members" objection is answerable without a new type, and testably** — see AC3.
   It is a contract question, not a type-system question, and the caller funnel is already a single
   method (`_decide`).

**Recorded so a later story does not silently re-open it:** if a future change gives `action` a
legal set that is *no longer* a subset of `ProposalState` (e.g. an `ESCALATED` action with no
corresponding proposal state), decision (a) expires and (b) becomes correct. That is the trigger to
revisit, not general dissatisfaction with 3 unused members.

## Relationship to STORY-198 — this story SUBSUMES it

**STORY-198 has NOT landed.** The previous revision of this file asserted it was "already landed"
and reasoned about reconciling with its `.value`-based comparison; that was wrong, and re-verified
wrong at HEAD (`86459ea`) — `dynamo_proposal_repository.py:286` still reads `if action ==
"approved":`, and STORY-198 is `status: draft`, `sprint: null` in the backlog.

Because it has not landed, the two stories must not both run: STORY-198 changes the literal to
`ProposalState.APPROVED.value`, and this story then changes the same three lines again to drop
`.value` entirely. Doing the port fix alone reaches the better end state in one edit. **STORY-198 is
therefore marked `superseded-by: STORY-200`**, and its content — the defect, the blast radius, and
its test trap — is folded into the AC below.

## Acceptance Criteria

- [x] **AC1** — `ProposalRepository.record_approval_event`'s abstract signature types `action` as
      `ProposalState`, not `str` (`backend/src/core/ports/proposal_repository.py:45`). Its docstring
      states the contract that only `APPROVED` and `REJECTED` are legal, and why.
- [x] **AC2** — `core/services/approval.py:128` passes `to_state` directly instead of
      `to_state.value`; no caller converts to a string at the call site.
- [x] **AC3** — The 2-member contract leaves a testable trace rather than a comment: passing a
      `ProposalState` outside `{APPROVED, REJECTED}` to the recording path raises a named error,
      proven by a test. **The guard lives in the core service (`approval.py`'s `_decide`), not in the
      adapter** — it is a domain-contract rule, and putting it in the adapter would both misplace it
      and leave the fake non-conforming.

      **Do not treat `is_valid_transition` as partial cover — it does not constrain this set.**
      `core/domain/proposal.py:105-107` admits any non-`OPEN` target, so
      `is_valid_transition(OPEN, SUPERSEDED)` returns `True`. AC3 is entirely new validation.
- [x] **AC4** — `DynamoProposalRepository.record_approval_event` compares by enum identity
      (`action is ProposalState.APPROVED`), not against a string literal. The **STORY-198 defect is
      gone**: no `"approved"` literal remains in that method.

      **The persisted bytes stay identical ONLY if `.value` is used explicitly at both write sites,
      and this is the trap in the story.** `ProposalState` is `class ProposalState(str, Enum)`
      (`core/domain/proposal.py:24`) — a str *mixin*, **not** `StrEnum` — so on Python 3.13
      `Enum.__format__` defers to `Enum.__str__`. Measured at planning:

      ```
      f'EVENT#TS#{ProposalState.APPROVED}'        -> 'EVENT#TS#ProposalState.APPROVED'
      f'EVENT#TS#{ProposalState.APPROVED.value}'  -> 'EVENT#TS#approved'
      ```

      So AC4 **requires `action.value` explicitly at both**:
      - `dynamo_proposal_repository.py:265` — the `sk` f-string (`EVENT#<occurred_at>#<action>`).
        Passing the bare member here silently corrupts every event sort key.
      - `dynamo_proposal_repository.py:268` — the `"action"` item attribute. This one *happens* to
        survive as a str subclass, but that is luck rather than design; pin it.
- [x] **AC5** — **The test trap is honoured.** `backend/tests/fakes.py:175-183`'s
      `record_approval_event` only appends a dict — it does NOT implement the `approved_actor`
      denormalization — so the branch this story fixes is **unobservable through the fake**. The
      proving test for AC4 therefore runs against DynamoDB Local, asserts `approved_actor` is
      written on approve and NOT written on reject, and a fake-based test may not be substituted for
      it. (A fake-based test here would assert nothing while looking green.)
- [x] **AC6** — End-to-end blast-radius check: an approve still populates `Publication.author`
      through `dynamo_publication_repository.py:94-96`, asserted against a non-empty author.
- [x] **AC7** — Mutation proof: change `ProposalState.APPROVED`'s *value* (not its name) in
      `core/domain/proposal.py:28`, confirm the AC5 test goes RED, restore and confirm `git diff` is
      empty. This is the specific drift the story exists to make impossible to miss — if nothing goes
      red, the coupling is still unpinned and the story is not done.
- [x] **AC9** — `FakeProposalRepository.record_approval_event` (`backend/tests/fakes.py:175-183`)
      declares `action: ProposalState`, matching the port. The 2026-06-26 fake/adapter parity
      agreement means the fake may not keep a signature the port has abandoned — and AC5 cites this
      file only as a trap, so without this AC nothing updates it.
- [x] **AC8** — The full DoD gate is green, and existing contract tests pass **except the two that
      must change**, named here rather than discovered during implementation:

      - `backend/tests/test_dynamo_proposal_repository.py:193` — passes `action="approved"`, then
        asserts `approved_actor == "ops-admin"` at `:217`.
      - `backend/tests/test_dynamo_publication_repository.py:79` — passes `action="approved"`,
        feeding the `Publication.author` assertion.

      Both hit the real adapter, and `"approved" is ProposalState.APPROVED` is **`False`** (measured),
      so under AC4's identity comparison the branch stops firing and both go RED. **They must be
      updated to pass `ProposalState.APPROVED`** — that is in scope, not a regression.

      The fake-backed tests (`test_approval.py:60`, `test_core_ports.py:269`, `test_decisions.py:82`)
      compare with `==` and survive the str mixin unchanged.

## Re-derive the citations before you start — this story's line numbers WILL have moved

**STORY-199 runs before this story (sprint order 2 vs 4) and edits the same file.** It adds a
`LastEvaluatedKey` loop to `list_open` at `dynamo_proposal_repository.py:174`, which shifts
everything below it. Every citation in this file below that line — `:265`, `:268`, `:286`, `:292` —
is stated against `1e60172` and will be stale by the time this story is implemented.

Re-derive them first (`grep -n "action ==\|approved_actor\|EVENT#" ` on the file). Flag and report
the new numbers rather than silently substituting them, per the standing re-derivation rule. This
note exists because the sprint plan made a point of "every citation re-derived, none had drifted"
while scheduling the drift it was about to cause.

## Open Questions

None. The (a)/(b) design question is settled above with its expiry condition recorded.

## History

- 2026-07-31: filed from STORY-195's quality-review fix round finding (`ZR-6`,
  `docs/scrum/sprints/2026-07-31-sprint-66/audit-core-adapters.md` §2b/§3/§6).
- 2026-08-02: refined to `ready` at sprint-67 planning; **re-pointed 2 -> 3** for the absorbed
  STORY-198 scope and the real-DynamoDB proving test. Citations re-derived against HEAD (`86459ea`)
  and all hold: port `action: str` :45, `to_state: ProposalState` :32, `ProposalState` import :6,
  adapter literal :286, `ProposalState.APPROVED = "approved"` `core/domain/proposal.py:28`,
  `action=to_state.value` `approval.py:128`. Two corrections to the previous revision: the sibling
  method is thirteen lines above, not four; and STORY-198 has **not** landed, so this story subsumes
  it rather than reconciling with it.
