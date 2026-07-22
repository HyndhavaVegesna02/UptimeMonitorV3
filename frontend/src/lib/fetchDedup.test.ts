import { describe, expect, it, vi } from 'vitest'
import { dedupedFetch, forgetFetch, resetFetchDedupCache } from './fetchDedup'

/**
 * Unit tests for the in-house promise-coalescing cache (STORY-137). These
 * exercise the primitive directly (no React, no MSW) — `useFetch.test.tsx`
 * and `shell/ShellLayout.test.tsx` cover it wired into a real hook/page.
 */
describe('dedupedFetch', () => {
  it('coalesces two CONCURRENT calls to the same fetcher reference into a single underlying invocation', async () => {
    const fetcher = vi.fn().mockResolvedValue('value')

    const [a, b] = await Promise.all([dedupedFetch(fetcher), dedupedFetch(fetcher)])

    expect(fetcher).toHaveBeenCalledTimes(1)
    expect(a).toBe('value')
    expect(b).toBe('value')
  })

  it('does NOT coalesce two DIFFERENT fetcher references, even if they resolve to the same value (never collapses distinct requests)', async () => {
    const fetcherA = vi.fn().mockResolvedValue('same-value')
    const fetcherB = vi.fn().mockResolvedValue('same-value')

    await Promise.all([dedupedFetch(fetcherA), dedupedFetch(fetcherB)])

    expect(fetcherA).toHaveBeenCalledTimes(1)
    expect(fetcherB).toHaveBeenCalledTimes(1)
  })

  it('issues a genuinely FRESH call once the prior one has settled — never serves a cached result', async () => {
    const fetcher = vi.fn().mockResolvedValueOnce('first').mockResolvedValueOnce('second')

    const first = await dedupedFetch(fetcher)
    const second = await dedupedFetch(fetcher)

    expect(first).toBe('first')
    expect(second).toBe('second')
    expect(fetcher).toHaveBeenCalledTimes(2)
  })

  it('issues a genuinely fresh call after a rejection — never serves a cached failure', async () => {
    const fetcher = vi.fn().mockRejectedValueOnce(new Error('boom')).mockResolvedValueOnce('recovered')

    await expect(dedupedFetch(fetcher)).rejects.toThrow('boom')
    await expect(dedupedFetch(fetcher)).resolves.toBe('recovered')
    expect(fetcher).toHaveBeenCalledTimes(2)
  })

  it('forgetFetch evicts a NEVER-SETTLING in-flight entry, so the next call genuinely re-invokes the fetcher (STORY-136 timeout composition)', async () => {
    let firstCallSettles: (() => void) | undefined
    const fetcher = vi
      .fn()
      .mockImplementationOnce(
        () =>
          new Promise<string>((resolve) => {
            firstCallSettles = () => resolve('too-late')
          }),
      )
      .mockResolvedValueOnce('fresh')

    const firstPromise = dedupedFetch(fetcher)
    forgetFetch(fetcher)

    const second = await dedupedFetch(fetcher)

    expect(fetcher).toHaveBeenCalledTimes(2)
    expect(second).toBe('fresh')

    // The original (never-settling-until-now) call is still a live promise
    // for whoever holds it — evicting it from the cache does not reject it.
    firstCallSettles?.()
    await expect(firstPromise).resolves.toBe('too-late')
  })

  it('forgetFetch on a key with no in-flight entry is a harmless no-op', () => {
    const fetcher = vi.fn()
    expect(() => forgetFetch(fetcher)).not.toThrow()
  })

  it('resetFetchDedupCache wipes every in-flight entry, even a NEVER-SETTLING one — the test-isolation escape hatch a single test-file-wide fetcher reference needs (a test that deliberately never resolves a fetch to assert the loading state must not poison every later test sharing that reference)', () => {
    const hungFetcher = vi.fn(() => new Promise<string>(() => undefined))
    void dedupedFetch(hungFetcher) // never settles, never self-evicts
    expect(hungFetcher).toHaveBeenCalledTimes(1)

    resetFetchDedupCache()

    // Post-reset, the SAME reference is a fresh invocation, not a rejoin of
    // the orphaned still-pending promise.
    void dedupedFetch(hungFetcher)
    expect(hungFetcher).toHaveBeenCalledTimes(2)
  })

  it('coalesces concurrent callers even when one of them is racing an in-flight REJECTION', async () => {
    const fetcher = vi.fn().mockRejectedValue(new Error('boom'))

    const results = await Promise.allSettled([dedupedFetch(fetcher), dedupedFetch(fetcher)])

    expect(fetcher).toHaveBeenCalledTimes(1)
    expect(results[0].status).toBe('rejected')
    expect(results[1].status).toBe('rejected')
  })
})
