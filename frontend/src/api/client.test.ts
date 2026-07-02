import { HttpResponse, http } from 'msw'
import { describe, expect, it } from 'vitest'
import { server } from '../mocks/server'
import { FIXTURE_COMPONENTS } from '../mocks/handlers'
import { ApiError, getComponents } from './client'

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
})
