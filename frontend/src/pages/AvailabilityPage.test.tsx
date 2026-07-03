import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import {
  FIXTURE_AVAILABILITY_BY_COMPONENT,
  FIXTURE_TOPOLOGY,
} from '../mocks/handlers'
import { AvailabilityPage } from './AvailabilityPage'

describe('AvailabilityPage', () => {
  it('shows a loading state, then one row per component with the rollup availability headline (AC1)', async () => {
    render(<AvailabilityPage />)

    expect(screen.getByRole('status')).toBeInTheDocument()

    const table = await screen.findByRole('table')
    expect(table).toBeInTheDocument()

    for (const component of FIXTURE_TOPOLOGY) {
      const availability = FIXTURE_AVAILABILITY_BY_COMPONENT[component.id]
      const row = screen.getByText(component.name).closest('tr') as HTMLElement
      expect(row).not.toBeNull()
      if (availability.rollup.availability_pct !== null) {
        expect(within(row).getByText(`${availability.rollup.availability_pct.toFixed(2)}%`)).toBeInTheDocument()
      }
    }
  })

  it('expands a multi-signal component to reveal its per-signal children (AC1)', async () => {
    const user = userEvent.setup()
    render(<AvailabilityPage />)

    await screen.findByRole('table')

    const multiSignal = FIXTURE_TOPOLOGY.find((c) => c.id === 'sockshop-frontend')!
    const expandButton = screen.getByRole('button', { name: new RegExp(multiSignal.name) })
    expect(expandButton).toHaveAttribute('aria-expanded', 'false')

    // Children not shown until expanded.
    for (const signal of multiSignal.signals) {
      expect(screen.queryByText(signal.signal_key)).not.toBeInTheDocument()
    }

    await user.click(expandButton)

    expect(expandButton).toHaveAttribute('aria-expanded', 'true')
    const componentAvailability = FIXTURE_AVAILABILITY_BY_COMPONENT[multiSignal.id]
    for (const signal of componentAvailability.signals) {
      const topologySignal = multiSignal.signals.find(
        (s) => s.signal_key === signal.signal_key,
      )!
      const signalKeyEl = screen.getByText(signal.signal_key)
      const childRow = signalKeyEl.closest('tr') as HTMLElement
      expect(childRow).not.toBeNull()
      expect(within(childRow).getByText(topologySignal.name)).toBeInTheDocument()
      expect(
        within(childRow).getByText(`${signal.availability_pct?.toFixed(2)}%`),
      ).toBeInTheDocument()
    }

    // Collapsing hides them again.
    await user.click(expandButton)
    expect(expandButton).toHaveAttribute('aria-expanded', 'false')
    for (const signal of multiSignal.signals) {
      expect(screen.queryByText(signal.signal_key)).not.toBeInTheDocument()
    }
  })

  it('renders a single-signal component the same expandable way as multi-signal (AC1)', async () => {
    const user = userEvent.setup()
    render(<AvailabilityPage />)

    await screen.findByRole('table')

    const single = FIXTURE_TOPOLOGY.find((c) => c.id === 'sockshop-catalogue')!
    const expandButton = screen.getByRole('button', { name: new RegExp(single.name) })
    await user.click(expandButton)

    const [signal] = single.signals
    expect(screen.getByText(signal.signal_key)).toBeInTheDocument()
  })

  it('renders a zero-signal component with its honest all-None rollup and no expand control (AC1, AC3)', async () => {
    render(<AvailabilityPage />)

    await screen.findByRole('table')

    const zeroSignal = FIXTURE_TOPOLOGY.find((c) => c.id === 'sockshop-orders')!
    // No expand button for a component with no signals.
    expect(
      screen.queryByRole('button', { name: new RegExp(zeroSignal.name) }),
    ).not.toBeInTheDocument()

    const row = screen.getByText(zeroSignal.name).closest('tr') as HTMLElement
    expect(row).not.toBeNull()
    // Null availability/completeness renders as "no data", never 0%/NaN%.
    expect(within(row).getAllByText('no data').length).toBeGreaterThan(0)
    expect(within(row).queryByText('0.00%')).not.toBeInTheDocument()
    expect(within(row).queryByText(/NaN/)).not.toBeInTheDocument()
  })
})
