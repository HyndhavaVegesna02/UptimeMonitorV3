import type { HealthStatus } from '../../components'

/**
 * Maps the OBSERVATION health vocabulary (`"up" | "down" | "degraded"` —
 * `core/domain/signal.py::Health`, serialized via `.value` in
 * `history/service.py`) onto the shell's health tokens `StatusBadge`
 * consumes (STORY-015e AC3).
 *
 * This is DELIBERATELY SEPARATE from `api/statusMapping.ts::toHealthStatus`:
 * that mapper's INPUT is the backend's `ComponentStatus` vocabulary
 * (`operational` / `degraded` / `partial_outage` / `major_outage`) used by
 * the Dashboard and Publications tabs. The two vocabularies share the string
 * `"degraded"` but otherwise disagree — `ComponentStatus` has no `"up"`
 * value, so reusing `toHealthStatus` here would silently map an observation's
 * `"up"` to `"unknown"` (its `else` branch), misreporting a healthy check as
 * unknown. Keeping the maps separate also means neither tab's contract
 * change ripples into the other's presentation.
 */
const OBSERVATION_HEALTH_MAP: Record<string, HealthStatus> = {
  up: 'up',
  down: 'down',
  degraded: 'degraded',
}

export function observationHealth(health: string): HealthStatus {
  return OBSERVATION_HEALTH_MAP[health] ?? 'unknown'
}
