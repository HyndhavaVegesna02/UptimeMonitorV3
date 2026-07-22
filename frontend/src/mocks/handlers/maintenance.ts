import { http, HttpResponse } from 'msw'
import type { MaintenanceWindowDTO } from '../../api/types'

/**
 * `GET /api/v1/maintenance` fixture (STORY-122) — the EXACT real response
 * captured from the running local stack (empty — no windows scheduled),
 * see `docs/scrum/sprints/2026-07-21-sprint-59/live-api-samples.md`.
 */
export const FIXTURE_MAINTENANCE: MaintenanceWindowDTO[] = []

/**
 * A populated list spanning upcoming/active/past (STORY-132 AC1's badge
 * test). Shape is the plan appendix's illustrative `MaintenanceWindowDTO`
 * sample; instants are pinned far from "now" (year 2000/2099) so the
 * derived state is stable regardless of when the suite runs —
 * `deriveMaintenanceWindowState` itself is unit-tested against exact
 * boundary instants separately (`deriveWindowState.test.ts`).
 */
export const FIXTURE_MAINTENANCE_WINDOWS: MaintenanceWindowDTO[] = [
  {
    id: 1,
    component_id: 'http-check',
    starts_at: '2099-01-01T00:00:00Z',
    ends_at: '2099-01-01T02:00:00Z',
    reason: 'DB upgrade',
    title: 'Planned DB maintenance',
  },
  {
    id: 2,
    component_id: 'http-check',
    starts_at: '2000-01-01T00:00:00Z',
    ends_at: '2099-01-01T00:00:00Z',
    reason: null,
    title: null,
  },
  {
    id: 3,
    component_id: 'http-check',
    starts_at: '2000-01-01T00:00:00Z',
    ends_at: '2000-01-01T02:00:00Z',
    reason: 'Completed patch',
    title: 'Past patch window',
  },
]

/** `POST /api/v1/maintenance` 201 fixture (STORY-132). */
export const FIXTURE_CREATED_MAINTENANCE_WINDOW: MaintenanceWindowDTO = {
  id: 4,
  component_id: 'http-check',
  starts_at: '2026-07-22T00:00:00Z',
  ends_at: '2026-07-22T02:00:00Z',
  reason: 'DB upgrade',
  title: 'Planned DB maintenance',
}

/**
 * Default success handlers (STORY-122, extended STORY-132 with the write
 * path). Tests override with `server.use(...)` for the populated-list, 422,
 * and 404 paths.
 */
export const maintenanceHandlers = [
  http.get('/api/v1/maintenance', () => {
    return HttpResponse.json(FIXTURE_MAINTENANCE)
  }),
  http.post('/api/v1/maintenance', () => {
    return HttpResponse.json(FIXTURE_CREATED_MAINTENANCE_WINDOW, { status: 201 })
  }),
  http.delete('/api/v1/maintenance/:windowId', () => {
    return new HttpResponse(null, { status: 204 })
  }),
]
