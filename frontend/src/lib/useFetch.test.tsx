import { act, render, screen, waitFor } from '@testing-library/react'
import { useState } from 'react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { DEFAULT_FETCH_TIMEOUT_MS, useFetch } from './useFetch'

function Harness({ fetcher }: { fetcher: () => Promise<string> }) {
  const { state, retry, succeededAt } = useFetch(fetcher)
  return (
    <div>
      <div data-testid="phase">{state.phase}</div>
      {state.phase === 'success' ? <div data-testid="data">{state.data}</div> : null}
      {state.phase === 'error' ? <div data-testid="message">{state.message}</div> : null}
      <div data-testid="succeededAt">{succeededAt ? succeededAt.toISOString() : 'null'}</div>
      <button type="button" onClick={retry}>
        Retry
      </button>
    </div>
  )
}

describe('useFetch', () => {
  it('starts in loading phase, then resolves to success with the fetched data', async () => {
    render(<Harness fetcher={() => Promise.resolve('hello')} />)

    expect(screen.getByTestId('phase')).toHaveTextContent('loading')
    expect(await screen.findByTestId('data')).toHaveTextContent('hello')
  })

  it('resolves to an error phase with the thrown Error message', async () => {
    render(<Harness fetcher={() => Promise.reject(new Error('boom'))} />)

    expect(await screen.findByTestId('message')).toHaveTextContent('boom')
  })

  it('falls back to a generic message for a non-Error rejection', async () => {
    render(<Harness fetcher={() => Promise.reject('not an error object')} />)

    expect(await screen.findByTestId('message')).toHaveTextContent('Unknown error')
  })

  it('retry resets to loading and re-invokes the fetcher', async () => {
    const fetcher = vi.fn().mockResolvedValue('first')
    render(<Harness fetcher={fetcher} />)
    await screen.findByTestId('data')
    expect(fetcher).toHaveBeenCalledTimes(1)

    fetcher.mockResolvedValue('second')
    act(() => {
      screen.getByRole('button', { name: 'Retry' }).click()
    })

    await waitFor(() => expect(screen.getByTestId('data')).toHaveTextContent('second'))
    expect(fetcher).toHaveBeenCalledTimes(2)
  })

  describe('succeededAt (STORY-121 quality review — a "last updated" timestamp callers can use without reading Date.now() during their own render)', () => {
    it('stays null while loading', () => {
      render(<Harness fetcher={() => new Promise(() => undefined)} />)
      expect(screen.getByTestId('succeededAt')).toHaveTextContent('null')
    })

    it('is set once the fetch succeeds', async () => {
      render(<Harness fetcher={() => Promise.resolve('hello')} />)
      await screen.findByTestId('data')
      expect(screen.getByTestId('succeededAt')).not.toHaveTextContent('null')
    })

    it('stays null when the fetch errors (never a fabricated success time)', async () => {
      render(<Harness fetcher={() => Promise.reject(new Error('boom'))} />)
      await screen.findByTestId('message')
      expect(screen.getByTestId('succeededAt')).toHaveTextContent('null')
    })

    it('gets a fresh value on a successful retry, not the first attempt\'s stale timestamp', async () => {
      const fetcher = vi.fn().mockResolvedValue('first')
      render(<Harness fetcher={fetcher} />)
      await screen.findByTestId('data')
      const firstSucceededAt = screen.getByTestId('succeededAt').textContent

      // Force real wall-clock separation so a second `new Date()` call is
      // provably distinct, not just coincidentally re-rendered with the
      // same millisecond.
      await act(async () => {
        await new Promise((resolve) => setTimeout(resolve, 5))
      })

      fetcher.mockResolvedValue('second')
      act(() => {
        screen.getByRole('button', { name: 'Retry' }).click()
      })
      await waitFor(() => expect(screen.getByTestId('data')).toHaveTextContent('second'))

      expect(screen.getByTestId('succeededAt').textContent).not.toBe(firstSucceededAt)
    })
  })

  describe('request timeout (STORY-136 AC3 — a never-settling request must not spin forever)', () => {
    afterEach(() => {
      vi.useRealTimers()
    })

    it('transitions a never-settling request to the error phase once the default timeout elapses, and a retry re-issues a fresh request', async () => {
      vi.useFakeTimers()
      const fetcher = vi.fn(() => new Promise<string>(() => undefined))

      render(<Harness fetcher={fetcher} />)
      expect(screen.getByTestId('phase')).toHaveTextContent('loading')

      await act(async () => {
        await vi.advanceTimersByTimeAsync(DEFAULT_FETCH_TIMEOUT_MS)
      })

      expect(screen.getByTestId('phase')).toHaveTextContent('error')
      expect(screen.getByTestId('message')).toHaveTextContent(/timed out/i)
      expect(fetcher).toHaveBeenCalledTimes(1)

      act(() => {
        screen.getByRole('button', { name: 'Retry' }).click()
      })

      expect(screen.getByTestId('phase')).toHaveTextContent('loading')
      expect(fetcher).toHaveBeenCalledTimes(2)
    })

    it('does not fire the timeout once the fetch has already settled (existing error/retry behavior preserved)', async () => {
      vi.useFakeTimers()
      const fetcher = vi.fn().mockRejectedValue(new Error('boom'))

      render(<Harness fetcher={fetcher} />)

      await act(async () => {
        await vi.advanceTimersByTimeAsync(0)
      })

      expect(screen.getByTestId('message')).toHaveTextContent('boom')

      await act(async () => {
        await vi.advanceTimersByTimeAsync(DEFAULT_FETCH_TIMEOUT_MS)
      })

      // Still the original rejection message, not a timeout overwrite.
      expect(screen.getByTestId('message')).toHaveTextContent('boom')
    })
  })

  describe('shared fetch dedup (STORY-137 AC1/AC2 — concurrent identical fetches coalesce)', () => {
    it('invokes a fetcher shared by two concurrently-mounted instances only ONCE', async () => {
      const fetcher = vi.fn().mockResolvedValue('shared')

      render(
        <div>
          <Harness fetcher={fetcher} />
          <Harness fetcher={fetcher} />
        </div>,
      )

      const dataNodes = await screen.findAllByTestId('data')
      expect(dataNodes).toHaveLength(2)
      dataNodes.forEach((node) => expect(node).toHaveTextContent('shared'))
      expect(fetcher).toHaveBeenCalledTimes(1)
    })

    it('never coalesces two DIFFERENT fetcher references, even resolving to the same value', async () => {
      const fetcherA = vi.fn().mockResolvedValue('same-value')
      const fetcherB = vi.fn().mockResolvedValue('same-value')

      render(
        <div>
          <Harness fetcher={fetcherA} />
          <Harness fetcher={fetcherB} />
        </div>,
      )

      await screen.findAllByTestId('data')
      expect(fetcherA).toHaveBeenCalledTimes(1)
      expect(fetcherB).toHaveBeenCalledTimes(1)
    })

    it('retry re-issues a REAL request, not a served-from-cache stale failure, once the shared request has settled', async () => {
      const fetcher = vi.fn().mockRejectedValueOnce(new Error('boom')).mockResolvedValueOnce('recovered')

      render(<Harness fetcher={fetcher} />)
      await screen.findByTestId('message')
      expect(fetcher).toHaveBeenCalledTimes(1)

      act(() => {
        screen.getByRole('button', { name: 'Retry' }).click()
      })

      await waitFor(() => expect(screen.getByTestId('data')).toHaveTextContent('recovered'))
      expect(fetcher).toHaveBeenCalledTimes(2)
    })
  })

  describe('unmount eviction (quality-review MAJOR fix — a never-settling request must not orphan the dedup cache entry on unmount)', () => {
    afterEach(() => {
      vi.useRealTimers()
    })

    it('evicts the in-flight entry on unmount, before the timeout fires, so a later mount of the SAME fetcher issues a genuinely fresh request instead of rejoining the orphaned promise', async () => {
      vi.useFakeTimers()
      const fetcher = vi.fn(() => new Promise<string>(() => undefined)) // never settles

      const { unmount } = render(<Harness fetcher={fetcher} />)
      expect(fetcher).toHaveBeenCalledTimes(1)

      // Unmount well before the 15s default timeout would fire — the
      // production sequence: user navigates away while the backend is
      // still hanging.
      act(() => {
        unmount()
      })

      // Mount a second instance against the SAME stable fetcher reference —
      // simulating the user returning to a page that shares it.
      render(<Harness fetcher={fetcher} />)

      expect(fetcher).toHaveBeenCalledTimes(2)
    })

    it('a still-pending request that settles after an unmount is a harmless no-op eviction (already-absent key delete)', async () => {
      let resolveFetch: (value: string) => void = () => undefined
      const fetcher = vi.fn(
        () =>
          new Promise<string>((resolve) => {
            resolveFetch = resolve
          }),
      )

      const { unmount } = render(<Harness fetcher={fetcher} />)
      unmount()

      // Resolving after unmount must not throw, and a subsequent fresh
      // mount must still get a genuinely new request (not somehow break
      // from the earlier `.finally()` deleting an already-absent key).
      await act(async () => {
        resolveFetch('too late')
      })

      render(<Harness fetcher={fetcher} />)
      await waitFor(() => expect(fetcher).toHaveBeenCalledTimes(2))
    })

    it('two components sharing one in-flight promise: one unmounting does not break the surviving sibling', async () => {
      let resolveFetch: (value: string) => void = () => undefined
      const fetcher = vi.fn(
        () =>
          new Promise<string>((resolve) => {
            resolveFetch = resolve
          }),
      )

      function Siblings({ showFirst }: { showFirst: boolean }) {
        return (
          <div>
            {showFirst ? <Harness fetcher={fetcher} /> : null}
            <Harness fetcher={fetcher} />
          </div>
        )
      }

      const { rerender } = render(<Siblings showFirst={true} />)
      expect(fetcher).toHaveBeenCalledTimes(1)

      // Unmount the first sibling only — the second is still mounted and
      // still awaiting the SAME shared promise.
      rerender(<Siblings showFirst={false} />)

      await act(async () => {
        resolveFetch('shared-value')
      })

      const secondData = await screen.findAllByTestId('data')
      expect(secondData.some((node) => node.textContent === 'shared-value')).toBe(true)
    })
  })

  it('never sets state after unmount (cancelled-guarded effect)', async () => {
    let resolveFetch: (value: string) => void = () => undefined
    const fetcher = () =>
      new Promise<string>((resolve) => {
        resolveFetch = resolve
      })

    function Wrapper() {
      const [mounted, setMounted] = useState(true)
      return (
        <div>
          {mounted ? <Harness fetcher={fetcher} /> : <div data-testid="unmounted" />}
          <button type="button" onClick={() => setMounted(false)}>
            Unmount
          </button>
        </div>
      )
    }

    render(<Wrapper />)
    screen.getByRole('button', { name: 'Unmount' }).click()

    // Resolving after unmount must not throw a "set state on an unmounted
    // component" warning-turned-error in strict test setups.
    await act(async () => {
      resolveFetch('too late')
    })

    expect(screen.getByTestId('unmounted')).toBeInTheDocument()
  })
})
