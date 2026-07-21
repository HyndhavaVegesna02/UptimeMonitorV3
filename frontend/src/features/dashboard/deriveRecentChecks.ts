import type { ComponentDTO } from '../../api/types'
import type { HealthStatus } from '../../components/StatusBadge/StatusBadge'
import { formatRelativeTime } from '../../lib/relativeTime'
import { locationLabel } from './locationLabel'
import type { SignalsMap } from './types'

export interface RecentCheckRow {
  key: string
  componentName: string
  locationLabel: string
  relativeTime: string
  latencyMs: number | null
  health: HealthStatus
}

function toRowHealth(health: string): HealthStatus {
  return health === 'up' ? 'up' : health === 'down' ? 'down' : 'degraded'
}

/**
 * The Dashboard's recent-checks feed (STORY-122 AC5) — the latest N
 * observations across every signal, most-recent first. Each row's
 * component name is resolved via signal_key === component id (the current
 * topology's 1:1 alignment, confirmed at the reality gate); an
 * unrecognized signal_key falls back to the raw key itself rather than
 * crashing or fabricating a name.
 */
export function deriveRecentChecks(
  components: ComponentDTO[],
  signalsData: SignalsMap,
  now: Date,
  limit: number,
): RecentCheckRow[] {
  const nameBySignalKey = new Map(components.map((component) => [component.id, component.name]))

  const withObservedAt = Object.entries(signalsData).flatMap(([signalKey, { history }]) =>
    history.map((observation) => ({ signalKey, observation })),
  )

  return withObservedAt
    .sort(
      (a, b) => new Date(b.observation.observed_at).getTime() - new Date(a.observation.observed_at).getTime(),
    )
    .slice(0, limit)
    .map(({ signalKey, observation }) => ({
      key: `${signalKey}-${observation.observed_at}-${observation.location}`,
      componentName: nameBySignalKey.get(signalKey) ?? signalKey,
      locationLabel: locationLabel(observation.location),
      relativeTime: formatRelativeTime(new Date(observation.observed_at), now),
      latencyMs: observation.latency_ms,
      health: toRowHealth(observation.health),
    }))
}
