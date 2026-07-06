import { HttpResponse, http } from 'msw'
import { describe, expect, it } from 'vitest'
import { server } from '../mocks/server'
import {
  FIXTURE_AVAILABILITY_BY_COMPONENT,
  FIXTURE_COMPONENTS,
  FIXTURE_HISTORY_FRONTEND_HTTP,
  FIXTURE_MAINTENANCE_WINDOWS,
  FIXTURE_PROPOSALS,
  FIXTURE_PUBLICATIONS,
  FIXTURE_TOPOLOGY,
} from '../mocks/handlers'
import {
  ApiError,
  getApprovals,
  getComponentAvailability,
  getComponents,
  getHistory,
  getMaintenance,
  getPublications,
  getSampleMode,
  getTopology,
  postDecision,
  postMaintenance,
  putSampleMode,
} from './client'

describe('getComponents', () => {
  it('fetches and parses the component list from /api/v1/components', async () => {
    const components = await getComponents()
    expect(components).toEqual(FIXTURE_COMPONENTS)
  })

  it('returns an empty array when the backend has no components', async () => {
    server.use(
      http.get('/api/v1/components', () => HttpResponse.json([])),
    )
    const components = await getComponents()
    expect(components).toEqual([])
  })

  it('throws a typed ApiError on a non-2xx response', async () => {
    server.use(
      http.get('/api/v1/components', () =>
        HttpResponse.json({ detail: 'boom' }, { status: 500 }),
      ),
    )

    await expect(getComponents()).rejects.toBeInstanceOf(ApiError)
    await expect(getComponents()).rejects.toMatchObject({ status: 500 })
  })

  it('carries the backend detail string on the thrown ApiError (STORY-015f AC3)', async () => {
    server.use(
      http.get('/api/v1/components', () =>
        HttpResponse.json({ detail: 'boom' }, { status: 500 }),
      ),
    )

    await expect(getComponents()).rejects.toMatchObject({ detail: 'boom' })
  })

  it('leaves ApiError.detail undefined when the non-ok body has no detail string', async () => {
    server.use(
      http.get('/api/v1/components', () => HttpResponse.json({}, { status: 500 })),
    )

    await expect(getComponents()).rejects.toMatchObject({ detail: undefined })
  })

  it('throws a typed ApiError on a network failure', async () => {
    server.use(http.get('/api/v1/components', () => HttpResponse.error()))

    await expect(getComponents()).rejects.toBeInstanceOf(ApiError)
  })

  it('throws a typed ApiError when a 2xx response body is not valid JSON', async () => {
    server.use(
      http.get('/api/v1/components', () => HttpResponse.text('not json')),
    )

    await expect(getComponents()).rejects.toBeInstanceOf(ApiError)
    await expect(getComponents()).rejects.not.toBeInstanceOf(SyntaxError)
  })
})

describe('getApprovals', () => {
  it('fetches and parses the open-proposal list from /api/v1/approvals', async () => {
    const proposals = await getApprovals()
    expect(proposals).toEqual(FIXTURE_PROPOSALS)
  })

  it('throws a typed ApiError on a non-2xx response', async () => {
    server.use(
      http.get('/api/v1/approvals', () =>
        HttpResponse.json({ detail: 'boom' }, { status: 500 }),
      ),
    )

    await expect(getApprovals()).rejects.toBeInstanceOf(ApiError)
    await expect(getApprovals()).rejects.toMatchObject({ status: 500 })
  })
})

