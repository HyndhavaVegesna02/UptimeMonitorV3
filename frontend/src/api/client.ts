import type {
  AvailabilityDTO,
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
      if (typeof detail === 'string') {
        return detail
      }
      if (Array.isArray(detail)) {
        return detail
          .map((item) =>
            typeof item === 'object' && item && 'msg' in item
              ? String((item as { msg: unknown }).msg)
              : JSON.stringify(item),
          )
          .join('; ')
      }
      if (detail && typeof detail === 'object') {
        return JSON.stringify(detail)
      }
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

async function postJson<TBody, TResult>(path: string, body: TBody): Promise<TResult> {
  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
  } catch {
    throw new ApiError(`Network error while posting to ${path}`)
  }

  return readOkJson<TResult>(response, path)
}

async function deleteRequest(path: string): Promise<void> {
  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method: 'DELETE',
    })
  } catch {
    throw new ApiError(`Network error while deleting ${path}`)
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

/** `GET /api/v1/components` */
export function getComponents(): Promise<ComponentDTO[]> {
  return getJson<ComponentDTO[]>('/v1/components')
}

/** `GET /api/v1/topology` (STORY-129) */
export function getTopology(): Promise<ComponentTopologyDTO[]> {
  return getJson<ComponentTopologyDTO[]>('/v1/topology')
}

/** `GET /api/v1/approvals` */
export function getApprovals(): Promise<ProposalDTO[]> {
  return getJson<ProposalDTO[]>('/v1/approvals')
}

export interface GetHistoryParams {
  signalKey?: string
  since?: string
  until?: string
  limit?: number
}

/** `GET /api/v1/history` (STORY-122, extended STORY-130) */
export function getHistory(
  signalKeyOrParams: string | GetHistoryParams,
  limitLegacy?: number,
): Promise<ObservationDTO[]> {
  const params = new URLSearchParams()
  if (typeof signalKeyOrParams === 'string') {
    params.set('signal_key', signalKeyOrParams)
    if (limitLegacy !== undefined) {
      params.set('limit', String(limitLegacy))
    }
  } else {
    if (signalKeyOrParams.signalKey) {
      params.set('signal_key', signalKeyOrParams.signalKey)
    }
    if (signalKeyOrParams.since) {
      params.set('since', signalKeyOrParams.since)
    }
    if (signalKeyOrParams.until) {
      params.set('until', signalKeyOrParams.until)
    }
    if (signalKeyOrParams.limit !== undefined) {
      params.set('limit', String(signalKeyOrParams.limit))
    }
  }
  const queryString = params.toString()
  return getJson<ObservationDTO[]>(`/v1/history${queryString ? `?${queryString}` : ''}`)
}

/** `GET /api/v1/availability` */
export function getAvailability(signalKey: string): Promise<AvailabilityDTO> {
  const params = new URLSearchParams({ signal_key: signalKey })
  return getJson<AvailabilityDTO>(`/v1/availability?${params.toString()}`)
}

export interface GetAvailabilityOptions {
  since?: string
  until?: string
}

/** `GET /api/v1/availability/component/{id}` (STORY-129) */
export function getComponentAvailability(
  componentId: string,
  options?: GetAvailabilityOptions,
): Promise<ComponentAvailabilityDTO> {
  const params = new URLSearchParams()
  if (options?.since) params.set('since', options.since)
  if (options?.until) params.set('until', options.until)
  const query = params.toString()
  return getJson<ComponentAvailabilityDTO>(
    `/v1/availability/component/${encodeURIComponent(componentId)}${query ? `?${query}` : ''}`,
  )
}

/** `GET /api/v1/maintenance` */
export function getMaintenance(): Promise<MaintenanceWindowDTO[]> {
  return getJson<MaintenanceWindowDTO[]>('/v1/maintenance')
}

/** `POST /api/v1/decisions/{proposal_id}` (STORY-131) */
export function postDecision(
  proposalId: number,
  body: DecisionRequest,
): Promise<DecisionResponse> {
  return postJson<DecisionRequest, DecisionResponse>(`/v1/decisions/${proposalId}`, body)
}

/** `POST /api/v1/maintenance` (STORY-132) */
export function postMaintenance(
  body: CreateMaintenanceRequest,
): Promise<MaintenanceWindowDTO> {
  return postJson<CreateMaintenanceRequest, MaintenanceWindowDTO>('/v1/maintenance', body)
}

/** `DELETE /api/v1/maintenance/{window_id}` (STORY-132) */
export function deleteMaintenance(windowId: number): Promise<void> {
  return deleteRequest(`/v1/maintenance/${windowId}`)
}

/** `GET /api/v1/publications` (STORY-133) */
export function getPublications(): Promise<PublicationDTO[]> {
  return getJson<PublicationDTO[]>('/v1/publications')
}

