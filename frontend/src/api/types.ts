/**
 * DTO types mirroring the backend's Pydantic models (STORY-015a AC3).
 * `backend/src/api/v1/components/models.py::ComponentDTO` is the source of
 * truth this mirrors — id/name/status, status a plain string (the backend
 * serializes the `ComponentStatus` enum's `.value`: "operational",
 * "degraded", "partial_outage", "major_outage").
 */
export interface ComponentDTO {
  id: string
  name: string
  status: string
}

/**
 * Mirrors `backend/src/api/v1/approvals/models.py::ProposalDTO`
 * (STORY-015c AC1). `from_status` is nullable — a component's first-ever
 * proposal has no prior status. No reason/evidence field, no friendly
 * component name: the tab renders `component_id` and the raw transition.
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
 * Mirrors `backend/src/api/v1/decisions/models.py::DecisionRequest`
 * (STORY-015c AC2). `action` is constrained to the two values the backend
 * validates; `actor` comes from the swappable `getActor()` seam
 * (`api/actor.ts`), never a literal scattered across call sites.
 */
export interface DecisionRequest {
  action: 'approve' | 'reject'
  actor: string
  notes?: string | null
}

/** Mirrors `backend/src/api/v1/decisions/models.py::DecisionResponse`. */
export interface DecisionResponse {
  proposal_id: number
  state: string
  resolved_at: string
}
