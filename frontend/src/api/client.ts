import type {
  AvailabilityDTO,
  ComponentAvailabilityDTO,
  ComponentDTO,
  ComponentTopologyDTO,
  MaintenanceWindowDTO,
  ObservationDTO,
  ProposalDTO,
} from './types'

/**
 * Fetch-based typed API client (STORY-121). Single base-URL seam: every call
 * goes through `API_BASE_URL`, which is `/api` in both dev (proxied by Vite
 * to the local backend — vite.config.ts) and production (same-origin
 * `/api/*`, dossier §17). STORY-122 adds the Dashboard's remaining endpoints
 * (history, availability, maintenance) onto this same seam.
 */
export const API_BASE_URL = '/api'

export class ApiError extends Error {
  status?: number
  /**
   * The backend's raw `detail` string, when the non-2xx body parsed as
   * `{ detail: string }` (FastAPI's shape for a manually-raised
   * `HTTPException`). `undefined` for network failures, malformed bodies, or
   * a body without a string `detail`.
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
 * `HTTPException` shape) from a non-ok response. Uses `.clone()` so the
 * original `response` is left readable by any other caller. Never throws.
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
 * Shared response-reader: maps a settled `fetch` `Response` to parsed JSON
 * or a typed `ApiError`. A non-2xx status -> `ApiError` carrying `.status`
 * and, when present, `.detail`; a malformed 2xx body -> `ApiError` (also
 * with status).
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

/** `GET /api/v1/components` — the sidebar's Pinned quick-links and the
 * topbar's worst-of overall status pill both derive from this. */
export function getComponents(): Promise<ComponentDTO[]> {
  return getJson<ComponentDTO[]>('/v1/components')
}

/** `GET /api/v1/approvals` — the sidebar's Approvals badge count is this
 * array's length (STORY-121 AC2). */
export function getApprovals(): Promise<ProposalDTO[]> {
  return getJson<ProposalDTO[]>('/v1/approvals')
}

/** `GET /api/v1/history?signal_key=...&limit=...` (STORY-122) — per-signal
 * observation history, most-recent first. `limit` is an optional
 * server-side cap (`backend/src/api/v1/history/controller.py`); omitted,
 * the backend returns the full window. */
export function getHistory(signalKey: string, limit?: number): Promise<ObservationDTO[]> {
  const params = new URLSearchParams({ signal_key: signalKey })
  if (limit !== undefined) {
    params.set('limit', String(limit))
  }
  return getJson<ObservationDTO[]>(`/v1/history?${params.toString()}`)
}

/** `GET /api/v1/availability?signal_key=...` (STORY-122) — per-signal
 * availability%/completeness% over the default 24h window.
 * `availability_pct`/`completeness_pct` may be `null` for a degenerate
 * (no-data) window — callers must handle that, never invent a number. */
export function getAvailability(signalKey: string): Promise<AvailabilityDTO> {
  const params = new URLSearchParams({ signal_key: signalKey })
  return getJson<AvailabilityDTO>(`/v1/availability?${params.toString()}`)
}

/** `GET /api/v1/maintenance` (STORY-122) — every scheduled maintenance
 * window, no filtering params (`backend/src/api/v1/maintenance/controller.py`). */
export function getMaintenance(): Promise<MaintenanceWindowDTO[]> {
  return getJson<MaintenanceWindowDTO[]>('/v1/maintenance')
}

/** `GET /api/v1/topology` (STORY-129) — every component and its nested
 * signals (name + interval), the join source for the `signal_key`-only
 * `SignalAvailabilityDTO` children `getComponentAvailability` returns. */
export function getTopology(): Promise<ComponentTopologyDTO[]> {
  return getJson<ComponentTopologyDTO[]>('/v1/topology')
}

/** `GET /api/v1/availability/component/{component_id}` (STORY-129) — the
 * component-grain rollup plus its nested per-signal children, over the
 * `[since, until)` window. `since`/`until` MUST be tz-aware UTC ISO strings
 * (trailing `Z`, e.g. `Date.prototype.toISOString()`) — the backend 422s a
 * naive datetime. */
export function getComponentAvailability(
  componentId: string,
  { since, until }: { since: string; until: string },
): Promise<ComponentAvailabilityDTO> {
  const params = new URLSearchParams({ since, until })
  return getJson<ComponentAvailabilityDTO>(
    `/v1/availability/component/${encodeURIComponent(componentId)}?${params.toString()}`,
  )
}
