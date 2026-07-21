import { http, HttpResponse } from 'msw'
import type { CreateMaintenanceRequest, MaintenanceWindowDTO } from '../../api/types'

/**
 * `GET /api/v1/maintenance` fixture (STORY-122) — the EXACT real response
 * captured from the running local stack (empty — no windows scheduled),
 * see `docs/scrum/sprints/2026-07-21-sprint-59/live-api-samples.md`.
 */
export const FIXTURE_MAINTENANCE: MaintenanceWindowDTO[] = []


/**
 * Default success handlers (STORY-122, extended STORY-132).
 */
export const maintenanceHandlers = [
  http.get('/api/v1/maintenance', () => {
    return HttpResponse.json(FIXTURE_MAINTENANCE)
  }),
  http.post('/api/v1/maintenance', async ({ request }) => {
    const body = (await request.json()) as CreateMaintenanceRequest
    const newWindow: MaintenanceWindowDTO = {
      id: Date.now(),
      component_id: body.component_id,
      starts_at: body.starts_at,
      ends_at: body.ends_at,
      title: body.title ?? null,
      reason: body.reason ?? null,
    }
    return HttpResponse.json(newWindow, { status: 201 })
  }),
  http.delete('/api/v1/maintenance/:windowId', ({ params }) => {
    const id = Number(params.windowId)
    if (id === 999) {
      return HttpResponse.json({ detail: `window ${id} not found` }, { status: 404 })
    }
    return new HttpResponse(null, { status: 204 })
  }),
]

