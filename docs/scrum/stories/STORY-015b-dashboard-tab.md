---
id: STORY-015b
title: Dashboard tab — component statuses
type: feature
---

## Context
Spec: dossier §17. Zone 7. Depends on STORY-015a (shell). The operator's landing view: current status of
every component. Consumes the existing API (see `api-five-file-convention` wiki).

## Acceptance Criteria
- [ ] AC1: The Dashboard tab renders each component with its current status (up / degraded / down /
      maintenance), using the design-system health tokens from `frontend/design-system/MASTER.md`.
- [ ] AC2: Data comes from the typed API client against `GET /api/v1/components` (the real status read);
      loading (skeleton) + error + empty states handled; MSW-backed Vitest tests cover success/empty/error.
- [ ] AC3: Accessibility floor met (status not conveyed by color alone — icon/label too; keyboard order;
      contrast ≥4.5:1). Responsive at 375px.

## Skills to use
`ui-ux-pro-max` (dashboard page override + status patterns), `vercel-react-best-practices`,
`design-taste-frontend`.

## History
- 2026-06-29: created as a per-tab split-child of STORY-015. 3 pts. Status: ready (enters a sprint after 015a).
