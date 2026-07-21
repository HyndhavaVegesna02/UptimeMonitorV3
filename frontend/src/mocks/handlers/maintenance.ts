import { http, HttpResponse } from 'msw'
import type { MaintenanceWindowDTO } from '../../api/types'

/**
 * `GET /api/v1/maintenance` fixture (STORY-122) — the EXACT real response
 * captured from the running local stack (empty — no windows scheduled),
 * see `docs/scrum/sprints/2026-07-21-sprint-59/live-api-samples.md`.
 */
export const FIXTURE_MAINTENANCE: MaintenanceWindowDTO[] = []

/**
 * Default success handler (STORY-122). Tests override with `server.use(...)`
 * for a populated-window scenario or the error path.
 */
export const maintenanceHandlers = [
  http.get('/api/v1/maintenance', () => {
    return HttpResponse.json(FIXTURE_MAINTENANCE)
  }),
]
