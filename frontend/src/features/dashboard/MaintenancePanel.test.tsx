import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import type { MaintenanceWindowDTO } from '../../api/types'
import { MaintenancePanel } from './MaintenancePanel'

describe('MaintenancePanel', () => {
  it('renders a tidy EmptyState when there are no scheduled windows (the real captured sample)', () => {
    render(<MaintenancePanel windows={[]} />)
    expect(screen.getByText(/No maintenance/i)).toBeInTheDocument()
  })

  it('renders the next upcoming window with its title/reason and formatted time range', () => {
    const windows: MaintenanceWindowDTO[] = [
      {
        id: 1,
        component_id: 'http-check',
        starts_at: '2026-07-25T02:00:00Z',
        ends_at: '2026-07-25T04:00:00Z',
        reason: 'Planned upgrade',
        title: 'HTTP Check',
      },
    ]
    render(<MaintenancePanel windows={windows} />)
    expect(screen.getByText('HTTP Check')).toBeInTheDocument()
    expect(screen.getByText(/Planned upgrade/)).toBeInTheDocument()
  })

  it('falls back to the reason when there is no title, and to the component id when there is neither', () => {
    const windows: MaintenanceWindowDTO[] = [
      { id: 2, component_id: 'http-check', starts_at: '2026-07-25T02:00:00Z', ends_at: '2026-07-25T04:00:00Z', reason: null, title: null },
    ]
    render(<MaintenancePanel windows={windows} />)
    expect(screen.getByText('http-check')).toBeInTheDocument()
  })

  it('picks the SOONEST upcoming window, not just the first array entry', () => {
    const windows: MaintenanceWindowDTO[] = [
      { id: 1, component_id: 'later', starts_at: '2026-08-01T00:00:00Z', ends_at: '2026-08-01T02:00:00Z', reason: null, title: 'Later window' },
      { id: 2, component_id: 'sooner', starts_at: '2026-07-22T00:00:00Z', ends_at: '2026-07-22T02:00:00Z', reason: null, title: 'Sooner window' },
    ]
    render(<MaintenancePanel windows={windows} />)
    expect(screen.getByText('Sooner window')).toBeInTheDocument()
    expect(screen.queryByText('Later window')).toBeNull()
  })
})
