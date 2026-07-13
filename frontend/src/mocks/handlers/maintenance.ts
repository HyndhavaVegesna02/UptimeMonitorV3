import { http, HttpResponse } from 'msw'
import type { CreateMaintenanceRequest, MaintenanceWindowDTO } from '../../api/types'

/**
 * Fixtures DERIVED from the sprint-34 plan's pinned live wire sample
 * (2026-07-06 real-sample rule) — `id`/`component_id`/`starts_at`/`ends_at`/
 * `reason` for the first window match the wire sample verbatim
 * (`"http-check"`, `"2026-07-07T10:00:00Z"`..`"2026-07-07T11:00:00Z"`,
 * `"planning-time wire probe"`). A second window with `reason: null` is
 * added to cover the em-dash null-rendering case (STORY-015f AC1,
 * conventions checklist (h)) — the wire sample itself has no null-reason
 * example.
 */
export const FIXTURE_MAINTENANCE_WINDOWS: MaintenanceWindowDTO[] = [
  {
    id: 1,
    component_id: 'http-check',
    starts_at: '2026-07-07T10:00:00Z',
    ends_at: '2026-07-07T11:00:00Z',
    reason: 'planning-time wire probe',
    title: 'Database Upgrade',
  },
  {
    id: 2,
    component_id: 'sockshop-catalogue',
    starts_at: '2026-07-08T00:00:00Z',
    ends_at: '2026-07-08T01:00:00Z',
    reason: null,
    title: null,
  },
]

/**
 * Maintenance feature's default success handlers (STORY-036/STORY-015f AC1,
 * AC2). The POST handler echoes the received body back as the "created" DTO
 * (id `99`, distinct from the GET fixtures' ids) so a test can assert on the
 * exact payload MSW received (AC2) as well as on what the page renders after
 * a successful create. Tests override with `server.use(...)` for the empty/
 * error/422 paths — MSW is the only mocked I/O edge.
 */
export const maintenanceHandlers = [
  http.get('/api/v1/maintenance', () => {
    return HttpResponse.json(FIXTURE_MAINTENANCE_WINDOWS)
  }),
  http.post('/api/v1/maintenance', async ({ request }) => {
    const body = (await request.json()) as CreateMaintenanceRequest
    const created: MaintenanceWindowDTO = {
      id: 99,
      component_id: body.component_id,
      starts_at: body.starts_at,
      ends_at: body.ends_at,
      reason: body.reason ?? null,
      title: body.title ?? null,
    }
    return HttpResponse.json(created, { status: 201 })
  }),
  http.delete('/api/v1/maintenance/:id', ({ params }) => {
    const id = Number(params.id)
    if (id === 999) {
      return HttpResponse.json({ detail: 'Maintenance window not found.' }, { status: 404 })
    }
    return new HttpResponse(null, { status: 204 })
  }),
]
