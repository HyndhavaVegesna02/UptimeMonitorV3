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

/**
 * Mirrors `backend/src/api/v1/topology/models.py::TopologySignalDTO`
 * (STORY-044/STORY-015d AC1). `interval_seconds` is nullable — `None` when
 * the seeded row predates the interval backfill or a re-seed has not yet
 * run, surfaced honestly rather than guessed.
 */
export interface TopologySignalDTO {
  signal_key: string
  name: string
  interval_seconds: number | null
  component_id: string
}

/**
 * Mirrors `backend/src/api/v1/topology/models.py::ComponentTopologyDTO`
 * (STORY-044/STORY-015d AC1). `signals` is sorted server-side; a component
 * with no mapped signals gets `signals: []`, never a 500.
 */
export interface ComponentTopologyDTO {
  id: string
  name: string
  signals: TopologySignalDTO[]
}

/**
 * Mirrors `backend/src/api/v1/availability/models.py::AvailabilityDTO`
 * (STORY-044/STORY-015d AC1, AC2). Both percentages are nullable — `None`
 * on a degenerate/no-data window (never a crash, never a stand-in `0`).
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
 * Mirrors `backend/src/api/v1/availability/models.py::SignalAvailabilityDTO`
 * — `AvailabilityDTO` plus `signal_key` naming which per-signal child this
 * result is for (STORY-015d AC1).
 */
export interface SignalAvailabilityDTO extends AvailabilityDTO {
  signal_key: string
}

/**
 * Mirrors
 * `backend/src/api/v1/availability/models.py::ComponentAvailabilityDTO`
 * (STORY-044/STORY-015d AC1, AC2) — the component-grain `rollup` plus its
 * per-signal `signals` children, sorted by `signal_key`. A zero-signal
 * component gets `signals: []` and an all-None/zero `rollup`, never a 500.
 */
export interface ComponentAvailabilityDTO {
  component_id: string
  rollup: AvailabilityDTO
  signals: SignalAvailabilityDTO[]
}

/**
 * Mirrors `backend/src/api/v1/history/models.py::ObservationDTO`
 * (STORY-014c/STORY-015e AC1) — a single raw per-signal check observation
 * (the ingest ledger view) as returned newest-first by `GET /api/v1/history`.
 * `health` is the OBSERVATION vocabulary (`"up" | "down" | "degraded"`,
 * serialized via `.value`) — **NOT** the `ComponentStatus` vocabulary
 * `api/statusMapping.ts::toHealthStatus` maps (see
 * `features/history/observationHealth.ts` for the separate mapper and why it
 * exists). `latency_ms` is an INTEGER MILLISECONDS value or `null` (no
 * measurement) — render `null` as an em-dash, never `0 ms`. `location` is a
 * raw vendor location id string (e.g. `"SYNTHETIC_LOCATION-0000000000000060"`);
 * STORY-064 adds `response_status_code` (an INTEGER HTTP status code or
 * `null` when missing/unparsable at the source, or a pre-migration row --
 * render `null` as an em-dash, same convention as `latency_ms`) and
 * `check_type` (a non-null string mapped from the persisted provenance
 * `native_kind`, e.g. `"http"` -- always present; render uppercased, `"HTTP"`)
 * — render as-is, in the mono token.
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
 * Mirrors `backend/src/api/v1/publications/models.py::PublicationDTO`
 * (STORY-037/STORY-015g AC1; STORY-072 AC3 added `outcome`) — a single
 * recorded publish ATTEMPT: the status that was (attempted to be) pushed,
 * for which component, when, and whether the Statuspage call itself
 * succeeded. There is NO from-status field — a publication carries only the
 * status that was (attempted to be) published, so an "old→new" transition
 * cannot be rendered from this shape. `status` is the `ComponentStatus`
 * vocabulary (operational / degraded / partial_outage / major_outage,
 * serialized via `.value`) — **UNLIKE** `ObservationDTO.health`, this DOES
 * map through the EXISTING `api/statusMapping.ts::toHealthStatus` (same
 * producing vocabulary as `ComponentDTO.status`). `outcome` is a CLOSED
 * `'succeeded' | 'failed'` vocabulary (STORY-072) — DISTINCT from `status`:
 * it is whether the Statuspage publish call itself succeeded, not the health
 * status attempted. `proposal_id` links to the originating proposal and is
 * nullable (no proposal_id when the publish had none) — render an em-dash,
 * never a sentinel `0`. `GET /api/v1/publications` returns these
 * newest-first, capped at the repository's most-recent 50 (`list_recent`,
 * no pagination).
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

/**
 * Mirrors `backend/src/api/v1/sample_mode/models.py::SampleModeDTO`
 * (STORY-048/STORY-049 AC4) — the persisted, process-crossing sample-mode
 * flag. `enabled: false` when the flag was never set. THIS IS A TEMPORARY
 * FEATURE (see `docs/scrum/wiki/sample-mode.md`'s REMOVAL inventory).
 */
export interface SampleModeDTO {
  enabled: boolean
}

/**
 * Mirrors `backend/src/api/v1/maintenance/models.py::MaintenanceWindowDTO`
 * (STORY-036/STORY-015f AC1) — a single scheduled maintenance window.
 * `starts_at`/`ends_at` are ISO-8601 UTC strings (trailing `Z`); `reason` is
 * `string | null` — render `null` as an em-dash, never "null"/a blank cell
 * (STORY-015f conventions checklist (h)). There is NO `state` field on the
 * wire — upcoming/active/past is derived CLIENT-SIDE by
 * `features/maintenance/windowState.ts` using the backend's half-open rule
 * (`core/ports/maintenance_repository.py::is_under_maintenance`): active
 * iff `starts_at <= now < ends_at`.
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
 * Mirrors
 * `backend/src/api/v1/maintenance/models.py::CreateMaintenanceRequest`
 * (STORY-036/STORY-015f AC2) — the `POST /api/v1/maintenance` body.
 * `starts_at`/`ends_at` MUST be tz-aware ISO strings (a trailing `Z`) — the
 * backend 422s a naive datetime (STORY-015f AC3);
 * `features/maintenance/useMaintenance.ts`'s caller builds them via
 * `new Date(value).toISOString()` from a `datetime-local` input. `reason` is
 * optional/nullable, matching the backend default of `None`.
 */
export interface CreateMaintenanceRequest {
  component_id: string
  starts_at: string
  ends_at: string
  reason?: string | null
  title?: string | null
}
