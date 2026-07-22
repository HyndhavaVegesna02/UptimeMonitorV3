import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import type { ProbeLocationRow } from './deriveProbeLocations'
import { ProbeLocationsPanel } from './ProbeLocationsPanel'

const LOCATIONS: ProbeLocationRow[] = [
  {
    location: 'SYNTHETIC_LOCATION-0000000000000047',
    label: '#0047',
    health: 'up',
    latestLatencyMs: 951,
    availabilityPct: 0.5,
    errorCount: 1,
  },
  {
    location: 'SYNTHETIC_LOCATION-0000000000000060',
    label: '#0060',
    health: 'up',
    latestLatencyMs: 588,
    availabilityPct: 1,
    errorCount: 0,
  },
]

describe('ProbeLocationsPanel', () => {
  it('renders one row per real probe location, with health dot+label', () => {
    render(<ProbeLocationsPanel locations={LOCATIONS} />)
    expect(screen.getByText(/#0047/)).toBeInTheDocument()
    expect(screen.getByText(/#0060/)).toBeInTheDocument()
    expect(screen.getAllByText('Up')).toHaveLength(2)
  })

  it('defaults to the Latency metric, shown for each row', () => {
    render(<ProbeLocationsPanel locations={LOCATIONS} />)
    expect(screen.getByRole('button', { name: 'Latency' })).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByText('951')).toBeInTheDocument()
    expect(screen.getByText('588')).toBeInTheDocument()
  })

  it('has a segmented control with the 3 metrics and correct aria-pressed roles', () => {
    render(<ProbeLocationsPanel locations={LOCATIONS} />)
    const group = screen.getByRole('group', { name: 'Metric' })
    expect(within(group).getByRole('button', { name: 'Latency' })).toHaveAttribute('aria-pressed', 'true')
    expect(within(group).getByRole('button', { name: 'Availability' })).toHaveAttribute('aria-pressed', 'false')
    expect(within(group).getByRole('button', { name: 'Errors' })).toHaveAttribute('aria-pressed', 'false')
  })

  it('switches to Availability values when that segment is pressed', async () => {
    const user = userEvent.setup()
    render(<ProbeLocationsPanel locations={LOCATIONS} />)

    await user.click(screen.getByRole('button', { name: 'Availability' }))

    expect(screen.getByRole('button', { name: 'Availability' })).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByRole('button', { name: 'Latency' })).toHaveAttribute('aria-pressed', 'false')
    expect(screen.getByText('50.00')).toBeInTheDocument()
    expect(screen.getByText('100.00')).toBeInTheDocument()
  })

  it('switches to Errors values when that segment is pressed', async () => {
    const user = userEvent.setup()
    render(<ProbeLocationsPanel locations={LOCATIONS} />)

    await user.click(screen.getByRole('button', { name: 'Errors' }))

    expect(screen.getByRole('button', { name: 'Errors' })).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getAllByText('0')).toHaveLength(1)
    expect(screen.getAllByText('1')).toHaveLength(1)
  })

  it('renders an EmptyState when there are no probe locations', () => {
    render(<ProbeLocationsPanel locations={[]} />)
    expect(screen.getByText(/No probe locations/)).toBeInTheDocument()
    expect(screen.queryByRole('group', { name: 'Metric' })).toBeNull()
  })
})
