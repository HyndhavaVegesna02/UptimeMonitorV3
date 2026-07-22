import { HttpResponse, http } from 'msw'
import { describe, expect, it } from 'vitest'
import { FIXTURE_DECISION_RESPONSE, FIXTURE_PROPOSALS } from '../mocks/handlers/approvals'
import { FIXTURE_AVAILABILITY, FIXTURE_COMPONENT_AVAILABILITY } from '../mocks/handlers/availability'
import { FIXTURE_COMPONENTS } from '../mocks/handlers/components'
import { FIXTURE_HISTORY } from '../mocks/handlers/history'
import { FIXTURE_CREATED_MAINTENANCE_WINDOW, FIXTURE_MAINTENANCE } from '../mocks/handlers/maintenance'
import { FIXTURE_TOPOLOGY } from '../mocks/handlers/topology'
import { server } from '../mocks/server'
import {
  ApiError,
  deleteMaintenance,
  getApprovals,
  getAvailability,
  getComponentAvailability,
  getComponents,
  getHistory,
  getHistoryWindow,
  getMaintenance,
  getTopology,
  postDecision,
  postMaintenance,
} from './client'

describe('getComponents', () => {
  it('resolves the fixture components on success', async () => {
    await expect(getComponents()).resolves.toEqual(FIXTURE_COMPONENTS)
  })

  it('throws an ApiError carrying the status on a non-2xx response', async () => {
    server.use(
      http.get('/api/v1/components', () => HttpResponse.json({ detail: 'boom' }, { status: 500 })),
    )

    await expect(getComponents()).rejects.toMatchObject({
      name: 'ApiError',
      status: 500,
      detail: 'boom',
    })
  })
})

describe('getApprovals', () => {
  it('resolves the fixture proposals on success', async () => {
    await expect(getApprovals()).resolves.toEqual(FIXTURE_PROPOSALS)
  })

  it('resolves an empty array when there are no open proposals', async () => {
    server.use(http.get('/api/v1/approvals', () => HttpResponse.json([])))

    await expect(getApprovals()).resolves.toEqual([])
  })
})

describe('getHistory', () => {
  it('resolves the fixture observations for a known signal_key', async () => {
    await expect(getHistory('http-check')).resolves.toEqual(FIXTURE_HISTORY['http-check'])
  })

  it('resolves an empty array for an unfixtured signal_key rather than another signal\'s data', async () => {
    await expect(getHistory('unknown-signal')).resolves.toEqual([])
  })

  it('sends an optional limit as a query param', async () => {
    let capturedUrl: string | undefined
    server.use(
      http.get('/api/v1/history', ({ request }) => {
        capturedUrl = request.url
        return HttpResponse.json([])
      }),
    )

    await getHistory('http-check', 8)

    expect(capturedUrl).toContain('signal_key=http-check')
    expect(capturedUrl).toContain('limit=8')
  })
})

describe('getHistoryWindow', () => {
  const since = '2026-07-20T18:20:42.000Z'
  const until = '2026-07-21T18:20:42.000Z'

  it('resolves the fixture observations for a known signal_key', async () => {
    await expect(getHistoryWindow({ signal_key: 'http-check', since, until })).resolves.toEqual(
      FIXTURE_HISTORY['http-check'],
    )
  })

  it('resolves an empty array for an unfixtured signal_key', async () => {
    await expect(getHistoryWindow({ signal_key: 'unknown-signal', since, until })).resolves.toEqual([])
  })

  it('sends signal_key/since/until (and an optional limit) as query params', async () => {
    let capturedUrl: string | undefined
    server.use(
      http.get('/api/v1/history', ({ request }) => {
        capturedUrl = request.url
        return HttpResponse.json([])
      }),
    )

    await getHistoryWindow({ signal_key: 'http-check', since, until, limit: 8 })

    expect(capturedUrl).toContain('signal_key=http-check')
    expect(capturedUrl).toContain(`since=${encodeURIComponent(since)}`)
    expect(capturedUrl).toContain(`until=${encodeURIComponent(until)}`)
    expect(capturedUrl).toContain('limit=8')
  })

  it('omits limit entirely when not given', async () => {
    let capturedUrl: string | undefined
    server.use(
      http.get('/api/v1/history', ({ request }) => {
        capturedUrl = request.url
        return HttpResponse.json([])
      }),
    )

    await getHistoryWindow({ signal_key: 'http-check', since, until })

    expect(capturedUrl).not.toContain('limit=')
  })
})

