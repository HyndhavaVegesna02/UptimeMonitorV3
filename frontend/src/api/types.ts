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
