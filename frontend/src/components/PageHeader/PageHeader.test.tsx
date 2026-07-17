import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { PageHeader } from './PageHeader'

describe('PageHeader', () => {
  it('renders the title as a level-one heading', () => {
    render(<PageHeader title="Dashboard" />)
    expect(
      screen.getByRole('heading', { name: 'Dashboard', level: 1 }),
    ).toBeInTheDocument()
  })

  it('renders an optional subtitle', () => {
    render(<PageHeader title="Dashboard" subtitle="Live status across monitored components" />)
    expect(
      screen.getByText('Live status across monitored components'),
    ).toBeInTheDocument()
  })

  it('renders nothing extra when subtitle is omitted', () => {
    const { container } = render(<PageHeader title="Dashboard" />)
    expect(container.querySelector('.page-header__subtitle')).not.toBeInTheDocument()
  })

  it('renders an optional actions slot', () => {
    render(
      <PageHeader
        title="Availability"
        actions={<button type="button">Time window</button>}
      />,
    )
    expect(screen.getByRole('button', { name: 'Time window' })).toBeInTheDocument()
  })

  it('renders nothing extra when actions is omitted', () => {
    const { container } = render(<PageHeader title="Availability" />)
    expect(container.querySelector('.page-header__actions')).not.toBeInTheDocument()
  })
})
