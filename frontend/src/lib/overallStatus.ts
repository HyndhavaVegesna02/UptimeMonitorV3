import { toHealthStatus } from '../api/statusMapping'
import type { ComponentDTO } from '../api/types'
import type { HealthStatus } from '../components/StatusBadge/StatusBadge'

/**
 * Worst-of ranking (STORY-121 AC4) — lower index is worse. `missing` (the
 * "no data at all" health state) never appears on a live `ComponentDTO`
 * (that vocabulary belongs to STORY-122's per-signal availability view), so
 * it is intentionally absent from this order.
 */
const SEVERITY_ORDER: HealthStatus[] = ['down', 'partial', 'degraded', 'maintenance', 'unknown', 'up']

/**
 * Derives the topbar's worst-of overall status across all components (AC4):
 * down > partial > degraded > maintenance > unknown > up; an empty list is
 * `unknown` (no data to judge health by, never a fabricated "up"). Pure and
 * derived on every render — never stored via an effect
 * (vercel-react-best-practices: derived-state-not-effect).
 */
export function deriveOverallStatus(components: ComponentDTO[]): HealthStatus {
  if (components.length === 0) {
    return 'unknown'
  }

  const present = new Set(components.map((component) => toHealthStatus(component.status)))

  for (const candidate of SEVERITY_ORDER) {
    if (present.has(candidate)) {
      return candidate
    }
  }

  // Unreachable: SEVERITY_ORDER covers every HealthStatus toHealthStatus can
  // produce, but a defensive fallback avoids an implicit `undefined` return.
  return 'unknown'
}
