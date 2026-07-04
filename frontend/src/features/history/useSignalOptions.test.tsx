import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HttpResponse, http } from 'msw'
import { describe, expect, it } from 'vitest'
import { server } from '../../mocks/server'
import { FIXTURE_TOPOLOGY } from '../../mocks/handlers'
import { useSignalOptions } from './useSignalOptions'

/** Minimal harness rendering every `useSignalOptions` phase. */
function Harness() {
  const { state, retry } = useSignalOptions()

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

describe('useSignalOptions', () => {
  it('starts in the loading phase, then reaches success with the fetched topology', async () => {
    render(<Harness />)

    expect(screen.getByRole('status')).toBeInTheDocument()

    expect(
      await screen.findByText(FIXTURE_TOPOLOGY[0].name),
    ).toBeInTheDocument()
  })

  it('reaches the error phase on failure, then recovers via retry', async () => {
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

    expect(
      await screen.findByText(FIXTURE_TOPOLOGY[0].name),
    ).toBeInTheDocument()
    expect(callCount).toBe(2)
  })
})
