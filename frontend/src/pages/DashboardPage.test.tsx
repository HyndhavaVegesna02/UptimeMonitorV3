import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HttpResponse, http } from 'msw'
import { describe, expect, it } from 'vitest'
import { server } from '../mocks/server'
import { FIXTURE_COMPONENTS } from '../mocks/handlers'
import { DashboardPage } from './DashboardPage'

describe('DashboardPage', () => {
  it('shows a loading state, then a table with one row per component (AC1, AC2)', async () => {
    render(<DashboardPage />)

    expect(screen.getByRole('status')).toBeInTheDocument()

    const table = await screen.findByRole('table')
    expect(table).toBeInTheDocument()

    // Semantic column headers (AC1: `<th scope="col">`).
    expect(
      screen.getByRole('columnheader', { name: 'Component' }),
    ).toBeInTheDocument()
    expect(
      screen.getByRole('columnheader', { name: 'Status' }),
    ).toBeInTheDocument()

    expect(screen.getByText(FIXTURE_COMPONENTS[0].name)).toBeInTheDocument()
    expect(screen.getByText(FIXTURE_COMPONENTS[1].name)).toBeInTheDocument()
    // operational -> "Up", degraded -> "Degraded" (src/api/statusMapping.ts)
    expect(screen.getByText('Up')).toBeInTheDocument()
    expect(screen.getByText('Degraded')).toBeInTheDocument()

    // Exactly one data row per fixture component.
    expect(screen.getAllByRole('row')).toHaveLength(FIXTURE_COMPONENTS.length + 1)
  })

  it('renders the empty state when the backend returns no components (AC2)', async () => {
    server.use(http.get('/api/v1/components', () => HttpResponse.json([])))

    render(<DashboardPage />)

    expect(
      await screen.findByText('No components configured'),
    ).toBeInTheDocument()
    expect(screen.queryByRole('table')).not.toBeInTheDocument()
  })

  it('shows an error state on failure, then recovers via retry (AC2)', async () => {
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

    render(<DashboardPage />)

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
