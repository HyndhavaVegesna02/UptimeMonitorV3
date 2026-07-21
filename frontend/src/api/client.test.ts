import { HttpResponse, http } from 'msw'
import { describe, expect, it } from 'vitest'
import { FIXTURE_PROPOSALS } from '../mocks/handlers/approvals'
import { FIXTURE_AVAILABILITY } from '../mocks/handlers/availability'
import { FIXTURE_COMPONENTS } from '../mocks/handlers/components'
import { FIXTURE_HISTORY } from '../mocks/handlers/history'
import { FIXTURE_MAINTENANCE } from '../mocks/handlers/maintenance'
import { server } from '../mocks/server'
import {
  ApiError,
  getApprovals,
  getAvailability,
  getComponents,
  getHistory,
  getMaintenance,
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

describe('ApiError', () => {
  it('is a real Error subclass', () => {
    const err = new ApiError('boom', 404, 'not found')
    expect(err).toBeInstanceOf(Error)
    expect(err.status).toBe(404)
    expect(err.detail).toBe('not found')
  })
})
