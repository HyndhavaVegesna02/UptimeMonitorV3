import type { ComponentDTO, ProposalDTO } from './types'

/**
 * Fetch-based typed API client (STORY-121). Single base-URL seam: every call
 * goes through `API_BASE_URL`, which is `/api` in both dev (proxied by Vite
 * to the local backend — vite.config.ts) and production (same-origin
 * `/api/*`, dossier §17). STORY-122 adds the remaining endpoints (history,
 * availability, maintenance, sample-mode) onto this same seam.
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
