import type { HealthStatus } from '../components'

/**
 * Maps the backend's closed `ComponentStatus` vocabulary
 * (`backend/src/core/domain/status.py::ComponentStatus` — operational /
 * degraded / partial_outage / major_outage) onto the shell's health tokens
 * (up / down / degraded / maintenance / unknown). This is the authoritative
 * component-health presentation mapping, consumed by the Dashboard tab
 * (STORY-015b) and any later surface that renders component status; an
 * unrecognized status falls back to `unknown`.
 */
const STATUS_MAP: Record<string, HealthStatus> = {
  operational: 'up',
  degraded: 'degraded',
  partial_outage: 'degraded',
  major_outage: 'down',
}

export function toHealthStatus(status: string): HealthStatus {
  return STATUS_MAP[status] ?? 'unknown'
}
