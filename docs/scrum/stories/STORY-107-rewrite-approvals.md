---
id: STORY-107
title: Rewrite approvals — evidence-first queue on new skin
type: story
---

## Context
UI-rewrite initiative (PO 2026-07-18). Binding brief: docs/scrum/ui-rewrite/design-brief.md.
Depends on STORY-103 foundation + STORY-104 shell.

## Description
Port the evidence-first approval concept (accepted in the parked initiative) onto the new
design: friendly component name (slug secondary), transition badges, Proposed RelativeTime,
per-location latest results (status/latency/relative time; skeleton/degrade-gracefully),
'View checks' deep link (?signal=), consequence copy on approve confirm; reject unchanged;
designed empty state ('Queue clear').

## Acceptance Criteria
- [ ] AC1: card anatomy per description incl. evidence rows + graceful degradation (Vitest, MSW failure path).
- [ ] AC2: deep link lands Check History pre-filtered (live).
- [ ] AC3: approve confirm states the publish consequence naming component + target status; reject prompt unchanged.
- [ ] AC4: gates green; live pass with a real sample-mode proposal (reject + off after).

## History
- 2026-07-18: filed at ui-rewrite refinement (PO-delegated); estimate 3.