describe('postDecision', () => {
  it('POSTs the decision body and parses the DecisionResponse on success', async () => {
    let receivedBody: unknown
    server.use(
      http.post('/api/v1/decisions/:proposalId', async ({ request, params }) => {
        receivedBody = await request.json()
        return HttpResponse.json({
          proposal_id: Number(params.proposalId),
          state: 'approved',
          resolved_at: '2026-07-02T09:00:00Z',
        })
      }),
    )

    const result = await postDecision(1, { action: 'approve', actor: 'dashboard-operator' })

    expect(receivedBody).toEqual({ action: 'approve', actor: 'dashboard-operator' })
    expect(result).toEqual({
      proposal_id: 1,
      state: 'approved',
      resolved_at: '2026-07-02T09:00:00Z',
    })
  })

  it('throws a typed ApiError carrying status 409 on a lost-race conflict', async () => {
    server.use(
      http.post('/api/v1/decisions/:proposalId', () =>
        HttpResponse.json({ detail: 'not open' }, { status: 409 }),
      ),
    )

    await expect(
      postDecision(1, { action: 'approve', actor: 'dashboard-operator' }),
    ).rejects.toMatchObject({ status: 409 })
  })

  it('throws a typed ApiError carrying status 404 when the proposal is gone', async () => {
    server.use(
      http.post('/api/v1/decisions/:proposalId', () =>
        HttpResponse.json({ detail: 'not found' }, { status: 404 }),
      ),
    )

    await expect(
      postDecision(1, { action: 'approve', actor: 'dashboard-operator' }),
    ).rejects.toMatchObject({ status: 404 })
  })

  it('throws a typed ApiError on a network failure', async () => {
    server.use(http.post('/api/v1/decisions/:proposalId', () => HttpResponse.error()))

    await expect(
      postDecision(1, { action: 'approve', actor: 'dashboard-operator' }),
    ).rejects.toBeInstanceOf(ApiError)
  })

  it('throws a typed ApiError when a 2xx response body is not valid JSON', async () => {
    server.use(
      http.post('/api/v1/decisions/:proposalId', () => HttpResponse.text('not json')),
    )

    await expect(
      postDecision(1, { action: 'approve', actor: 'dashboard-operator' }),
    ).rejects.toBeInstanceOf(ApiError)
  })
})

describe('getTopology', () => {
  it('fetches and parses the component+signals list from /api/v1/topology', async () => {
    const topology = await getTopology()
    expect(topology).toEqual(FIXTURE_TOPOLOGY)
  })

  it('returns an empty array when the topology has no components', async () => {
    server.use(http.get('/api/v1/topology', () => HttpResponse.json([])))
    const topology = await getTopology()
    expect(topology).toEqual([])
  })

  it('throws a typed ApiError on a non-2xx response', async () => {
    server.use(
      http.get('/api/v1/topology', () =>
        HttpResponse.json({ detail: 'boom' }, { status: 500 }),
      ),
    )

    await expect(getTopology()).rejects.toBeInstanceOf(ApiError)
    await expect(getTopology()).rejects.toMatchObject({ status: 500 })
  })

  it('throws a typed ApiError on a network failure', async () => {
    server.use(http.get('/api/v1/topology', () => HttpResponse.error()))

    await expect(getTopology()).rejects.toBeInstanceOf(ApiError)
  })
})

