export type KpiTone = 'positive' | 'accent' | 'negative' | 'neutral'

/**
 * The "Components healthy" KPI card's accent tone (STORY-138 AC4) — tied to
 * the SAME `healthy`/`total` counts the card's own headline number uses,
 * never an arbitrary color: `positive` (green) when every component is up,
 * `negative` (red) when at least one is not, `neutral` for the explicit
 * empty-input case (no components at all — nothing to call out either way).
 */
export function componentsHealthTone(healthy: number, total: number): KpiTone {
  if (total === 0) {
    return 'neutral'
  }
  return healthy === total ? 'positive' : 'negative'
}

/**
 * The "Pending approvals" KPI card's accent tone (STORY-138 AC4) — `accent`
 * (the same sky-blue the card's own `attention` treatment already uses)
 * when something awaits review, `neutral` when the queue is empty.
 */
export function approvalsTone(pendingApprovals: number): KpiTone {
  return pendingApprovals > 0 ? 'accent' : 'neutral'
}
