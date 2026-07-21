import { HttpResponse, http } from 'msw'
import { describe, expect, it } from 'vitest'
import { FIXTURE_PROPOSALS } from '../mocks/handlers/approvals'
import { FIXTURE_COMPONENTS } from '../mocks/handlers/components'
import { server } from '../mocks/server'
import { ApiError, getApprovals, getComponents } from './client'

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

describe('ApiError', () => {
  it('is a real Error subclass', () => {
    const err = new ApiError('boom', 404, 'not found')
    expect(err).toBeInstanceOf(Error)
    expect(err.status).toBe(404)
    expect(err.detail).toBe('not found')
  })
})