describe('getComponentAvailability', () => {
  it('fetches ComponentAvailabilityDTO and sends since/until as query params', async () => {
    let receivedUrl: URL | undefined
    server.use(
      http.get('/api/v1/availability/component/:componentId', ({ request, params }) => {
        receivedUrl = new URL(request.url)
        const dto = FIXTURE_AVAILABILITY_BY_COMPONENT[params.componentId as string]
        return HttpResponse.json(dto)
      }),
    )

    const range = { since: '2026-07-02T00:00:00.000Z', until: '2026-07-03T00:00:00.000Z' }
    const result = await getComponentAvailability('sockshop-frontend', range)

    expect(receivedUrl?.pathname).toBe('/api/v1/availability/component/sockshop-frontend')
    expect(receivedUrl?.searchParams.get('since')).toBe(range.since)
    expect(receivedUrl?.searchParams.get('until')).toBe(range.until)
    expect(result).toEqual(FIXTURE_AVAILABILITY_BY_COMPONENT['sockshop-frontend'])
  })

  it('fetches the zero-signal component with its all-None rollup honestly', async () => {
    const range = { since: '2026-07-02T00:00:00.000Z', until: '2026-07-03T00:00:00.000Z' }
    const result = await getComponentAvailability('sockshop-orders', range)

    expect(result.signals).toEqual([])
    expect(result.rollup.availability_pct).toBeNull()
    expect(result.rollup.completeness_pct).toBeNull()
  })

  it('throws a typed ApiError carrying status 404 for an unknown component', async () => {
    const range = { since: '2026-07-02T00:00:00.000Z', until: '2026-07-03T00:00:00.000Z' }

    await expect(
      getComponentAvailability('does-not-exist', range),
    ).rejects.toMatchObject({ status: 404 })
  })

  it('throws a typed ApiError on a network failure', async () => {
    server.use(
      http.get('/api/v1/availability/component/:componentId', () => HttpResponse.error()),
    )

    await expect(
      getComponentAvailability('sockshop-frontend', {
        since: '2026-07-02T00:00:00.000Z',
        until: '2026-07-03T00:00:00.000Z',
      }),
    ).rejects.toBeInstanceOf(ApiError)
  })
})

describe('getHistory', () => {
  it('fetches ObservationDTO[] and sends signal_key/since/until as query params', async () => {
    let receivedUrl: URL | undefined
    server.use(
      http.get('/api/v1/history', ({ request }) => {
        receivedUrl = new URL(request.url)
        return HttpResponse.json(FIXTURE_HISTORY_FRONTEND_HTTP)
      }),
    )

    const params = {
      signal_key: 'frontend-http',
      since: '2026-07-02T13:29:17.931000Z',
      until: '2026-07-03T13:29:17.931000Z',
    }
    const result = await getHistory(params)

    expect(receivedUrl?.pathname).toBe('/api/v1/history')
    expect(receivedUrl?.searchParams.get('signal_key')).toBe(params.signal_key)
    expect(receivedUrl?.searchParams.get('since')).toBe(params.since)
    expect(receivedUrl?.searchParams.get('until')).toBe(params.until)
    expect(result).toEqual(FIXTURE_HISTORY_FRONTEND_HTTP)
  })

  it('fetches the default fixture from /api/v1/history newest-first', async () => {
    const result = await getHistory({
      signal_key: 'frontend-http',
      since: '2026-07-02T13:29:17.931000Z',
      until: '2026-07-03T13:29:17.931000Z',
    })
    expect(result).toEqual(FIXTURE_HISTORY_FRONTEND_HTTP)
  })

  it('returns an empty array when the signal has no observations in the window', async () => {
    const result = await getHistory({
      signal_key: 'does-not-exist',
      since: '2026-07-02T13:29:17.931000Z',
      until: '2026-07-03T13:29:17.931000Z',
    })
    expect(result).toEqual([])
  })

  it('throws a typed ApiError on a non-2xx response', async () => {
    server.use(
      http.get('/api/v1/history', () =>
        HttpResponse.json({ detail: 'boom' }, { status: 422 }),
      ),
    )

    await expect(
      getHistory({
        signal_key: 'frontend-http',
        since: '2026-07-02T13:29:17.931000Z',
        until: '2026-07-03T13:29:17.931000Z',
      }),
    ).rejects.toBeInstanceOf(ApiError)
    await expect(
      getHistory({
        signal_key: 'frontend-http',
        since: '2026-07-02T13:29:17.931000Z',
        until: '2026-07-03T13:29:17.931000Z',
      }),
    ).rejects.toMatchObject({ status: 422 })
  })

  it('throws a typed ApiError on a network failure', async () => {
    server.use(http.get('/api/v1/history', () => HttpResponse.error()))

    await expect(
      getHistory({
        signal_key: 'frontend-http',
        since: '2026-07-02T13:29:17.931000Z',
        until: '2026-07-03T13:29:17.931000Z',
      }),
    ).rejects.toBeInstanceOf(ApiError)
  })

  it('throws a typed ApiError when a 2xx response body is not valid JSON', async () => {
    server.use(http.get('/api/v1/history', () => HttpResponse.text('not json')))

    await expect(
      getHistory({
        signal_key: 'frontend-http',
        since: '2026-07-02T13:29:17.931000Z',
        until: '2026-07-03T13:29:17.931000Z',
      }),
    ).rejects.toBeInstanceOf(ApiError)
  })
})

