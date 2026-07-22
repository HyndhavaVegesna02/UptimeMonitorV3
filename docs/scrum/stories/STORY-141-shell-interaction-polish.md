# STORY-141 — Shell interaction polish

- **Status:** ready
- **Points:** 3
- **Sprint:** 61
- **Type:** defect
- **Scope:** frontend only

## Context
From the 2026-07-22 design-QA review, verified live + in code. The notifications bell is a
dead control (`Topbar.tsx:71` — no `onClick`/panel; confirmed live). The mobile nav drawer
has no in-drawer close button and no brand/title header (dismiss only via backdrop/Escape;
confirmed live @390). The Styleguide Loading/Error/Empty examples read center-aligned while
sibling gallery sections are left-aligned.

## Acceptance criteria
- **AC1** — The notifications **bell opens a real popover/panel** with a proper empty state
  ("No notifications") and correct a11y (`aria-expanded`/`aria-controls`, focus management,
  Escape-to-close, click-outside). Fresh, minimal, extensible — not a stub. (If the PO would
  rather hide it than build it, that is a review call; the default is to implement.)
- **AC2** — The mobile drawer has an **in-drawer brand/title header AND an explicit close (X)
  button** (in addition to backdrop/Escape). Verified live @390.
- **AC3** — The Styleguide Loading/Error/Empty gallery entries are **left-aligned to match the
  sibling sections** (the state primitives keep their own internal centering; the gallery cell
  presents them consistently).
- **AC4** — Gates green; reality-gate the bell (open/empty/close) + mobile drawer
  (open/close/header) live.

## Design / skills
Honor the mandated skills. The bell popover and the drawer header are fresh design-system
components — match the sprint-59 language (Panel, Button, Icon). No raw hex; tokens only.
