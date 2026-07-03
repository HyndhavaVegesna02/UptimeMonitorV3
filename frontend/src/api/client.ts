import type {
  ComponentAvailabilityDTO,
  ComponentDTO,
  ComponentTopologyDTO,
  DecisionRequest,
  DecisionResponse,
  ProposalDTO,
} from './types'

/**
 * Fetch-based typed API client (STORY-015a AC3). Single base-URL seam: every
 * call goes through `API_BASE_URL`, which is `/api` in both dev (proxied by
 * Vite to the local backend — vite.config.ts) and production (Vercel
 * rewrites to the Railway backend — dossier §17; wired in a later
 * deployment story).
 */
export const API_BASE_URL = '/api'

export class ApiError extends Error {
  status?: number

  constructor(message: string, status?: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

/**
 * Shared response-reader: maps a settled `fetch` `Response` to parsed JSON or a
 * typed `ApiError`. A non-2xx status → `ApiError` carrying `.status` (so callers
 * can branch on 404/409); a malformed 2xx body → `ApiError` (also with status).
 * Both `getJson`/`postJson` funnel through here so there is ONE parse-error
 * contract for every future tab to inherit (single source of the error shape).
 */
async function readOkJson<T>(response: Response, path: string): Promise<T> {
  if (!response.ok) {
    throw new ApiError(
      `Request to ${path} failed with status ${response.status}`,
      response.status,
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