describe('getSampleMode', () => {
  it('fetches and parses the current flag state from /api/v1/sample-mode', async () => {
    const result = await getSampleMode()
    expect(result).toEqual({ enabled: false })
  })

  it('throws a typed ApiError on a non-2xx response', async () => {
    server.use(
      http.get('/api/v1/sample-mode', () =>
        HttpResponse.json({ detail: 'boom' }, { status: 500 }),
      ),
    )

    await expect(getSampleMode()).rejects.toBeInstanceOf(ApiError)
    await expect(getSampleMode()).rejects.toMatchObject({ status: 500 })
  })

  it('throws a typed ApiError on a network failure', async () => {
    server.use(http.get('/api/v1/sample-mode', () => HttpResponse.error()))

    await expect(getSampleMode()).rejects.toBeInstanceOf(ApiError)
  })
})

describe('putSampleMode', () => {
  it('PUTs { enabled } and parses the resulting SampleModeDTO', async () => {
    let receivedBody: unknown
    server.use(
      http.put('/api/v1/sample-mode', async ({ request }) => {
        receivedBody = await request.json()
        return HttpResponse.json({ enabled: true })
      }),
    )

    const result = await putSampleMode(true)

    expect(receivedBody).toEqual({ enabled: true })
    expect(result).toEqual({ enabled: true })
  })

  it('throws a typed ApiError on a non-2xx response', async () => {
    server.use(
      http.put('/api/v1/sample-mode', () =>
        HttpResponse.json({ detail: 'boom' }, { status: 500 }),
      ),
    )

    await expect(putSampleMode(true)).rejects.toMatchObject({ status: 500 })
  })

  it('throws a typed ApiError on a network failure', async () => {
    server.use(http.put('/api/v1/sample-mode', () => HttpResponse.error()))

    await expect(putSampleMode(true)).rejects.toBeInstanceOf(ApiError)
  })

  it('throws a typed ApiError when a 2xx response body is not valid JSON', async () => {
    server.use(http.put('/api/v1/sample-mode', () => HttpResponse.text('not json')))

    await expect(putSampleMode(true)).rejects.toBeInstanceOf(ApiError)
  })
})

describe('getPublications', () => {
  it('fetches and parses the publication list from /api/v1/publications', async () => {
    const publications = await getPublications()
    expect(publications).toEqual(FIXTURE_PUBLICATIONS)
  })

  it('returns an empty array when nothing has been published yet', async () => {
    server.use(http.get('/api/v1/publications', () => HttpResponse.json([])))

    const publications = await getPublications()
    expect(publications).toEqual([])
  })

  it('throws a typed ApiError on a non-2xx response', async () => {
    server.use(
      http.get('/api/v1/publications', () =>
        HttpResponse.json({ detail: 'boom' }, { status: 500 }),
      ),
    )

    await expect(getPublications()).rejects.toBeInstanceOf(ApiError)
    await expect(getPublications()).rejects.toMatchObject({ status: 500 })
  })

  it('throws a typed ApiError on a network failure', async () => {
    server.use(http.get('/api/v1/publications', () => HttpResponse.error()))

    await expect(getPublications()).rejects.toBeInstanceOf(ApiError)
  })

  it('throws a typed ApiError when a 2xx response body is not valid JSON', async () => {
    server.use(http.get('/api/v1/publications', () => HttpResponse.text('not json')))

    await expect(getPublications()).rejects.toBeInstanceOf(ApiError)
    await expect(getPublications()).rejects.not.toBeInstanceOf(SyntaxError)
  })
})

