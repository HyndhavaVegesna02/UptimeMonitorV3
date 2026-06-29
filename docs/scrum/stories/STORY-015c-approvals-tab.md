---
id: STORY-015c
title: Approvals tab — pending proposals list + approve/reject
type: feature
---

## Context
Spec: dossier §17 (human-approved degradations). Zone 7. Depends on STORY-015a (shell). The one
interactive tab: an operator reviews pending status proposals and approves or rejects them.

## Acceptance Criteria
- [ ] AC1: Lists pending proposals from `GET /api/v1/approvals` (proposed component status change, current
      vs proposed, timestamp), with loading/empty/error states.
- [ ] AC2: Approve and Reject actions call the backend mutation; on success the list refreshes and the
      acted item leaves the pending list; the button shows a loading state and is disabled mid-request
      (`loading-buttons`); failures surface a clear, recoverable error (`error-recovery`).
- [ ] AC3: A destructive/confirming interaction pattern for reject (confirmation per `confirmation-dialogs`),
      and approve/reject are visually distinct (`destructive-emphasis`).
- [ ] AC4: MSW-backed Vitest tests cover: list render, approve happy-path (list updates), reject
      happy-path, and a mutation-failure path. No live API.
- [ ] AC5: Accessibility floor met (focus management after action, aria-live for result, keyboard).

## Skills to use
Design source: `DESIGN-airtable.md` (reuse the shell's token layer; approve = `button-primary`, reject =
secondary/destructive emphasis per the spec's button pair).
`ui-ux-pro-max` (forms & feedback, confirmation patterns), `vercel-react-best-practices` (mutation/state),
`design-taste-frontend`.

## History
- 2026-06-29: created as a per-tab split-child of STORY-015. 5 pts (interactive, mutations). Status: ready.