describe('getAvailability', () => {
  it('resolves the fixture availability for a known signal_key', async () => {
    await expect(getAvailability('http-check')).resolves.toEqual(FIXTURE_AVAILABILITY['http-check'])
  })

  it('throws an ApiError on an unfixtured signal_key (mirrors the real 404)', async () => {
    await expect(getAvailability('unknown-signal')).rejects.toMatchObject({
      name: 'ApiError',
      status: 404,
    })
  })
})

describe('getMaintenance', () => {
  it('resolves the fixture maintenance windows', async () => {
    await expect(getMaintenance()).resolves.toEqual(FIXTURE_MAINTENANCE)
  })

  it('resolves an empty array when nothing is scheduled', async () => {
    server.use(http.get('/api/v1/maintenance', () => HttpResponse.json([])))

    await expect(getMaintenance()).resolves.toEqual([])
  })
})

describe('getTopology', () => {
  it('resolves the fixture topology', async () => {
    await expect(getTopology()).resolves.toEqual(FIXTURE_TOPOLOGY)
  })
})

describe('getComponentAvailability', () => {
  const since = '2026-07-20T18:20:42.000Z'
  const until = '2026-07-21T18:20:42.000Z'

  it('resolves the fixture component-grain availability for a known component id', async () => {
    await expect(getComponentAvailability('http-check', { since, until })).resolves.toEqual(
      FIXTURE_COMPONENT_AVAILABILITY['http-check'],
    )
  })

  it('sends since/until as query params', async () => {
    let capturedUrl: string | undefined
    server.use(
      http.get('/api/v1/availability/component/:componentId', ({ request }) => {
        capturedUrl = request.url
        return HttpResponse.json(FIXTURE_COMPONENT_AVAILABILITY['http-check'])
      }),
    )

    await getComponentAvailability('http-check', { since, until })

    expect(capturedUrl).toContain(`since=${encodeURIComponent(since)}`)
    expect(capturedUrl).toContain(`until=${encodeURIComponent(until)}`)
  })

  it('throws an ApiError on an unknown component id (mirrors the real 404)', async () => {
    await expect(getComponentAvailability('unknown-component', { since, until })).rejects.toMatchObject({
      name: 'ApiError',
      status: 404,
    })
  })
})

describe('postDecision', () => {
  it('resolves the fixture DecisionResponse on success', async () => {
    await expect(postDecision(1, { action: 'approve', actor: 'dashboard-operator' })).resolves.toEqual(
      FIXTURE_DECISION_RESPONSE,
    )
  })

  it('POSTs a JSON body with Content-Type: application/json to /v1/decisions/{proposal_id}', async () => {
    let capturedUrl: string | undefined
    let capturedMethod: string | undefined
    let capturedContentType: string | null = null
    let capturedBody: unknown
    server.use(
      http.post('/api/v1/decisions/:proposalId', async ({ request }) => {
        capturedUrl = request.url
        capturedMethod = request.method
        capturedContentType = request.headers.get('content-type')
        capturedBody = await request.json()
        return HttpResponse.json(FIXTURE_DECISION_RESPONSE)
      }),
    )

    await postDecision(7, { action: 'reject', actor: 'dashboard-operator', notes: 'flaky check' })

    expect(capturedUrl).toContain('/v1/decisions/7')
    expect(capturedMethod).toBe('POST')
    expect(capturedContentType).toContain('application/json')
    expect(capturedBody).toEqual({ action: 'reject', actor: 'dashboard-operator', notes: 'flaky check' })
  })

  it('throws an ApiError carrying status 409 (proposal not open / lost race / double-submit)', async () => {
    server.use(
      http.post('/api/v1/decisions/:proposalId', () =>
        HttpResponse.json({ detail: 'Proposal is not open' }, { status: 409 }),
      ),
    )

    await expect(postDecision(1, { action: 'approve', actor: 'dashboard-operator' })).rejects.toMatchObject({
      name: 'ApiError',
      status: 409,
      detail: 'Proposal is not open',
    })
  })

  it('throws an ApiError carrying status 404 (proposal no longer exists)', async () => {
    server.use(
      http.post('/api/v1/decisions/:proposalId', () =>
        HttpResponse.json({ detail: 'Proposal not found' }, { status: 404 }),
      ),
    )

    await expect(postDecision(999, { action: 'reject', actor: 'dashboard-operator' })).rejects.toMatchObject({
      name: 'ApiError',
      status: 404,
      detail: 'Proposal not found',
    })
  })
})

