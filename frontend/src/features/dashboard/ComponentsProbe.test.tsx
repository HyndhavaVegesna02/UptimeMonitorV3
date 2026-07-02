import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HttpResponse, http } from 'msw'
import { describe, expect, it } from 'vitest'
import { server } from '../../mocks/server'
import { FIXTURE_COMPONENTS } from '../../mocks/handlers'
import { ComponentsProbe } from './ComponentsProbe'

describe('ComponentsProbe', () => {
  it('shows a loading state, then the fetched components with mapped status badges', async () => {
    render(<ComponentsProbe />)

    expect(screen.getByRole('status')).toBeInTheDocument()

    expect(
      await screen.findByText(FIXTURE_COMPONENTS[0].name),
    ).toBeInTheDocument()
    expect(screen.getByText(FIXTURE_COMPONENTS[1].name)).toBeInTheDocument()
    // operational -> "Up", degraded -> "Degraded" (src/api/statusMapping.ts)
    expect(screen.getByText('Up')).toBeInTheDocument()
    expect(screen.getByText('Degraded')).toBeInTheDocument()
  })

  it('renders the empty state when the backend returns no components', async () => {
    server.use(http.get('/api/v1/components', () => HttpResponse.json([])))

    render(<ComponentsProbe />)

    expect(await screen.findByText('No components yet')).toBeInTheDocument()
  })

  it('shows an error state on failure, then recovers via retry', async () => {
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

    render(<ComponentsProbe />)

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Could not load components',
    )

    await user.click(screen.getByRole('button', { name: 'Retry' }))

    expect(
      await screen.findByText(FIXTURE_COMPONENTS[0].name),
    ).toBeInTheDocument()
    expect(callCount).toBe(2)
  })
})
