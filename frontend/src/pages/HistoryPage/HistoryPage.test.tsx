import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import { AppRoutes } from '../../routes'

function renderPage() {
  return render(
    <MemoryRouter initialEntries={['/history']}>
      <AppRoutes />
    </MemoryRouter>,
  )
}

describe('HistoryPage (STORY-130)', () => {
  it('renders heading, filter toolbar, and observation rows', async () => {
    renderPage()

    expect(screen.getByRole('heading', { level: 1, name: 'History' })).toBeInTheDocument()

    await waitFor(
      () => {
        expect(screen.getByText('588 ms')).toBeInTheDocument()
      },
      { timeout: 5000 },
    )

    expect(
      screen.getAllByText(/SYNTHETIC_LOCATION-0000000000000060/i).length,
    ).toBeGreaterThan(0)
  })

  it('filters observation rows by text search', async () => {
    const user = userEvent.setup()
    renderPage()

    await waitFor(
      () => {
        expect(screen.getByText('588 ms')).toBeInTheDocument()
      },
      { timeout: 5000 },
    )

    const searchInput = screen.getByLabelText('Search')
    await user.type(searchInput, 'nonexistent-location-xyz')

    expect(
      screen.getByText('No check observations match the active search and filters.'),
    ).toBeInTheDocument()
  })

  it('filters observation rows by result select', async () => {
    const user = userEvent.setup()
    renderPage()

    await waitFor(
      () => {
        expect(screen.getByText('588 ms')).toBeInTheDocument()
      },
      { timeout: 5000 },
    )

    const resultSelect = screen.getByLabelText('Result')
    await user.selectOptions(resultSelect, 'down')

    expect(
      screen.getByText('No check observations match the active search and filters.'),
    ).toBeInTheDocument()
  })

  it('toggles time window selection', async () => {
    const user = userEvent.setup()
    renderPage()

    await waitFor(
      () => {
        expect(screen.getByText('588 ms')).toBeInTheDocument()
      },
      { timeout: 5000 },
    )

    const btn30d = screen.getByRole('button', { name: '30D' })
    await user.click(btn30d)

    await waitFor(
      () => {
        expect(screen.getByText('588 ms')).toBeInTheDocument()
      },
      { timeout: 5000 },
    )
  })
})
