import type { ComponentDTO } from '../../api/types'
import { toHealthStatus } from '../../api/statusMapping'
import type { SummaryCardTone } from '../../components'

export interface SummaryCardViewModel {
  key: string
  label: string
  value: number
  sub: string
  tone: SummaryCardTone
}

/**
 * Derives the Dashboard's summary-card row (STORY-057 AC1) from
 * `GET /api/v1/components` — REAL counts only, never a fabricated total.
 * One card per health bucket `toHealthStatus` can produce among component
 * statuses (up/degraded/partial/down), led by a "Components" total card, so
 * the cards' values always reconcile with `components.length`. A status the
 * mapper doesn't recognize (`toHealthStatus`'s `'unknown'` fallback) gets
 * its own trailing card too, ONLY when it actually occurs — no permanent
 * zero-value "Unknown" card cluttering the common case.
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
    { key: 'total', label: 'Components', value: total, sub: 'monitored', tone: 'accent' },
    { key: 'up', label: 'Operational', value: counts.up, sub: `of ${total}`, tone: 'up' },
    {
      key: 'degraded',
      label: 'Degraded',
      value: counts.degraded,
      sub: `of ${total}`,
      tone: 'degraded',
    },
    {
      key: 'partial',
      label: 'Partial outage',
      value: counts.partial,
      sub: `of ${total}`,
      tone: 'partial',
    },
    { key: 'down', label: 'Down', value: counts.down, sub: `of ${total}`, tone: 'down' },
  ]

  if (counts.unknown > 0) {
    cards.push({
      key: 'unknown',
      label: 'Unknown',
      value: counts.unknown,
      sub: `of ${total}`,
      tone: 'neutral',
    })
  }

  return cards
}
