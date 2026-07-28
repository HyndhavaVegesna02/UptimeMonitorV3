# Sprint 61 — ABORTED (PO directive, 2026-07-28)

## Reason

The PO rejected the operator-cockpit UI itself — not any individual story's
execution: *"i dont like this ui also"*. This is the **third rejected UI
direction** (see `docs/scrum/wiki/` history and the two prior rejections
2026-07-19 / 2026-07-21, plus the sprint-60 external-delivery rejection
2026-07-25).

Sprint 61's goal — *harden and refine the operator cockpit delivered in
sprints 59–60* — is therefore moot: the thing being hardened is being
replaced. Per the abort protocol, the PO chose **option 3: keep all work
unmerged**. `main` is untouched; the `sprint-61` branch stays for reference.

## Disposition

- **Branch:** `sprint-61` (tip `56b7fc8`), left unmerged. Not deleted.
- **`main`:** untouched — no sprint-59/60/61 frontend work has ever merged.
- **Velocity:** records **0 points** for sprint 61 (nothing merged).
- **Stories:** all sprint-61 stories return to the backlog as `superseded`
  rather than `ready` — they describe defects in a UI that no longer has a
  future. They are NOT re-estimated for a future sprint.

## Board state at abort

| Story | Title (short) | Points | Status at abort |
| ----- | ------------- | ------ | --------------- |
| STORY-136 | Dashboard/shell correctness hardening | 3 | done (unmerged) |
| STORY-137 | Shared fetch dedup/cache | 3 | done (unmerged) |
| STORY-138 | Dashboard layout coherence | 5 | done (unmerged) |
| STORY-139 | see plan.md | — | done (unmerged) |
| STORY-140 | see plan.md | — | done (unmerged) |
| STORY-141 | see plan.md | — | done (unmerged) |
| STORY-142 | Styled datetime-local fields | — | done (unmerged) |
| STORY-143 | ComponentAvailabilityPage (last) | — | **in progress**, abandoned at step 2 (`c8c2f62`) |

STORY-143 was mid-TDD (steps 1–2 committed, green). It is abandoned in place,
not completed — the page it adds belongs to the rejected shell.

## What replaces it

The PO has built a **new UI inspiration app with full mock data** at
`C:\Hyn\new ui\ops-pulse-react` (a Vite + React 19 + Tailwind v4 clone of the
`ops-pulse-6.preview.emergentagent.com` prototype, running on `localhost:5173`).
The next planning cycle scopes **adapting the existing backend to that new
frontend** — see the sprint-62 planning artefacts.

## Retro input (mandatory)

The abort reason is mandatory retro material. The standing question this raises
is process-level, not story-level:

> Three UI directions have now been rejected *after* being built. Every one
> passed its own AC, its own DoD gate, and its own reality gate — the
> mechanical floor held perfectly and still produced three rejections. The
> gates verify *conformance to the AC we wrote*; nothing in the loop verified
> **the PO wants this look** before a sprint's worth of work existed.

Candidate amendment (to route down the enforcement ladder at retro): a
**visual-direction gate before any UI sprint locks** — the PO signs off on a
static, throwaway visual reference (a screenshot, a prototype page, an existing
app) and that reference becomes the binding spec artefact, the way
`uptime-monitor-v3-design.html` is binding for the backend. Sprint 62 is in fact
the first sprint where such an artefact exists up front (the PO built it
themselves), which is the natural pilot.
