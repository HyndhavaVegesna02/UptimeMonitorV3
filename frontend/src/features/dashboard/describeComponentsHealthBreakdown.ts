import { toHealthStatus } from '../../api/statusMapping'
import type { ComponentDTO } from '../../api/types'
import type { HealthStatus } from '../../components/StatusBadge/StatusBadge'

const BREAKDOWN_LABELS: Record<Exclude<HealthStatus, 'up'>, string> = {
  degraded: 'degraded',
  partial: 'partial outage',
  down: 'down',
  maintenance: 'in maintenance',
  unknown: 'unknown',
  missing: 'missing data',
}

/**
 * The KPI row's "components healthy" sub-line (STORY-122 AC1, e.g. "1
 * degraded · 1 in maintenance") — a real breakdown of the SAME
 * `GET /api/v1/components` response the headline n/total count uses, never
 * an invented figure. `null` when every component is up (nothing to call
 * out) or the list is empty.
 */
export function describeComponentsHealthBreakdown(components: ComponentDTO[]): string | null {
  const counts = new Map<Exclude<HealthStatus, 'up'>, number>()

  for (const component of components) {
    const status = toHealthStatus(component.status)
    if (status === 'up') {
      continue
    }
    counts.set(status, (counts.get(status) ?? 0) + 1)
  }

  if (counts.size === 0) {
    return null
  }

  return [...counts.entries()].map(([status, count]) => `${count} ${BREAKDOWN_LABELS[status]}`).join(' · ')
}
