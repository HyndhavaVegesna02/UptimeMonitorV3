import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { useFetch } from './useFetch'

/** Minimal harness rendering every `useFetch` phase — mirrors how a real
 * consumer (`useComponents`, `useApprovals`) drives the hook. The fetcher
 * itself is a plain function under the test's control (not a network call),
 * since `useFetch` is a generic utility with no I/O of its own to mock. */
function Harness<T>({ fetcher }: { fetcher: () => Promise<T> }) {
  const { state, retry } = useFetch(fetcher)

  if (state.phase === 'loading') {
    return <div role="status">Loading…</div>
  }

  if (state.phase === 'error') {
    return (
      <div>
        <p role="alert">{state.message}</p>
        <button onClick={retry}>Retry</button>
      </div>
    )
  }

  return <p>{JSON.stringify(state.data)}</p>
}

describe('useFetch', () => {
  it('starts in the loading phase, then reaches success with the resolved data', async () => {
    const fetcher = () => Promise.resolve(['a', 'b'])

    render(<Harness fetcher={fetcher} />)

    expect(screen.getByRole('status')).toBeInTheDocument()

    expect(await screen.findByText(JSON.stringify(['a', 'b']))).toBeInTheDocument()
  })

  it('reaches the error phase on a rejected fetch, then recovers via retry (re-fetching)', async () => {
    const user = userEvent.setup()
    let callCount = 0
    const fetcher = () => {
      callCount += 1
      if (callCount === 1) {
        return Promise.reject(new Error('boom'))
      }
      return Promise.resolve({ ok: true })
    }

    render(<Harness fetcher={fetcher} />)

    expect(await screen.findByRole('alert')).toHaveTextContent('boom')

    await user.click(screen.getByRole('button', { name: 'Retry' }))

    expect(await screen.findByText(JSON.stringify({ ok: true }))).toBeInTheDocument()
    expect(callCount).toBe(2)
  })

  it('falls back to a generic message when the rejection is not an Error', async () => {
    const fetcher = () => Promise.reject('not an Error instance')

    render(<Harness fetcher={fetcher} />)

    expect(await screen.findByRole('alert')).toHaveTextContent('Unknown error')
  })
})
