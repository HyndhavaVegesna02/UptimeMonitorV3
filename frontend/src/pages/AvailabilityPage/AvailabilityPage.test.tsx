import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import { AppRoutes } from '../../routes'

function renderPage() {
  return render(
    <MemoryRouter initialEntries={['/availability']}>
      <AppRoutes />
    </MemoryRouter>,
  )
}

describe('AvailabilityPage (STORY-129)', () => {
  it('renders heading, window toggle, and component rollup card', async () => {
    renderPage()

    expect(screen.getByRole('heading', { level: 1, name: 'Availability' })).toBeInTheDocument()

    await waitFor(
      () => {
        expect(screen.getByText('100.0%')).toBeInTheDocument()
      },
      { timeout: 5000 },
    )

    expect(screen.getByText('HTTP Check')).toBeInTheDocument()
    expect(screen.getByText('9.3%')).toBeInTheDocument()
    expect(screen.getByText('Low completeness')).toBeInTheDocument()
  })

  it('toggles window selection', async () => {
    const user = userEvent.setup()
    renderPage()

    await waitFor(
      () => {
        expect(screen.getByText('HTTP Check')).toBeInTheDocument()
      },
      { timeout: 5000 },
    )

    const btn7d = screen.getByRole('button', { name: '7D' })
    await user.click(btn7d)

    expect(screen.getByText('HTTP Check')).toBeInTheDocument()
  })

  it('expands signal breakdown table on toggle click', async () => {
    const user = userEvent.setup()
    renderPage()

    await waitFor(
      () => {
        expect(screen.getByText('HTTP Check')).toBeInTheDocument()
      },
      { timeout: 5000 },
    )

    const toggleBtn = await screen.findByRole(
      'button',
      { name: /Signals \(1\)/i },
      { timeout: 5000 },
    )
    expect(toggleBtn).toHaveAttribute('aria-expanded', 'false')

    await user.click(toggleBtn)
    expect(toggleBtn).toHaveAttribute('aria-expanded', 'true')

    expect(screen.getByText('Signal Breakdown')).toBeInTheDocument()
    expect(screen.getByText('120s')).toBeInTheDocument()
  })
})
