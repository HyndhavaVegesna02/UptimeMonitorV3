---
title: Frontend zone — why the operator-cockpit SPA is shaped as it is (reference tier)
tier: reference
verified_sprint: sprint-63
archived_reason: >-
  Demoted from tier: map / status: stale to tier: reference on 2026-08-17 (STORY-229). NOT a
  tombstone in the deployment-and-infra.md sense — frontend/ is live, running code, gated every
  story by the three frontend DoD commands (npm test / npm run build / npm run lint, CLAUDE.md).
  What ended is the Fact-by-Fact tracking, not the code. Two measurements drove the call: (1) this
  article sat `status: stale` since 2026-08-12 — quarantined, correctly, per the wiki protocol's
  designed safe state — and no story needed it across four-plus months of sprints (STORY-229
  refinement); (2) the PO's 2026-08-13 UI-rewrite directive archived all further frontend UI work
  ("a working six-tab SPA already lives on main"; see the equilibrium/UI-rewrite memory notes),
  removing the ongoing churn a `tier: map` article exists to track. At 634 lines and 67
  `code_refs` this was the single most expensive shape in the wiki, and rehabilitating it to
  `tier: map` (the default a careless AC1 reading would take) would have resumed paying that cost
  every sprint against four months of zero demonstrated demand. STORY-155a/155b had already made
  three of its `code_refs` dead (`SampleModeBanner.tsx`, `useSampleMode.ts`, the sample-mode MSW
  handler) and it still documented a `putJson` helper deleted with the feature — the quarantine
  was correctly protecting readers from those, not merely administrative. The routing philosophy
  this follows (`.scrum/checklists/implementer.md`'s wiki-discipline items): a *reason* article
  costs nothing every sprint; a map article is the one tier that does, and only what is left after
  routing through test/lint → CLAUDE.md → reference article earns one. What is below is the
  durable "why"; the file-by-file "what" this article used to carry is fully recoverable from git
  history at any commit before this one, or from reading `frontend/src/` itself, which — unlike
  this article ever was — cannot go stale.
# tier: reference (2026-08-17, STORY-229). code_refs and the `## Facts` heading are removed per
# the reference tier's integrity rule (yt_wiki.py::check_integrity) -- a reference article makes
# no live-code claims, so it carries nothing that can rot and is never swept. Filenames mentioned
# in prose below are bare (no line numbers) navigation, per the deployment-and-infra.md precedent
# -- never a checkable claim. See History for the full accounting of this conversion.
---

This article no longer tracks frontend/'s current shape. It records *why* the frontend zone is
built the way it is — decisions and rationale that don't rot when a file moves — for whoever next
works in `frontend/`. For what the code does today, read the code, `frontend/README.md`, or
CLAUDE.md's "The frontend zone" section, all of which are either live-code themselves or actively
maintained; none of the three needs a wiki sweep to stay true.

## Why frontend/ is isolated from the backend (dossier §17)
The operator-cockpit SPA and the public Statuspage are the design's two deliberately separate
surfaces — this article is about the former. `frontend/` was built with no import of backend
source and no shared build step: a separate Vite + React + TypeScript toolchain, its own three-
command DoD gate, talking to the backend only over `/api/*` HTTP. That isolation is why no CORS
middleware was ever needed — dev goes through the Vite proxy, production is same-origin behind
CloudFront — a decision stated directly in CLAUDE.md now, after an earlier docstring pointed at an
archived story that was never actually about CORS (STORY-181 corrected that drift once, which is
itself a small case study in why a reason belongs in one place, not restated per-file).

## Why the design direction changed twice
The first frontend attempt (sprints 23–24) was built to a since-removed `DESIGN-airtable.md` and
fully reverted (`521764c`) — nothing in the current tree descends from it. The second attempt
(sprint-25 onward, the one still live) was guided by `DESIGN-linear.app.md`; sprint-38 retuned its
palette/type-scale values to an imported *Operator Dashboard* mock while keeping that shape; and
sprint-62 planning replaced the design source outright with a PO-built UI reference
(`C:\Hyn\new ui\ops-pulse-react`, visual-only, no data layer), captured in-repo at
`docs/scrum/sprints/2026-07-28-sprint-62/`. `DESIGN-linear.app.md` stays on disk as lineage — the
shell's layout DNA traces to it and sprint history cites it — but it stopped being live guidance
two generations ago. The pattern worth remembering: a design *reference* rots the moment a newer
one is chosen, and only a human re-reading catches that a stale pointer survived the switch — this
article's own sprint-62 History entry (see below) is the same class of correction, caught late.

## Why the toolchain choices
Vitest + React Testing Library + jsdom + MSW, not a heavier E2E stack (Playwright was deliberately
deferred): RTL's accessible-role queries push every component toward a real accessible name, and
MSW as the *only* mocked edge means a test drives real component/hook behavior against a faked
network boundary rather than mocking application code directly. ESLint's flat config and Node 24 /
npm 11 are unremarkable toolchain facts, not decisions worth a reason article — see
`frontend/package.json`/`frontend/eslint.config.js` directly, which cannot lie about their own
content the way a paraphrase can. Fonts are self-hosted (`@fontsource/geist` +
`@fontsource/geist-mono`) specifically to avoid a runtime Google-CDN `<link>` — a reliability/
privacy choice, not a styling one.

## Why the shell is structured the way it is
Two decisions worth carrying forward even without file specifics:
- **One source of truth for navigation.** The six tabs are defined once and consumed by both the
  sidebar and the router, specifically so the two could never drift apart — a duplication that
  would otherwise be trivial to introduce one tab at a time across separate stories.
- **The accessible name is set explicitly, never left to visible text.** Collapsing the sidebar to
  icon-only must not change what a screen reader announces — this was a deliberate, tested
  invariant, not an accident of the collapsed markup happening to still contain text.
- **Graceful degradation over fabrication, everywhere.** A failed or loading secondary fetch
  (maintenance windows, per-component uptime, an approvals badge) degrades to "no badge" / "no
  bar" / "no count" — never a stale or invented value standing in. This shows up repeatedly across
  every tab and is the frontend's version of the backend's "no persisted verdicts" discipline.

## Why the API client centralizes error handling
Every client call funnels through one `readOkJson` helper so there is exactly one `ApiError`
shape (network failure, non-2xx with a readable `.status`, or a malformed 2xx body) — the reason a
mutating tab can branch on 404/409 without re-deriving what "failure" means per endpoint. The
later addition of a best-effort `.detail` parse (a non-2xx body's `{"detail": "..."}` string) was
built as purely additive to that contract for exactly this reason: no caller that already checked
`.status` could break. The actor seam (`getActor()`) is a single, deliberately fake swap-point for
identity — every decision POST reads the actor from there and nowhere else — so that whenever real
auth lands, it is a one-function change, not a grep-and-replace across every mutating tab.

## Why there are two health-status mappers, not one
The backend exposes two *different* vocabularies that happen to share exactly one string:
`ComponentStatus` (operational/degraded/partial_outage/major_outage, no "up" value) and an
observation's own health (up/down/degraded). Folding them into one mapper was tried in thought and
rejected — a `ComponentStatus` mapper handed an observation's `"up"` would silently mis-map it to
"unknown," and the fix does not compose backward. Keeping two small, obviously-named mappers means
a future contract change to either vocabulary can never quietly ripple into the tab that doesn't
use it.

## Why `useFetch` is the one fetch primitive
An early retro (sprint-26) flagged a risk that every read tab would reinvent its own
loading/error/success state machine. The fix was a single shared hook every tab's read fetching
funnels through, later proven to generalize to parameterized fetches (a window selector, a
compound topology+range key) with zero changes to the hook itself — evidence the original
abstraction was drawn at the right seam. Its one sharp edge, worth carrying forward: the fetcher
function passed in must be a stable reference, or the effect refetches every render.

## Why fields the wire doesn't expose are omitted, never invented
Every one of the six tab rebuilds hit fields a mock or a design reference implied but the backend
did not yet provide (an approval's detected-ago, a publication's author, a maintenance window's
delete control). The standing convention was to omit the field and file an explicit follow-up
story, never to fabricate a plausible-looking value — the same "fixtures derive from a real
captured sample" discipline the backend testing checklist states, applied to what a UI is allowed
to *display*, not just what a test is allowed to *assert*.

## Sample mode (removed — historical pointer only)
A shell-level "force every observation DOWN" trigger existed from STORY-049 through STORY-155a/b
as a deliberately TEMPORARY stand-in for the Dynatrace demo engine's real degrade→approve→publish
loop. It was fully removed (frontend half in STORY-155a, backend half in STORY-155b) once the demo
engine proved the same loop with real, unmodified ingest. Nothing in `frontend/src/` implements it
today; the full account of what it was and why removability was designed in from day one lives at
[[sample-mode]], not here.

## History
- sprint-25 (STORY-015a): created, as `tier: map`, tracking the sprint-25 shell built to
  `DESIGN-linear.app.md`.
- sprint-26 through sprint-45: rebuilt/extended across every tab (STORY-015b through 015g,
  STORY-041/046/049/052/055/056/072 and others) and re-verified Fact-by-Fact at each landing —
  full entry-by-entry detail for this span is in git history for this file, any commit before
  this one.
- sprint-38 (Wave 2 of the Operator Dashboard redesign): the widest single re-verification in this
  article's life — all six tabs recompiled onto the new design system in one sprint-close pass.
- sprint-62 (PO-directed docs correction, no code change): corrected two Facts that had gone wrong
  with no code moving — a wrong backend-DoD-command count, and `DESIGN-linear.app.md` still stated
  as current guidance two design generations after it stopped being one. Recorded here as the
  clearest example of why a *reason* article (this one, now) survives that failure mode better
  than a Fact ever could: "the design reference changed" does not go stale the way "the design
  reference is X" does.
- 2026-08-12: demoted `status: stale` (not flagged by the sweep — the tier pass touched every
  article's frontmatter, and touching a `verified` article claims its Facts were re-read, so an
  article nobody had re-read was marked stale instead of laundered clean).
- sprint-73 (STORY-155a/b): the frontend half of sample mode removed, orphaning three of this
  article's `code_refs` (`SampleModeBanner.tsx`, `useSampleMode.ts`, the sample-mode MSW handler)
  and leaving a `putJson` claim describing a helper deleted with the feature — while the article
  stayed quarantined and unread.
- 2026-08-17 (STORY-229): measured at refinement — 634 lines, 67 `code_refs` (3 confirmed dead),
  58 distinct path-shaped Fact citations (22 resolving, 36 not — 33 merely mis-rooted relative to
  `frontend/src/`, only 3 genuinely gone) — and no consumer in four-plus months of quarantine.
  Weighed against the PO's 2026-08-13 directive archiving further frontend UI work. Converted to
  `tier: reference`: `code_refs` and the `## Facts` heading dropped, the file-by-file Fact detail
  retired to git history, and the durable "why" content above written in its place. Not moved to
  `wiki/archive/` — frontend/ is live code, not a decommissioned feature, so the sample-mode/
  deployment-and-infra tombstone shape does not apply; this stays in the main wiki dir at
  `tier: reference`, matching `deployment-and-infra.md`'s precedent for that exact distinction.
  Inbound plain-path references corrected in the same story: `CLAUDE.md`'s "full detail" pointer,
  and the frontend-lens council prompt's "wiki Facts vs code" phrasing (both `.claude/` and
  `.agents/` copies of `council.config.yaml`). `backend/tests/test_citation_gate.py`'s baseline
  table, headline-ratio comment, and `test_ac1_docstring_scope_numbers_are_current` assertions
  re-derived live in the same commit (map-tier article count 12 → 11; `total`/`anchored`/
  `globally_distinct` unaffected — this article contributed 0 citations to that gate both before
  and after, having never carried a `` `path:line` `` citation).
