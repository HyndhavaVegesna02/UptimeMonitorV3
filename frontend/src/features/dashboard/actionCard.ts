import type { SummaryCardTone } from '../../components'

export interface ActionCardView {
  /** An honest em-dash while the count is unresolved (loading/error) — a
   * real number once known. Never fabricated as 0. */
  value: number | string
  tone: SummaryCardTone
}

/**
 * Derives a cross-tab awareness action card's display value + tone
 * (STORY-099 AC2, journal D4) from a live count that a `useFetch`-backed
 * hook may not have resolved yet: `undefined` (loading OR error — the same
 * graceful-degradation convention as `useApprovalsBadge`) renders an honest
 * em-dash in the neutral tone rather than fabricating a `0`; a resolved `0`
 * is genuine good news (color carries state only when non-nominal) and
 * stays neutral too; any resolved count above `0` gets the accent
 * (indigo/info) tone — deliberately never the alert-red vocabulary the
 * health-status cards use, since a pending approval or a scheduled
 * maintenance window is informational, not a fault.
 */
export function actionCardView(count: number | undefined): ActionCardView {
  if (count === undefined) {
    return { value: '—', tone: 'neutral' }
  }
  return { value: count, tone: count > 0 ? 'accent' : 'neutral' }
}
