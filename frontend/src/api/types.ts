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
 * (STORY-122/129). `availability_pct`/`completeness_pct` are 0-1 FRACTIONS
 * on the wire (never 0-100) and nullable — a degenerate (no-data) window
 * computes neither; render "no data", never a fabricated `0%`.
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
 * (STORY-122, tightened STORY-132). `reason`/`title` are nullable but
 * ALWAYS present on the wire — `title` is a required (never-absent) nullable
 * field, not an optional one (sprint-60 plan §Shared foundation).
 */
export interface MaintenanceWindowDTO {
  id: number
  component_id: string
  starts_at: string
  ends_at: string
  reason: string | null
  title: string | null
}

/**
 * Mirrors `backend/src/api/v1/maintenance/models.py::CreateMaintenanceRequest`
 * (STORY-132) — the body of `POST /api/v1/maintenance`. `starts_at`/`ends_at`
 * MUST be tz-aware UTC ISO strings (trailing `Z`) — the backend 422s a
 * naive or non-UTC datetime, and 422s `ends_at <= starts_at` (global API
 * contract fact + plan §Maintenance edge behavior).
 */
export interface CreateMaintenanceRequest {
  component_id: string
  starts_at: string
  ends_at: string
  reason?: string | null
  title?: string | null
}

/**
 * Mirrors `backend/src/api/v1/topology/models.py` (STORY-129) — one signal
 * belonging to a component. `interval_seconds` is nullable: signals that
 * predate the interval backfill carry no configured interval (sprint-60
 * plan §Availability edge behavior (b)).
 */
export interface TopologySignalDTO {
  signal_key: string
  name: string
  interval_seconds: number | null
  component_id: string
}

/**
 * Mirrors `backend/src/api/v1/topology/models.py::ComponentTopologyDTO`
 * (STORY-129) — `GET /api/v1/topology`'s per-component shape, nesting its
 * signals (name + interval), used to join display names onto the
 * `signal_key`-only `SignalAvailabilityDTO` children below.
 */
export interface ComponentTopologyDTO {
  id: string
  name: string
  signals: TopologySignalDTO[]
}

/**
 * Mirrors `backend/src/api/v1/decisions/models.py::DecisionRequest`
 * (STORY-131) — the body of `POST /api/v1/decisions/{proposal_id}`. `action`
 * must be exactly `"approve"`/`"reject"` and `actor` non-blank, else the API
 * 422s (the UI only ever sends valid values — `ApprovalsPage` never lets a
 * blank/other value reach this type).
 */
export interface DecisionRequest {
  action: 'approve' | 'reject'
  actor: string
  notes?: string | null
}

/**
 * Mirrors `backend/src/api/v1/decisions/models.py::DecisionResponse`
 * (STORY-131) — the 200 response of `POST /api/v1/decisions/{proposal_id}`.
 */
export interface DecisionResponse {
  proposal_id: number
  state: string
  resolved_at: string
}

/**
 * `AvailabilityDTO` plus the `signal_key` it was computed for (STORY-129) —
 * the per-signal children of `ComponentAvailabilityDTO.signals`. Carries no
 * display name (that's joined from `TopologySignalDTO.name` by `signal_key`).
 */
export interface SignalAvailabilityDTO extends AvailabilityDTO {
  signal_key: string
}

/**
 * Mirrors `backend/src/api/v1/availability/models.py::ComponentAvailabilityDTO`
 * (STORY-129) — `GET /api/v1/availability/component/{component_id}`'s
 * response: a component-grain rollup plus its nested per-signal children.
 * Verified live quirk (plan-verifier 2026-07-22): `rollup.distinct_locations`
 * reads `0` while each signal child reads the real count — a backend
 * rollup-group quirk, rendered honestly, not "fixed" client-side.
 */
export interface ComponentAvailabilityDTO {
  component_id: string
  rollup: AvailabilityDTO
  signals: SignalAvailabilityDTO[]
}

/**
 * Mirrors `backend/src/api/v1/publications/models.py::PublicationDTO`
 * (STORY-133) — `GET /api/v1/publications`'s per-attempt shape, most-recent-
 * first, capped ~50 server-side (no pagination). `status` is the raw vendor
 * status vocabulary (like `ComponentDTO.status`) — map with
 * `api/statusMapping.ts::toHealthStatus`, NOT the observation health mapper.
 * `outcome` is a SEPARATE concept from `status` (the Statuspage-call result
 * vs the published health) — never conflate the two. `proposal_id`/`author`
 * are nullable; there is NO `incident_id` field (STORY-081 unbuilt) — do not
 * invent one.
 */
export interface PublicationDTO {
  id: number
  component_id: string
  status: string
  published_at: string
  proposal_id: number | null
  outcome: 'succeeded' | 'failed'
  author: string | null
}
