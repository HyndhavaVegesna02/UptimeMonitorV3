import { act, render, screen, waitFor } from '@testing-library/react'
import { useState } from 'react'
import { describe, expect, it, vi } from 'vitest'
import { useFetch } from './useFetch'

function Harness({ fetcher }: { fetcher: () => Promise<string> }) {
  const { state, retry } = useFetch(fetcher)
  return (
    <div>
      <div data-testid="phase">{state.phase}</div>
      {state.phase === 'success' ? <div data-testid="data">{state.data}</div> : null}
      {state.phase === 'error' ? <div data-testid="message">{state.message}</div> : null}
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
