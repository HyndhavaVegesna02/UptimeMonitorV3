import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HttpResponse, http } from 'msw'
import { describe, expect, it } from 'vitest'
import type { ComponentTopologyDTO } from '../../api/types'
import { FIXTURE_COMPONENT_AVAILABILITY } from '../../mocks/handlers/availability'
import { server } from '../../mocks/server'
import { ComponentAvailabilityCard } from './ComponentAvailabilityCard'

const COMPONENT: ComponentTopologyDTO = {
  id: 'http-check',
  name: 'HTTP Check',
  signals: [{ signal_key: 'http-check', name: 'HTTP Check', interval_seconds: 120, component_id: 'http-check' }],
}

const SINCE = '2026-07-20T18:20:42.000Z'
const UNTIL = '2026-07-21T18:20:42.000Z'

/** Column order: name/toggle, Availability, Completeness, Total, Passing,
 * Maintenance, Down, Gap, Locations. `role="row"` has no name-from-content
 * (ARIA accname spec) - rows are addressed structurally, not by name. */
function cellText(row: HTMLElement): string[] {
  return within(row)
    .getAllByRole('cell')
    .map((cell) => cell.textContent ?? '')
}

/** The always-visible rollup row: `rows[0]` is the `<thead>` header row,
 * `rows[1]` is the rollup row (the only row rendered while collapsed). */
function getRollupRow(): HTMLElement {
  const rows = screen.getAllByRole('row')
  return rows[1]
}

function renderCard(component: ComponentTopologyDTO = COMPONENT) {
  return render(<ComponentAvailabilityCard component={component} since={SINCE} until={UNTIL} />)
}

describe('ComponentAvailabilityCard', () => {
  it('shows a loading region before the fetch settles', () => {
    renderCard()
    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('renders the rollup row from the real captured fixture: fraction x100, real counts, honest 0-locations quirk', async () => {
    renderCard()
    await screen.findByRole('table')

    const cells = cellText(getRollupRow())
    expect(cells[0]).toContain('HTTP Check')

    // rollup: availability_pct 1.0, completeness_pct 0.0930555, total 65,
    // passing 65, maintenance 0, down = 65-65-0 = 0, gap 655, locations 0
    // (verified live quirk - rendered honestly, not "fixed" client-side).
    expect(cells[1]).toContain('100.00')
    expect(cells[2]).toContain('9.31')
    expect(cells[3]).toBe('65')
    expect(cells[4]).toBe('65')
    expect(cells[5]).toBe('0')
    expect(cells[6]).toBe('0')
    expect(cells[7]).toBe('655')
    expect(cells[8]).toBe('0')
  })

  it('flags low completeness (the real 9.31% sample) without treating it as "no data"', async () => {
    renderCard()
    await screen.findByRole('table')

    expect(within(getRollupRow()).getByText(/low data/i)).toBeInTheDocument()
  })

  it('renders "No data" (never a fabricated 0%) when availability_pct/completeness_pct are null, and does not flag low completeness', async () => {
    server.use(
      http.get('/api/v1/availability/component/:componentId', () =>
        HttpResponse.json({
          component_id: 'http-check',
          rollup: {
            availability_pct: null,
            completeness_pct: null,
            total_verdicts: 0,
            passing_verdicts: 0,
            maintenance_verdicts: 0,
            gap_verdicts: 0,
            distinct_locations: 0,
            window: '24h',
            computed_at: '2026-07-21T18:20:42Z',
          },
          signals: [],
        }),
      ),
    )
    renderCard()
    await screen.findByRole('table')

    const cells = cellText(getRollupRow())
    expect(cells[1]).toBe('No data')
    expect(cells[2]).toBe('No data')
    expect(screen.queryByText(/low data/i)).toBeNull()
  })

  it('offers no drill-down affordance for a zero-signal component (no crash)', async () => {
    server.use(
      http.get('/api/v1/availability/component/:componentId', () =>
        HttpResponse.json({ ...FIXTURE_COMPONENT_AVAILABILITY['http-check'], signals: [] }),
      ),
    )
    renderCard({ id: 'http-check', name: 'HTTP Check', signals: [] })

    await screen.findByRole('table')
    expect(screen.queryByRole('button', { name: /signal/i })).toBeNull()
  })

  it('expands to reveal the real http-check signal child, keyboard-operable, with aria-expanded/aria-controls', async () => {
    const user = userEvent.setup()
    renderCard()
    await screen.findByRole('table')

    const toggle = screen.getByRole('button', { name: /signal/i })
    expect(toggle).toHaveAttribute('aria-expanded', 'false')
    const controlsId = toggle.getAttribute('aria-controls')
    expect(controlsId).toBeTruthy()
    const signalsRegion = document.getElementById(controlsId!)!
    expect(signalsRegion).toHaveAttribute('hidden')
    // Collapsed: only the header + rollup row are in the accessibility tree.
    expect(screen.getAllByRole('row')).toHaveLength(2)

    toggle.focus()
    await user.keyboard('{Enter}')

    expect(toggle).toHaveAttribute('aria-expanded', 'true')
    expect(signalsRegion).not.toHaveAttribute('hidden')

    const rows = screen.getAllByRole('row')
    expect(rows).toHaveLength(3)
    const signalRow = rows[2]
    const signalCells = cellText(signalRow)
    expect(signalCells[0]).toContain('HTTP Check')
    // The signal row's real distinct_locations (2) reads honestly different
    // from the rollup row's quirked 0 - proves no client "fix-up".
    expect(signalCells[8]).toBe('2')

    await user.keyboard('{Enter}')
    expect(toggle).toHaveAttribute('aria-expanded', 'false')
    expect(signalsRegion).toHaveAttribute('hidden')
    expect(screen.getAllByRole('row')).toHaveLength(2)
  })

  it('shows an error state with a retry action on a fetch failure, never fabricating a rollup', async () => {
    server.use(
      http.get('/api/v1/availability/component/:componentId', () =>
        HttpResponse.json({ detail: 'boom' }, { status: 500 }),
      ),
    )
    renderCard()

    expect(await screen.findByRole('alert')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Retry' })).toBeInTheDocument()
    expect(screen.queryByRole('table')).toBeNull()
  })

  it('surfaces a 404 unknown component as a region error, not a crash', async () => {
    renderCard({ id: 'unknown-component', name: 'Unknown', signals: [] })

    expect(await screen.findByRole('alert')).toBeInTheDocument()
  })
})
