import type {
  ComponentAvailabilityDTO,
  ComponentDTO,
  ComponentTopologyDTO,
  CreateMaintenanceRequest,
  DecisionRequest,
  DecisionResponse,
  MaintenanceWindowDTO,
  ObservationDTO,
  ProposalDTO,
  PublicationDTO,
} from './types'

/**
 * Fetch-based typed API client (STORY-015a AC3). Single base-URL seam: every
 * call goes through `API_BASE_URL`, which is `/api` in both dev (proxied by
 * Vite to the local backend — vite.config.ts) and production (same-origin
 * behind CloudFront — dossier §17, STORY-089).
 */
export const API_BASE_URL = '/api'

export class ApiError extends Error {
  status?: number
  /**
   * The backend's raw `detail` string, when the non-2xx body parsed as
   * `{ detail: string }` (FastAPI's shape for a manually-raised
   * `HTTPException`, e.g. `maintenance/service.py`'s 422s — STORY-015f
   * AC3). `undefined` for network failures, malformed bodies, or a body
   * without a string `detail`. Lets a mutating tab map a 422's message onto
   * the specific field it names (see `features/maintenance/fieldError.ts`)
   * without every caller re-parsing the response body itself.
   */
  detail?: string

  constructor(message: string, status?: number, detail?: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}

/**
 * Best-effort extraction of a `{ detail: string }` body (FastAPI's
 * `HTTPException` shape) from a non-ok response, for `ApiError.detail`.
 * Uses `.clone()` so the original `response` is left readable by any other
 * caller. Never throws — a non-JSON body, an empty body, or a `detail` that
 * isn't a string all resolve to `undefined`.
 */
async function readDetail(response: Response): Promise<string | undefined> {
  try {
    const body: unknown = await response.clone().json()
    if (body && typeof body === 'object' && 'detail' in body) {
      const detail = (body as { detail: unknown }).detail
      return typeof detail === 'string' ? detail : undefined
    }
  } catch {
    // Non-JSON or empty body — no detail available.
  }
  return undefined
}

/**
 * Shared response-reader: maps a settled `fetch` `Response` to parsed JSON or a
 * typed `ApiError`. A non-2xx status → `ApiError` carrying `.status` (so callers
 * can branch on 404/409) and, when present, `.detail` (the raw backend message,
 * STORY-015f AC3); a malformed 2xx body → `ApiError` (also with status). Both
 * `getJson`/`postJson` funnel through here so there is ONE parse-error contract
 * for every future tab to inherit (single source of the error shape).
 */
async function readOkJson<T>(response: Response, path: string): Promise<T> {
  if (!response.ok) {
    const detail = await readDetail(response)
    throw new ApiError(
      `Request to ${path} failed with status ${response.status}`,
      response.status,
      detail,
    )
  }

  try {
    return (await response.json()) as T
  } catch {
    throw new ApiError(`Malformed JSON response from ${path}`, response.status)
  }
}

async function getJson<T>(path: string): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}${path}`)
  } catch {
    throw new ApiError(`Network error while requesting ${path}`)
  }

  return readOkJson<T>(response, path)
}

async function postJson<TResponse, TBody>(
  path: string,
  body: TBody,
): Promise<TResponse> {
  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
  } catch {
    throw new ApiError(`Network error while requesting ${path}`)
  }

  return readOkJson<TResponse>(response, path)
}

async function deleteRequest(path: string): Promise<void> {
  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method: 'DELETE',
    })
  } catch {
    throw new ApiError(`Network error while requesting ${path}`)
  }

  if (!response.ok) {
    const detail = await readDetail(response)
    throw new ApiError(
      `Request to ${path} failed with status ${response.status}`,
      response.status,
      detail,
    )
  }
}

/** The AC3 proving endpoint: `GET /api/v1/components`. */
export function getComponents(): Promise<ComponentDTO[]> {
  return getJson<ComponentDTO[]>('/v1/components')
}

/** `GET /api/v1/approvals` (STORY-015c AC1) — the open status proposals. */
export function getApprovals(): Promise<ProposalDTO[]> {
  return getJson<ProposalDTO[]>('/v1/approvals')
}

/**
 * `POST /api/v1/decisions/{proposal_id}` (STORY-015c AC2). Rejects with a
 * typed `ApiError` carrying `.status` on any non-2xx response — the
 * Approvals tab branches on 409 (lost race — proposal no longer open) and
 * 404 (proposal gone) distinctly from any other failure.
 */
export function postDecision(
  proposalId: number,
  body: DecisionRequest,
): Promise<DecisionResponse> {
  return postJson<DecisionResponse, DecisionRequest>(
    `/v1/decisions/${proposalId}`,
    body,
  )
}

/**
 * `GET /api/v1/topology` (STORY-044/STORY-015d AC1) — every component with
 * its nested signals, sourced from the seeded topology.
 */
export function getTopology(): Promise<ComponentTopologyDTO[]> {
  return getJson<ComponentTopologyDTO[]>('/v1/topology')
}

/**
 * `GET /api/v1/availability/component/{componentId}` (STORY-044/STORY-015d
 * AC1, AC2) — the component-grain rollup plus its per-signal children for
 * the given window. `since`/`until` MUST be tz-aware ISO strings (a
 * trailing `Z`) — the backend 422s naive datetimes;
 * `features/availability/windowRange.ts::windowToRange` is the app's single
 * seam that guarantees this.
 */
export function getComponentAvailability(
  componentId: string,
  range: { since: string; until: string },
): Promise<ComponentAvailabilityDTO> {
  const query = new URLSearchParams({ since: range.since, until: range.until })
  return getJson<ComponentAvailabilityDTO>(
    `/v1/availability/component/${componentId}?${query.toString()}`,
  )
}

/**
 * `GET /api/v1/history` (STORY-014c/STORY-015e AC1, AC2) — newest-first raw
 * observations for exactly ONE signal over a window; NO pagination. `since`/
 * `until` MUST be tz-aware ISO strings (the backend 422s a naive datetime) —
 * reuse `features/availability/windowRange.ts::windowToRange` to build them
 * (the same tz-discipline seam STORY-015d relies on). Because there is no
 * pagination, a wide window can return many thousands of rows; the Check
 * History tab caps what it RENDERS client-side (STORY-015e AC4) — this fetch
 * always requests the full in-window result. The server now also accepts an
 * optional `limit` query param (STORY-094) that caps the response server-side
 * (newest-first); this client deliberately does NOT send it — the render cap
 * below stays the authoritative behavior for this story.
 */
export function getHistory(params: {
  signal_key: string
  since: string
  until: string
}): Promise<ObservationDTO[]> {
  const query = new URLSearchParams(params)
  return getJson<ObservationDTO[]>(`/v1/history?${query.toString()}`)
}

/**
 * `GET /api/v1/publications` (STORY-037/STORY-015g AC1) — recorded
 * Statuspage publishes, newest-first, capped at the repository's most-recent
 * 50 (`list_recent` — no pagination params exist on this endpoint).
 */
export function getPublications(): Promise<PublicationDTO[]> {
  return getJson<PublicationDTO[]>('/v1/publications')
}

/**
 * `GET /api/v1/maintenance` (STORY-036/STORY-015f AC1) — every scheduled
 * maintenance window. No `state` field on the wire; the Maintenance tab
 * derives upcoming/active/past client-side (see
 * `features/maintenance/windowState.ts`).
 */
export function getMaintenance(): Promise<MaintenanceWindowDTO[]> {
  return getJson<MaintenanceWindowDTO[]>('/v1/maintenance')
}

/**
 * `POST /api/v1/maintenance` (STORY-036/STORY-015f AC2) — schedules a new
 * maintenance window and returns the created DTO. `starts_at`/`ends_at`
 * MUST be tz-aware ISO strings — the backend 422s naive datetimes and an
 * empty/whitespace `component_id` (STORY-015f AC3); the rejected
 * `ApiError.detail` carries the raw validation message for inline
 * field-error rendering.
 */
export function postMaintenance(
  body: CreateMaintenanceRequest,
): Promise<MaintenanceWindowDTO> {
  return postJson<MaintenanceWindowDTO, CreateMaintenanceRequest>('/v1/maintenance', body)
}

/**
 * `DELETE /api/v1/maintenance/{id}` (STORY-065 AC3/AC5) — deletes a scheduled
 * maintenance window. Returns 204 (no body) on success, 404 on unknown ID.
 */
export function deleteMaintenance(id: number): Promise<void> {
  return deleteRequest(`/v1/maintenance/${id}`)
}

