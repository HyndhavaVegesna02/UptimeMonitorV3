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
  const { state, retry, lastUpdatedAt } = useComponents()

  if (state.phase === 'loading') {
    return (
      <div role="status">
        Loading…
        <span data-testid="last-updated">{lastUpdatedAt ?? 'none'}</span>
      </div>
    )
  }

  if (state.phase === 'error') {
    return (
      <div>
        <p role="alert">{state.message}</p>
        <button onClick={retry}>Retry</button>
        <span data-testid="last-updated">{lastUpdatedAt ?? 'none'}</span>
      </div>
    )
  }

  return (
    <div>
      <ul>
        {state.data.map((component) => (
          <li key={component.id}>{component.name}</li>
        ))}
      </ul>
      <span data-testid="last-updated">{lastUpdatedAt ?? 'none'}</span>
    </div>
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

  describe('lastUpdatedAt (STORY-099 AC3)', () => {
    it('is null before the first successful fetch, then a real ISO instant of the last success', async () => {
      render(<Harness />)

      expect(screen.getByTestId('last-updated')).toHaveTextContent('none')

      await screen.findByText(FIXTURE_COMPONENTS[0].name)
      // The effect that stamps `lastUpdatedAt` commits in a render AFTER the
      // one `findByText` resolved on — wait for it explicitly rather than
      // racing the two renders.
      await waitFor(() =>
        expect(screen.getByTestId('last-updated')).not.toHaveTextContent('none'),
      )

      const stamped = screen.getByTestId('last-updated').textContent
      // A real, parseable ISO instant — never a fabricated/placeholder value.
      expect(Number.isNaN(new Date(stamped as string).getTime())).toBe(false)
    })

    it('stays null on a fetch failure — never a fabricated instant', async () => {
      server.use(
        http.get('/api/v1/components', () =>
          HttpResponse.json({ detail: 'boom' }, { status: 500 }),
        ),
      )

      render(<Harness />)

      await screen.findByRole('alert')
      expect(screen.getByTestId('last-updated')).toHaveTextContent('none')
    })

    it('re-stamps on every later success (e.g. a manual retry), not just the first', async () => {
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

      await screen.findByRole('alert')
      expect(screen.getByTestId('last-updated')).toHaveTextContent('none')

      await user.click(screen.getByRole('button', { name: 'Retry' }))
      await screen.findByText(FIXTURE_COMPONENTS[0].name)

      expect(screen.getByTestId('last-updated')).not.toHaveTextContent('none')
    })
  })
})