describe('postMaintenance', () => {
  it('resolves the fixture created window on a 201 success', async () => {
    await expect(
      postMaintenance({
        component_id: 'http-check',
        starts_at: '2026-07-22T00:00:00Z',
        ends_at: '2026-07-22T02:00:00Z',
        reason: 'DB upgrade',
        title: 'Planned DB maintenance',
      }),
    ).resolves.toEqual(FIXTURE_CREATED_MAINTENANCE_WINDOW)
  })

  it('POSTs a JSON body with Content-Type: application/json to /v1/maintenance', async () => {
    let capturedUrl: string | undefined
    let capturedMethod: string | undefined
    let capturedContentType: string | null = null
    let capturedBody: unknown
    server.use(
      http.post('/api/v1/maintenance', async ({ request }) => {
        capturedUrl = request.url
        capturedMethod = request.method
        capturedContentType = request.headers.get('content-type')
        capturedBody = await request.json()
        return HttpResponse.json(FIXTURE_CREATED_MAINTENANCE_WINDOW, { status: 201 })
      }),
    )

    await postMaintenance({
      component_id: 'http-check',
      starts_at: '2026-07-22T00:00:00Z',
      ends_at: '2026-07-22T02:00:00Z',
    })

    expect(capturedUrl).toContain('/v1/maintenance')
    expect(capturedMethod).toBe('POST')
    expect(capturedContentType).toContain('application/json')
    expect(capturedBody).toEqual({
      component_id: 'http-check',
      starts_at: '2026-07-22T00:00:00Z',
      ends_at: '2026-07-22T02:00:00Z',
    })
  })

  it('throws an ApiError carrying the 422 detail string (end-before-start)', async () => {
    server.use(
      http.post('/api/v1/maintenance', () =>
        HttpResponse.json({ detail: 'ends_at must be strictly greater than starts_at.' }, { status: 422 }),
      ),
    )

    await expect(
      postMaintenance({
        component_id: 'http-check',
        starts_at: '2026-07-22T02:00:00Z',
        ends_at: '2026-07-22T00:00:00Z',
      }),
    ).rejects.toMatchObject({
      name: 'ApiError',
      status: 422,
      detail: 'ends_at must be strictly greater than starts_at.',
    })
  })
})

describe('deleteMaintenance', () => {
  it('resolves (void) on a 204 success, without attempting to parse a body', async () => {
    await expect(deleteMaintenance(4)).resolves.toBeUndefined()
  })

  it('sends a DELETE to /v1/maintenance/{window_id}', async () => {
    let capturedUrl: string | undefined
    let capturedMethod: string | undefined
    server.use(
      http.delete('/api/v1/maintenance/:windowId', ({ request }) => {
        capturedUrl = request.url
        capturedMethod = request.method
        return new HttpResponse(null, { status: 204 })
      }),
    )

    await deleteMaintenance(4)

    expect(capturedUrl).toContain('/v1/maintenance/4')
    expect(capturedMethod).toBe('DELETE')
  })

  it('throws an ApiError carrying status 404 (already gone — delete is not idempotent)', async () => {
    server.use(
      http.delete('/api/v1/maintenance/:windowId', () =>
        HttpResponse.json({ detail: 'Maintenance window not found' }, { status: 404 }),
      ),
    )

    await expect(deleteMaintenance(999)).rejects.toMatchObject({
      name: 'ApiError',
      status: 404,
      detail: 'Maintenance window not found',
    })
  })
})

describe('ApiError', () => {
  it('is a real Error subclass', () => {
    const err = new ApiError('boom', 404, 'not found')
    expect(err).toBeInstanceOf(Error)
    expect(err.status).toBe(404)
    expect(err.detail).toBe('not found')
  })
})
