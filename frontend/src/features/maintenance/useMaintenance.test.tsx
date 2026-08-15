import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HttpResponse, http } from 'msw'
import { describe, expect, it } from 'vitest'
import { server } from '../../mocks/server'
import { FIXTURE_MAINTENANCE_WINDOWS } from '../../mocks/handlers'
import { useMaintenance } from './useMaintenance'

const VALID_REQUEST = {
  component_id: 'checkout',
  starts_at: '2026-07-07T10:00:00.000Z',
  ends_at: '2026-07-07T11:00:00.000Z',
  reason: 'Database migration',
}

/** Minimal harness driving every `useMaintenance` phase the way its
 * consumer (`MaintenancePage`) will (mirrors `useComponents.test.tsx`'s
 * harness pattern). */
function Harness() {
  const { state, retry, schedule, scheduling, mutationError } = useMaintenance()

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
      <ul>
        {state.data.map((window) => (
          <li key={window.id}>{window.component_id}</li>
        ))}
      </ul>
      <button disabled={scheduling} onClick={() => void schedule(VALID_REQUEST)}>
        Schedule
      </button>
      {mutationError ? <p role="alert">{mutationError.message}</p> : null}
    </div>
  )
}

describe('useMaintenance', () => {
  it('starts in the loading phase, then lists the GET-loaded windows', async () => {
    render(<Harness />)

    expect(screen.getByRole('status')).toBeInTheDocument()

    for (const window of FIXTURE_MAINTENANCE_WINDOWS) {
      expect(await screen.findByText(window.component_id)).toBeInTheDocument()
    }
  })

  it('reaches the error phase on a GET failure, then recovers via retry', async () => {
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

  it('schedules a window and refreshes the list on success (AC2)', async () => {
    const user = userEvent.setup()
    let postedBody: unknown
    let getCallCount = 0
    server.use(
      http.get('/api/v1/maintenance', () => {
        getCallCount += 1
        if (getCallCount === 1) {
          return HttpResponse.json(FIXTURE_MAINTENANCE_WINDOWS)
        }
        return HttpResponse.json([
          ...FIXTURE_MAINTENANCE_WINDOWS,
          { id: 99, ...VALID_REQUEST },
        ])
      }),
      http.post('/api/v1/maintenance', async ({ request }) => {
        postedBody = await request.json()
        return HttpResponse.json({ id: 99, ...VALID_REQUEST }, { status: 201 })
      }),
    )

    render(<Harness />)
    await screen.findByText(FIXTURE_MAINTENANCE_WINDOWS[0].component_id)

    await user.click(screen.getByRole('button', { name: 'Schedule' }))

    await waitFor(() => expect(getCallCount).toBe(2))
    expect(postedBody).toEqual(VALID_REQUEST)
  })

  it('disables scheduling while the POST is in flight', async () => {
    const user = userEvent.setup()
    let resolvePost: (() => void) | undefined
    server.use(
      http.post('/api/v1/maintenance', async () => {
        await new Promise<void>((resolve) => {
          resolvePost = resolve
        })
        return HttpResponse.json({ id: 99, ...VALID_REQUEST }, { status: 201 })
      }),
    )

    render(<Harness />)
    await screen.findByText(FIXTURE_MAINTENANCE_WINDOWS[0].component_id)

    await user.click(screen.getByRole('button', { name: 'Schedule' }))

    await waitFor(() =>
      expect(screen.getByRole('button', { name: 'Schedule' })).toBeDisabled(),
    )

    resolvePost?.()

    // Success re-queries the button fresh each poll: a successful schedule
    // triggers a list refresh (retry()), which briefly unmounts the success
    // view for the loading view (015c Approvals precedent) before a NEW,
    // enabled button remounts — a stale element reference would never
    // observe that remount.
    await waitFor(() =>
      expect(screen.getByRole('button', { name: 'Schedule' })).not.toBeDisabled(),
    )
  })

  it('on a failed POST, leaves the list unchanged and surfaces a mutation error', async () => {
    const user = userEvent.setup()
    let getCallCount = 0
    server.use(
      http.get('/api/v1/maintenance', () => {
        getCallCount += 1
        return HttpResponse.json(FIXTURE_MAINTENANCE_WINDOWS)
      }),
      http.post('/api/v1/maintenance', () =>
        HttpResponse.json({ detail: 'component_id must be a non-empty string.' }, { status: 422 }),
      ),
    )

    render(<Harness />)
    await screen.findByText(FIXTURE_MAINTENANCE_WINDOWS[0].component_id)

    await user.click(screen.getByRole('button', { name: 'Schedule' }))

    expect(await screen.findByRole('alert')).toBeInTheDocument()
    expect(getCallCount).toBe(1)
  })
})
