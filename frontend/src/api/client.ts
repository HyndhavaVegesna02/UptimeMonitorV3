import type { ComponentDTO } from './types'

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

async function getJson<T>(path: string): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}${path}`)
  } catch {
    throw new ApiError(`Network error while requesting ${path}`)
  }

  if (!response.ok) {
    throw new ApiError(
      `Request to ${path} failed with status ${response.status}`,
      response.status,
    )
  }

  return (await response.json()) as T
}

/** The AC3 proving endpoint: `GET /api/v1/components`. */
export function getComponents(): Promise<ComponentDTO[]> {
  return getJson<ComponentDTO[]>('/v1/components')
}
