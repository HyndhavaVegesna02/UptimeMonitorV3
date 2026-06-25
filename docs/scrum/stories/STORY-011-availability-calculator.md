---
id: STORY-011
title: Availability calculator — two-grain math + group rollup
type: feature
---

## Context
Spec: dossier §11 (availability engine). Zone 4. The system's first CALCULATOR — compute-only,
no tables, part of the constant core (`core/services/availability.py`). Runs parallel to the
four-stage pipeline, never consults the streak (P4). Derive-on-read, persists nothing (D-1).
Reuses `collapse` (STORY-010, built).

**Split note (2026-06-25):** the per-component SKEW flag (Tier-2 item 7 / T2.7 — a cross-signal
watermark peer comparison) was split out at refinement into **STORY-026**; this story is the
two-grain availability/completeness math + group rollup.

## Description
In `core/services/availability.py`: pure functions computing two percentages from the same
observation stream at deliberately different grains, plus a group rollup.
- **Availability %** over collapsed verdicts (cycles): `passing ÷ (total − maintenance)` — `up`
  passes; `down`/`degraded` don't; maintenance excluded BOTH sides; gaps excluded from the
  denominator (default `exclude` policy). Reuses `collapse`.
- **Completeness %** over raw observations: `actual ÷ (intervals × distinct_locations)` where
  `intervals = window ÷ interval` and `distinct_locations = COUNT(DISTINCT location)`. The
  location-aware denominator is the multi-location fix (stops a 3-location signal reporting 300%).
- **Group rollup**: a group's availability and completeness are each the MIN of its children;
  counts (verdicts, passing, maintenance, gaps) SUM across children; percentages take the min.
  Children with no data are excluded from the min but their absence stays visible.

`interval` and `window` are INJECTED inputs (parameters), NOT loaded from per-app config — the
calculator stays pure and config-free (the composition layer will supply them later, the same way
STORY-010 injected maintenance). Observations are read through a repository port: add a read
capability to the persistence boundary (e.g. an observation-in-window read method/port);
ALL SQL stays behind the port — the service never sees SQL.

Result shape (dossier §11, frozen):
```
AvailabilityResult: availability_pct: float | None; completeness_pct: float | None;
  total_verdicts: int; passing_verdicts: int; maintenance_verdicts: int; gap_verdicts: int;
  distinct_locations: int; window: str; computed_at: datetime
```

## Acceptance Criteria (refined — PO-approved 2026-06-25)
- [ ] AC1: `availability_pct` correct on in-memory fixtures per §11: `passing ÷ (total −
      maintenance)`, `up` passes / `down`+`degraded` don't, maintenance excluded both sides, gaps
      excluded (default `exclude`). Built on collapsed verdicts (reuses `collapse`).
- [ ] AC2: `completeness_pct` uses the location-aware denominator `intervals × distinct_locations`
      — a 3-location signal NEVER exceeds 100% completeness. Tested.
- [ ] AC3: Group rollup — a group's availability/completeness = MIN of its children; counts SUM;
      children with no data are excluded from the min but their absence stays visible. Tested.
- [ ] AC4: Derive-on-read — nothing is persisted; the entry points are shaped so a short-TTL cache
      could drop in later, but NO cache is built (working agreement: measure first).
- [ ] AC5: Observations are read through a repository port — ALL SQL behind the port; the service
      is pure and provider-blind (no vendor/HTTP/SQL imports); `lint-imports` green. `interval`/
      `window` are injected inputs (no per-app config dependency).
- [ ] AC6: Empty/degenerate input has DEFINED, TESTED behavior (per the sprint-6 working
      agreement): a window with zero observations → `availability_pct=None` (no verdicts to judge)
      with zero counts, and completeness with a zero denominator → `None` rather than a divide
      error. No crash; documented.

## Resolved Questions
- Gap policy default: **`exclude`** (gaps excluded from the availability denominator, dossier §11).
- `AvailabilityResult` fields: the §11 frozen dataclass above (PO-approved at refinement, 2026-06-25).
- Skew flag: OUT of scope — split to STORY-026.

## History
- 2026-06-23: drafted from YOURTEAM_INCEPTION.md §8 + dossier §11. Status: draft.
- 2026-06-25: refined for Sprint 7. Skew split to STORY-026; open questions resolved from §11
  (gap=exclude, AvailabilityResult shape); added the empty-input AC (sprint-6 agreement); estimate
  held at 5. Status: ready.
