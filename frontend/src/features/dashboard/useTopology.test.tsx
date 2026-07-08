import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HttpResponse, http } from 'msw'
import { describe, expect, it } from 'vitest'
import { server } from '../../mocks/server'
import { FIXTURE_TOPOLOGY } from '../../mocks/handlers'
import { useTopology } from './useTopology'

/** Minimal harness rendering every `useTopology` phase, so the hook is
 * driven the same way its consumer (`DashboardPage`) will drive it. */
function Harness() {
  const { state, retry } = useTopology()

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
        <li key={component.id}>
          {component.name}: {component.signals.length} signals
        </li>
      ))}
    </ul>
  )
}

describe('useTopology', () => {
  it('starts in the loading phase, then reaches success with the fetched topology', async () => {
    render(<Harness />)

    expect(screen.getByRole('status')).toBeInTheDocument()

    const firstComponent = FIXTURE_TOPOLOGY[0]
    expect(
      await screen.findByText(`${firstComponent.name}: ${firstComponent.signals.length} signals`),
    ).toBeInTheDocument()
  })

  it('reaches the error phase on failure, then recovers via retry (re-fetching)', async () => {
    const user = userEvent.setup()
    let callCount = 0
    server.use(
      http.get('/api/v1/topology', () => {
        callCount += 1
        if (callCount === 1) {
          return HttpResponse.json({ detail: 'boom' }, { status: 500 })
        }
        return HttpResponse.json(FIXTURE_TOPOLOGY)
      }),
    )

    render(<Harness />)

    expect(await screen.findByRole('alert')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Retry' }))

    const firstComponent = FIXTURE_TOPOLOGY[0]
    expect(
      await screen.findByText(`${firstComponent.name}: ${firstComponent.signals.length} signals`),
    ).toBeInTheDocument()
    expect(callCount).toBe(2)
  })
})
