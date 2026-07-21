import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import { AppRoutes } from '../../routes'

function renderPage() {
  return render(
    <MemoryRouter initialEntries={['/publications']}>
      <AppRoutes />
    </MemoryRouter>,
  )
}

describe('PublicationsPage (STORY-133)', () => {
  it('renders heading, caption, and publication rows', async () => {
    renderPage()

    expect(screen.getByRole('heading', { level: 1, name: 'Publications' })).toBeInTheDocument()

    await waitFor(
      () => {
        expect(screen.getByText('dashboard-operator')).toBeInTheDocument()
      },
      { timeout: 5000 },
    )

    expect(screen.getByText('Succeeded')).toBeInTheDocument()
    expect(screen.getByText('Failed')).toBeInTheDocument()
    expect(screen.getByText('#1')).toBeInTheDocument()
    expect(screen.getByText('Showing recent publish attempts (capped at 50)')).toBeInTheDocument()
  })
})
