import { http, HttpResponse } from 'msw'
import type { SampleModeDTO } from '../../api/types'

/**
 * Default-OFF fixture (STORY-048/STORY-049 AC1) — mirrors the backend's
 * never-set default. TEMPORARY feature — see
 * `docs/scrum/wiki/sample-mode.md`'s REMOVAL inventory.
 */
export const FIXTURE_SAMPLE_MODE_OFF: SampleModeDTO = { enabled: false }

/**
 * Sample-mode feature's default handlers (STORY-049 AC1, AC2). The PUT
 * handler echoes back the requested `enabled` value as the backend's real
 * PUT does (idempotent upsert, returns the new state) — it does not carry
 * state across requests; tests that need a specific starting state override
 * the GET handler with `server.use(...)`, matching the approvals/components
 * convention. MSW is the only mocked I/O edge; nothing mocks the api client
 * or the hook/page itself.
 */
export const sampleModeHandlers = [
  http.get('/api/v1/sample-mode', () => HttpResponse.json(FIXTURE_SAMPLE_MODE_OFF)),
  http.put('/api/v1/sample-mode', async ({ request }) => {
    const body = (await request.json()) as { enabled: boolean }
    const response: SampleModeDTO = { enabled: body.enabled }
    return HttpResponse.json(response)
  }),
]
