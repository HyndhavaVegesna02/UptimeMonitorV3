---
id: STORY-015b
title: Dashboard tab — live component health at a glance
type: feature
---

## Context
Spec: dossier §17. Zone 7. Split-child of STORY-015; depends on STORY-015a (shell). The first
real tab — it consumes `GET /api/v1/components` (STORY-014b) and establishes the per-tab
pattern (page component in `tabs/`, data hook in `hooks/`, shell primitives for badges/panels)
that 015c–015g copy.

## Description
The operator's landing view: every monitored component with its current health, at a glance.
Each component row shows name + health StatusBadge (dot/icon + label — never color alone).
Health tokens from the shell drive the badge; an unknown status value renders a neutral
"unknown" badge rather than crashing.

**API contract note (verified 2026-07-02):** `backend/src/api/v1/components/models.py::ComponentDTO`
exposes exactly `{id, name, status}` — there is NO last-observed timestamp, latency, or location
field. This tab renders only what the DTO provides (name + status); a richer per-component
last-observed/latency view would require a backend DTO change and is out of scope here (candidate
future story). The shell already proved this endpoint end-to-end in
`features/dashboard/ComponentsProbe.tsx` (STORY-015a AC3) — 015b promotes that proving example
into the real, extracted Dashboard tab.

## Acceptance Criteria
- [ ] AC1: The Dashboard tab fetches `GET /api/v1/components` via the shell's `apiClient` and
      renders one entry per component: name + status badge (icon/dot + label). A semantic table
      (`<th scope>`) or a list with proper roles — keyboard/reader accessible.
- [ ] AC2: Loading, empty ("no components configured"), and error+retry states render using the
      shell's state components; MSW-backed tests drive all three plus the success path.
- [ ] AC3: Status→badge mapping is tested via accessible text (operational→UP, degraded→DEGRADED,
      partial_outage→DEGRADED, major_outage→DOWN per `api/statusMapping.ts`), including the
      unknown-status guard (an unrecognized status string → neutral "unknown" badge).
- [ ] AC4: The per-tab pattern is established for the remaining tabs to copy — the fetch logic is
      extracted from the shell's `ComponentsProbe` into a reusable hook (e.g.
      `features/dashboard/useComponents.ts`) with the discriminated-union fetch state +
      cancelled-guard + attempt-keyed retry; the placeholder `ComponentsProbe` scaffolding is
      removed/absorbed (no dead code left behind); no `eslint-disable` to paper over effect misuse.

## Open Questions
None.

## History
- 2026-06-29: first version accepted (sprint 24), then reverted with `521764c`.
- 2026-07-02: re-refined for the Linear-guided direction. Status: ready. Estimate 3.
