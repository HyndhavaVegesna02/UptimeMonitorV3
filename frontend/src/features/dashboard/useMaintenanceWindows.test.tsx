import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HttpResponse, http } from 'msw'
import { describe, expect, it } from 'vitest'
import { server } from '../../mocks/server'
import { FIXTURE_MAINTENANCE_WINDOWS } from '../../mocks/handlers'
import { useMaintenanceWindows } from './useMaintenanceWindows'

/** Minimal harness rendering every `useMaintenanceWindows` phase, mirroring
 * `useComponents.test.tsx`'s harness pattern (STORY-046). */
function Harness() {
  const { state, retry } = useMaintenanceWindows()

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
      {state.data.map((window) => (
        <li key={window.id}>{window.component_id}</li>
      ))}
    </ul>
  )
}

describe('useMaintenanceWindows', () => {
  it('starts in the loading phase, then reaches success with the fetched windows', async () => {
    render(<Harness />)

    expect(screen.getByRole('status')).toBeInTheDocument()

    for (const window of FIXTURE_MAINTENANCE_WINDOWS) {
      expect(await screen.findByText(window.component_id)).toBeInTheDocument()
    }
  })

  it('reaches the error phase on failure, then recovers via retry (re-fetching)', async () => {
    const user = userEvent.setup()
    let callCount = 0
    server.use(
      http.get('/api/v1/maintenance', () => {
        callCount += 1
        if (callCount === 1) {
          return HttpResponse.json({ detail: 'boom' }, { status: 500 })
        }
        return HttpResponse.json(FIXTURE_MAINTENANCE_WINDOWS)
      }),
    )

    render(<Harness />)

    expect(await screen.findByRole('alert')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Retry' }))

    expect(
      await screen.findByText(FIXTURE_MAINTENANCE_WINDOWS[0].component_id),
    ).toBeInTheDocument()
    expect(callCount).toBe(2)
  })
})
