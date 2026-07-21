import type { HealthStatus } from '../../components/StatusBadge/StatusBadge'

/**
 * Maps `ObservationDTO.health` ("up"|"down"|"degraded" per
 * `backend/src/api/v1/history/models.py`) onto the shell's health tokens
 * (STORY-130 — sprint-60 plan §History edge behavior). This is a DEDICATED
 * mapper for the raw-observation vocabulary — deliberately NOT
 * `api/statusMapping.ts::toHealthStatus`, which maps the *component vendor*
 * vocabulary (`operational`/`degraded_performance`/…) and would mis-map a
 * raw observation `"up"` onto `unknown` (that string isn't in its table).
 * An unrecognized value falls back to `unknown` rather than crashing.
 */
const OBSERVATION_HEALTH_MAP: Record<string, HealthStatus> = {
  up: 'up',
  down: 'down',
  degraded: 'degraded',
}

export function toObservationHealth(health: string): HealthStatus {
  return OBSERVATION_HEALTH_MAP[health] ?? 'unknown'
}