describe('getMaintenance', () => {
  it('fetches and parses the maintenance window list from /api/v1/maintenance', async () => {
    const windows = await getMaintenance()
    expect(windows).toEqual(FIXTURE_MAINTENANCE_WINDOWS)
  })

  it('returns an empty array when nothing is scheduled', async () => {
    server.use(http.get('/api/v1/maintenance', () => HttpResponse.json([])))

    const windows = await getMaintenance()
    expect(windows).toEqual([])
  })

  it('throws a typed ApiError on a non-2xx response', async () => {
    server.use(
      http.get('/api/v1/maintenance', () =>
        HttpResponse.json({ detail: 'boom' }, { status: 500 }),
      ),
    )

    await expect(getMaintenance()).rejects.toBeInstanceOf(ApiError)
    await expect(getMaintenance()).rejects.toMatchObject({ status: 500 })
  })

  it('throws a typed ApiError on a network failure', async () => {
    server.use(http.get('/api/v1/maintenance', () => HttpResponse.error()))

    await expect(getMaintenance()).rejects.toBeInstanceOf(ApiError)
  })
})

describe('postMaintenance', () => {
  it('POSTs a tz-aware, well-formed body and parses the created DTO (AC2)', async () => {
    let receivedBody: unknown
    server.use(
      http.post('/api/v1/maintenance', async ({ request }) => {
        receivedBody = await request.json()
        return HttpResponse.json(
          {
            id: 42,
            component_id: 'checkout',
            starts_at: '2026-07-07T10:00:00.000Z',
            ends_at: '2026-07-07T11:00:00.000Z',
            reason: 'Database migration',
          },
          { status: 201 },
        )
      }),
    )

    const payload = {
      component_id: 'checkout',
      starts_at: '2026-07-07T10:00:00.000Z',
      ends_at: '2026-07-07T11:00:00.000Z',
      reason: 'Database migration',
    }
    const result = await postMaintenance(payload)

    expect(receivedBody).toEqual(payload)
    // The exact assertion AC2 names: the payload the handler received is
    // tz-aware (trailing Z) and well-formed (parses to a valid Date).
    const receivedStartsAt = (receivedBody as { starts_at: string }).starts_at
    expect(receivedStartsAt.endsWith('Z')).toBe(true)
    expect(Number.isNaN(new Date(receivedStartsAt).getTime())).toBe(false)
    expect(result).toEqual({
      id: 42,
      component_id: 'checkout',
      starts_at: '2026-07-07T10:00:00.000Z',
      ends_at: '2026-07-07T11:00:00.000Z',
      reason: 'Database migration',
    })
  })

  it('throws a typed ApiError carrying status 422 and the detail message on invalid input (AC3)', async () => {
    server.use(
      http.post('/api/v1/maintenance', () =>
        HttpResponse.json({ detail: 'starts_at must be timezone-aware.' }, { status: 422 }),
      ),
    )

    await expect(
      postMaintenance({
        component_id: 'checkout',
        starts_at: '2026-07-07T10:00:00Z',
        ends_at: '2026-07-07T11:00:00Z',
        reason: null,
      }),
    ).rejects.toMatchObject({ status: 422, detail: 'starts_at must be timezone-aware.' })
  })

  it('throws a typed ApiError on a network failure', async () => {
    server.use(http.post('/api/v1/maintenance', () => HttpResponse.error()))

    await expect(
      postMaintenance({
        component_id: 'checkout',
        starts_at: '2026-07-07T10:00:00Z',
        ends_at: '2026-07-07T11:00:00Z',
        reason: null,
      }),
    ).rejects.toBeInstanceOf(ApiError)
  })
})
