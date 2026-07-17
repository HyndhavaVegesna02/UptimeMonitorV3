import type { ComponentDTO } from '../../api/types'
import { toHealthStatus } from '../../api/statusMapping'
import type { SummaryCardTone } from '../../components'

export interface SummaryCardViewModel {
  key: string
  label: string
  value: number
  sub: string
  tone: SummaryCardTone
  /** Passed straight through to `SummaryCard`'s `neutralAtZero` (STORY-099
   * AC1, journal D4): true for the "bad state" buckets (degraded/partial/
   * down) — a 0 count there is good news, not an alert — false for
   * Operational, which stays its status color regardless of count. */
  neutralAtZero: boolean
}

/**
 * Derives the Dashboard's summary-card row (STORY-057 AC1, re-scoped by
 * STORY-099 AC1) from `GET /api/v1/components` — REAL counts only, never a
 * fabricated total. One card per health bucket `toHealthStatus` can produce
 * among component statuses (up/degraded/partial/down); the redundant
 * "Components" total card (it only ever duplicated "Operational N of N") is
 * gone — the Dashboard replaces that slot with the "Pending approvals" /
 * "Maintenance" cross-tab awareness action cards instead (`DashboardPage.tsx`,
 * not derived from this function). A status the mapper doesn't recognize
 * (`toHealthStatus`'s `'unknown'` fallback) gets its own trailing card too,
 * ONLY when it actually occurs — no permanent zero-value "Unknown" card
 * cluttering the common case.
 */
export function summarizeComponents(components: ComponentDTO[]): SummaryCardViewModel[] {
  const total = components.length
  const counts = { up: 0, degraded: 0, partial: 0, down: 0, unknown: 0 }

  for (const component of components) {
    const status = toHealthStatus(component.status)
    if (
      status === 'up' ||
      status === 'degraded' ||
      status === 'partial' ||
      status === 'down'
    ) {
      counts[status] += 1
    } else {
      counts.unknown += 1
    }
  }

  const cards: SummaryCardViewModel[] = [
    {
      key: 'up',
      label: 'Operational',
      value: counts.up,
      sub: `of ${total}`,
      tone: 'up',
      neutralAtZero: false,
    },
    {
      key: 'degraded',
      label: 'Degraded',
      value: counts.degraded,
      sub: `of ${total}`,
      tone: 'degraded',
      neutralAtZero: true,
    },
    {
      key: 'partial',
      label: 'Partial outage',
      value: counts.partial,
      sub: `of ${total}`,
      tone: 'partial',
      neutralAtZero: true,
    },
    {
      key: 'down',
      label: 'Down',
      value: counts.down,
      sub: `of ${total}`,
      tone: 'down',
      neutralAtZero: true,
    },
  ]

  if (counts.unknown > 0) {
    cards.push({
      key: 'unknown',
      label: 'Unknown',
      value: counts.unknown,
      sub: `of ${total}`,
      tone: 'neutral',
      neutralAtZero: false,
    })
  }

  return cards
}
