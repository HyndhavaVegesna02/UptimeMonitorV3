import { describe, expect, it, vi } from 'vitest'
import { dedupedFetch } from './fetchDedup'

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

  it('coalesces concurrent callers even when one of them is racing an in-flight REJECTION', async () => {
    const fetcher = vi.fn().mockRejectedValue(new Error('boom'))

    const results = await Promise.allSettled([dedupedFetch(fetcher), dedupedFetch(fetcher)])

    expect(fetcher).toHaveBeenCalledTimes(1)
    expect(results[0].status).toBe('rejected')
    expect(results[1].status).toBe('rejected')
  })
})
