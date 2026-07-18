import type { ComponentDTO } from '../../api/types'
import { toHealthStatus } from '../../api/statusMapping'
import type { HealthStatus } from '../../components'

/**
 * Worst-first ordering for the command-bar overall-status dot (STORY-104
 * AC2, design brief §IA — the exact table the brief specifies). `down` is
 * the worst outcome, `up` the best; `maintenance`/`missing` never come out
 * of `toHealthStatus` today (this story's scope is the components endpoint
 * only — a component's maintenance state is a separate concept, see
 * `useMaintenanceWindows`) but are included so the ordering stays TOTAL
 * over the whole `HealthStatus` vocabulary, matching the brief exactly.
 */
const WORST_FIRST: readonly HealthStatus[] = [
  'down',
  'partial',
  'degraded',
  'maintenance',
  'unknown',
  'missing',
  'up',
]

/**
 * Worst-of over every component's mapped health status (STORY-104 AC2) —
 * the single source of truth for the command bar's overall-status dot. An
 * empty component list has no signal to assess: returns `'unknown'` rather
 * than fabricating a false "all up" reading (the explicit, tested
 * empty-input behavior the test-discipline convention requires).
 */
export function deriveOverallStatus(components: ComponentDTO[]): HealthStatus {
  if (components.length === 0) {
    return 'unknown'
  }

  let worst: HealthStatus = 'up'
  let worstRank = WORST_FIRST.indexOf(worst)

  for (const component of components) {
    const status = toHealthStatus(component.status)
    const rank = WORST_FIRST.indexOf(status)
    if (rank < worstRank) {
      worst = status
      worstRank = rank
    }
  }

  return worst
}
