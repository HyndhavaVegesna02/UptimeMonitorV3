/**
 * DTO types mirroring the backend's Pydantic models (STORY-121). These are
 * the two live contracts this story's shell needs — the sidebar's Approvals
 * badge and the topbar's worst-of status pill. STORY-122 extends this file
 * with the remaining DTOs (history/availability/maintenance/publications).
 */

/**
 * Mirrors `backend/src/api/v1/components/models.py::ComponentDTO`. `status`
 * is the raw vendor string (`operational` / `degraded_performance` /
 * `partial_outage` / `major_outage` / `under_maintenance` / anything else) —
 * `api/statusMapping.ts::toHealthStatus` maps it onto the shell's health
 * vocabulary.
 */
export interface ComponentDTO {
  id: string
  name: string
  status: string
}

/**
 * Mirrors `backend/src/api/v1/approvals/models.py::ProposalDTO`.
 * `from_status` is nullable — a component's first-ever proposal has no
 * prior status.
 */
export interface ProposalDTO {
  id: number
  component_id: string
  from_status: string | null
  to_status: string
  state: string
  proposed_at: string
}

/**
 * Mirrors `backend/src/api/v1/history/models.py::ObservationDTO` (STORY-122).
 * `latency_ms`/`response_status_code` are nullable — the normalizer's
 * source row can omit either.
 */
export interface ObservationDTO {
  signal_key: string
  observed_at: string
  health: string
  location: string
  latency_ms: number | null
  response_status_code: number | null
  check_type: string
}

/**
 * Mirrors `backend/src/api/v1/availability/models.py::AvailabilityDTO`
 * (STORY-122). `availability_pct`/`completeness_pct` are nullable — a
 * degenerate (no-data) window computes neither.
 */
export interface AvailabilityDTO {
  availability_pct: number | null
  completeness_pct: number | null
  total_verdicts: number
  passing_verdicts: number
  maintenance_verdicts: number
  gap_verdicts: number
  distinct_locations: number
  window: string
  computed_at: string
}

/**
 * Mirrors `backend/src/api/v1/maintenance/models.py::MaintenanceWindowDTO`
 * (STORY-122). `reason`/`title` are nullable.
 */
export interface MaintenanceWindowDTO {
  id: number
  component_id: string
  starts_at: string
  ends_at: string
  reason: string | null
  title?: string | null
}
