---
id: STORY-015
title: Dashboard shell + six tabs (redesigned)
type: feature
---

## Context
Spec: dossier §17 (two-surface model; six-tab IA). Zone 7. React/TS SPA — the operator
cockpit. Same information architecture as V2, fresh visual design.

## ⚠️ Split required before this story can enter a sprint
The seed flags this as **likely an 8** — an 8 may never enter a sprint. At refinement,
split into (at minimum): a **shell** story (SPA scaffold, routing, six-tab nav, API
client, CORS, frontend test runner choice) and **per-tab** stories (Dashboard,
Availability, Approvals [approve/reject], Check History, Maintenance, Publications).
Choose the frontend test runner (Vitest?) and E2E approach (Playwright?) at that point —
both are open tooling gaps to raise at planning.

## Description
React + TypeScript SPA on Vercel, six tabs (Dashboard · Availability · Approvals ·
Check History · Maintenance · Publications), consuming the API from STORY-014. The
Approvals tab performs approve/reject. CORS restricted to the Vercel origin.

## Acceptance Criteria (draft — will be re-derived per split story)
- [ ] AC1: Six tabs render against the live API.
- [ ] AC2: Approve/reject works on the Approvals tab.
- [ ] AC3: CORS restricted to the Vercel origin (+ localhost for dev).

## Open Questions
- MUST split (likely an 8). Choose frontend test runner + E2E tool at refinement/planning.

## History
- 2026-06-23: drafted from YOURTEAM_INCEPTION.md §8 + dossier §17. Status: draft — MUST be split before its sprint.
