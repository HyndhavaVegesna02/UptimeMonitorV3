import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HttpResponse, http } from 'msw'
import { describe, expect, it } from 'vitest'
import { server } from '../../mocks/server'
import { useSampleMode } from './useSampleMode'

/** Minimal harness driving every `useSampleMode` phase the same way its
 * consumer (`DashboardPage`) will drive it (mirrors `useComponents.test.tsx`'s
 * harness pattern). */
function Harness() {
  const { state, retry, enabled, setEnabled, mutating, mutationError } = useSampleMode()

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

  return (
    <div>
      <button
        role="switch"
        aria-checked={enabled ?? false}
        disabled={mutating}
        onClick={() => void setEnabled(!enabled)}
      >
        toggle
      </button>
      {mutationError ? <p role="alert">{mutationError}</p> : null}
    </div>
  )
}

describe('useSampleMode', () => {
  it('starts in the loading phase, then reflects the GET-loaded state (off)', async () => {
    render(<Harness />)

    expect(screen.getByRole('status')).toBeInTheDocument()

    expect(await screen.findByRole('switch')).toHaveAttribute('aria-checked', 'false')
  })

  it('reflects the GET-loaded state when the flag is already on', async () => {
    server.use(http.get('/api/v1/sample-mode', () => HttpResponse.json({ enabled: true })))

    render(<Harness />)

    expect(await screen.findByRole('switch')).toHaveAttribute('aria-checked', 'true')
  })

  it('PUTs the requested value and reflects the RESPONSE state on success (no optimistic flip)', async () => {
    const user = userEvent.setup()
    let receivedBody: unknown
    server.use(
      http.put('/api/v1/sample-mode', async ({ request }) => {
        receivedBody = await request.json()
        return HttpResponse.json({ enabled: true })
      }),
    )

    render(<Harness />)
    const toggle = await screen.findByRole('switch')
    expect(toggle).toHaveAttribute('aria-checked', 'false')

    await user.click(toggle)

    await waitFor(() => expect(toggle).toHaveAttribute('aria-checked', 'true'))
    expect(receivedBody).toEqual({ enabled: true })
  })

  it('disables the switch while the PUT is in flight', async () => {
    const user = userEvent.setup()
    let resolvePut: (() => void) | undefined
    server.use(
      http.put('/api/v1/sample-mode', async () => {
        await new Promise<void>((resolve) => {
          resolvePut = resolve
        })
        return HttpResponse.json({ enabled: true })
      }),
    )

    render(<Harness />)
    const toggle = await screen.findByRole('switch')

    await user.click(toggle)

    await waitFor(() => expect(toggle).toBeDisabled())

    resolvePut?.()

    await waitFor(() => expect(toggle).not.toBeDisabled())
    expect(toggle).toHaveAttribute('aria-checked', 'true')
  })

  it('on a failed PUT, leaves the state unchanged and surfaces a mutation error', async () => {
    const user = userEvent.setup()
    server.use(
      http.put('/api/v1/sample-mode', () =>
        HttpResponse.json({ detail: 'boom' }, { status: 500 }),
      ),
    )

    render(<Harness />)
    const toggle = await screen.findByRole('switch')
    expect(toggle).toHaveAttribute('aria-checked', 'false')

    await user.click(toggle)

    expect(await screen.findByRole('alert')).toBeInTheDocument()
    expect(toggle).toHaveAttribute('aria-checked', 'false')
  })

  it('reaches the error phase on a GET failure, then recovers via retry', async () => {
    const user = userEvent.setup()
    let callCount = 0
    server.use(
      http.get('/api/v1/sample-mode', () => {
        callCount += 1
        if (callCount === 1) {
          return HttpResponse.json({ detail: 'boom' }, { status: 500 })
        }
        return HttpResponse.json({ enabled: false })
      }),
    )

    render(<Harness />)

    expect(await screen.findByRole('alert')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Retry' }))

    expect(await screen.findByRole('switch')).toHaveAttribute('aria-checked', 'false')
    expect(callCount).toBe(2)
  })
})
