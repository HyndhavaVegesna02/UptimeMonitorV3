import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HttpResponse, http } from 'msw'
import { describe, expect, it } from 'vitest'
import { server } from '../../mocks/server'
import { FIXTURE_COMPONENTS } from '../../mocks/handlers'
import { useComponents } from './useComponents'

/** Minimal harness rendering every `useComponents` phase, so the hook is
 * driven the same way its consumer (`DashboardPage`) will drive it. */
function Harness() {
  const { state, retry } = useComponents()

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
    <ul>
      {state.data.map((component) => (
        <li key={component.id}>{component.name}</li>
      ))}
    </ul>
  )
}

describe('useComponents', () => {
  it('starts in the loading phase, then reaches success with the fetched components', async () => {
    render(<Harness />)

    expect(screen.getByRole('status')).toBeInTheDocument()

    expect(
      await screen.findByText(FIXTURE_COMPONENTS[0].name),
    ).toBeInTheDocument()
    expect(screen.getByText(FIXTURE_COMPONENTS[1].name)).toBeInTheDocument()
  })

  it('reports fetchedAtIso as undefined until the fetch succeeds, then a valid ISO instant (STORY-104 AC — "Updated Xs ago", display-layer only)', async () => {
    function FetchedAtHarness() {
      const { state, fetchedAtIso } = useComponents()
      return (
        <p data-testid="fetched-at">
          {state.phase === 'success' ? (fetchedAtIso ?? 'none') : 'pending'}
        </p>
      )
    }

    render(<FetchedAtHarness />)

    expect(screen.getByTestId('fetched-at')).toHaveTextContent('pending')

    await waitFor(() => {
      const text = screen.getByTestId('fetched-at').textContent
      expect(text).not.toBe('pending')
      expect(text).not.toBe('none')
      expect(Number.isNaN(new Date(text ?? '').getTime())).toBe(false)
    })
  })

  it('reaches the error phase on failure, then recovers via retry (re-fetching)', async () => {
    const user = userEvent.setup()
    let callCount = 0
    server.use(
      http.get('/api/v1/components', () => {
        callCount += 1
        if (callCount === 1) {
          return HttpResponse.json({ detail: 'boom' }, { status: 500 })
        }
        return HttpResponse.json(FIXTURE_COMPONENTS)
      }),
    )

    render(<Harness />)

    expect(await screen.findByRole('alert')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Retry' }))

    expect(
      await screen.findByText(FIXTURE_COMPONENTS[0].name),
    ).toBeInTheDocument()
    expect(callCount).toBe(2)
  })
})
