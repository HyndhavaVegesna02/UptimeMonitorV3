# Sprint 39 Retro — debug sprint

**Outcome:** 1 story (STORY-071), 2/2 pts accepted, one clean fix via systematic debugging (root
cause found before any fix — no thrashing). Merged to `main`.

## What went well
- Systematic debugging pinned the root cause from the backend log + one `git`/`grep` trace, no
  guess-and-check. The DB-gated regression test reproduced the EXACT `CheckViolation` before the fix
  and passed after — verification by reproduction, not assertion.
- The live review walkthrough (Sprint 38) is what surfaced this latent bug in the first place — the
  "run it live at review" discipline (2026-07-04 agreement) earning its keep a third time.

## Root-cause class (the real lesson)
This was a **fake/adapter-parity** miss (the 2026-06-26 agreement): the in-memory fake
`record_approval_event` stored any string, so `action='approve'` passed every fake-backed test; only
real Postgres enforces `ck_approval_events_action`. The existing agreement already covers "fake and
adapter must agree on edge behavior" — the gap was that a **DB CHECK-constraint on an enum-like text
column** is exactly such an edge the fake cannot model, and no DB-gated test wrote the real value
through it. The fix added that test.

## Amendment decision
No NEW working-agreement proposed: the 2026-06-26 fake/adapter-parity agreement already governs this
class; the corrective action is to APPLY it to constraint-backed columns (write each allowed value —
and prove a wrong one is rejected — through a DB-gated test, since the fake can't). Noted here as
reinforcement. (If the PO later wants this sharpened into an explicit "every CHECK/enum column gets a
DB-gated allowed-and-rejected-value test" agreement, that's a one-line add — surfaced at review, PO
chose to leave the existing agreement as the governing rule.)

## Follow-ups
None new. STORY-070 (vendor-id drift health check) remains the standing preventive item from the
Sprint 38 hotfix.
