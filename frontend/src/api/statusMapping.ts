import type { HealthStatus } from '../components/StatusBadge/StatusBadge'

/**
 * Maps the backend's vendor status vocabulary
 * (`backend/src/api/v1/components/models.py::ComponentDTO.status` —
 * operational / degraded_performance / partial_outage / major_outage /
 * under_maintenance) onto the shell's health tokens (STORY-121). This is the
 * authoritative component-health presentation mapping — an unrecognized
 * status falls back to `unknown` rather than crashing.
 */
const STATUS_MAP: Record<string, HealthStatus> = {
  operational: 'up',
  degraded_performance: 'degraded',
  partial_outage: 'partial',
  major_outage: 'down',
  under_maintenance: 'maintenance',
}

export function toHealthStatus(status: string): HealthStatus {
  return STATUS_MAP[status] ?? 'unknown'
}
