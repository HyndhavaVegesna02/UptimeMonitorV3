import { HttpResponse, http } from 'msw'
import { describe, expect, it } from 'vitest'
import { server } from '../mocks/server'
import { FIXTURE_COMPONENTS, FIXTURE_PROPOSALS } from '../mocks/handlers'
import { ApiError, getApprovals, getComponents, postDecision } from './client'

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
