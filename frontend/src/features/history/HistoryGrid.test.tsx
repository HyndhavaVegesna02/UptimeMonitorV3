import { render, screen, within } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { ComponentTopologyDTO, ObservationDTO } from '../../api/types'
import type { HistoryRow } from './mergeHistoryRows'
import { mergeHistoryRows } from './mergeHistoryRows'
import { HistoryGrid } from './HistoryGrid'

const ROWS: HistoryRow[] = [
  {
    key: '1',
    signalKey: 'http-check',
    componentName: 'HTTP Check',
    observedAt: '2026-07-21T07:58:41.133000Z',
    checkType: 'http',
    location: 'SYNTHETIC_LOCATION-0000000000000060',
    health: 'up',
    latencyMs: 588,
    responseStatusCode: 200,
  },
  {
    key: '2',
    signalKey: 'http-check',
    componentName: 'HTTP Check',
    observedAt: '2026-07-21T07:57:41.375000Z',
    checkType: 'http',
    location: 'SYNTHETIC_LOCATION-0000000000000047',
    health: 'down',
    latencyMs: null,
    responseStatusCode: null,
  },
]

describe('HistoryGrid', () => {
  it('renders one row per observation with the seven required columns', () => {
    render(<HistoryGrid rows={ROWS} />)
    const table = screen.getByRole('table')
    expect(within(table).getAllByRole('row')).toHaveLength(3) // header + 2 rows
    ;['Time', 'Check type', 'Component', 'Location', 'Result', 'Status code', 'Latency'].forEach((header) => {
      expect(within(table).getByRole('columnheader', { name: header })).toBeInTheDocument()
    })
  })

  it('renders the real captured values for the http-check row (timestamp, location tail, latency, code)', () => {
    render(<HistoryGrid rows={ROWS} />)
    expect(screen.getByText('Jul 21, 07:58:41')).toBeInTheDocument()
    expect(screen.getByText('…0060')).toBeInTheDocument()
    expect(screen.getByText('588')).toBeInTheDocument()
    expect(screen.getByText('200')).toBeInTheDocument()
  })

  it('renders "—" (never "0 ms"/"0") for null latency and null status code', () => {
    render(<HistoryGrid rows={ROWS} />)
    const secondRow = screen.getAllByRole('row')[2]
    expect(within(secondRow).getAllByText('—')).toHaveLength(2)
    expect(within(secondRow).queryByText('0 ms')).toBeNull()
    expect(within(secondRow).queryByText('0')).toBeNull()
  })

  it('conveys the result with a dot + text badge, never colour alone', () => {
    render(<HistoryGrid rows={ROWS} />)
    expect(screen.getByText('Up')).toBeInTheDocument()
    expect(screen.getByText('Down')).toBeInTheDocument()
  })

  it('scrolls the wide grid within its OWN overflow-x container, not the page body', () => {
    const { container } = render(<HistoryGrid rows={ROWS} />)
    const scrollContainer = container.querySelector('.history-grid__scroll')
    expect(scrollContainer).not.toBeNull()
    expect(scrollContainer?.contains(screen.getByRole('table'))).toBe(true)
  })

  describe('a confirmed live wire collision (reality gate 2026-07-22)', () => {
    let consoleErrorSpy: ReturnType<typeof vi.spyOn>

    beforeEach(() => {
      consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => undefined)
    })

    afterEach(() => {
      consoleErrorSpy.mockRestore()
    })

    it('renders exactly one row per input observation — never duplicated/omitted — when two observations share an identical (signal_key, observed_at, location) triple', () => {
      const topology: ComponentTopologyDTO[] = [
        { id: 'http-check', name: 'HTTP Check', signals: [{ signal_key: 'http-check', name: 'HTTP Check', interval_seconds: 120, component_id: 'http-check' }] },
      ]
      const duplicateTriple: ObservationDTO = {
        signal_key: 'http-check',
        observed_at: '2026-07-21T20:24:41.129000Z',
        health: 'up',
        location: 'SYNTHETIC_LOCATION-0000000000000060',
        latency_ms: 400,
        response_status_code: 200,
        check_type: 'http',
      }
      const observations = [duplicateTriple, { ...duplicateTriple }, { ...duplicateTriple, latency_ms: 401 }]

      const mergedRows = mergeHistoryRows(topology, { 'http-check': observations })
      render(<HistoryGrid rows={mergedRows} />)

      const table = screen.getByRole('table')
      expect(within(table).getAllByRole('row')).toHaveLength(1 + observations.length) // header + N

      // No "same key"/"non-unique" React reconciliation warning was logged.
      const keyCollisionCalls = consoleErrorSpy.mock.calls.filter((call: unknown[]) =>
        call.some((arg) => typeof arg === 'string' && /same key|non-unique/i.test(arg)),
      )
      expect(keyCollisionCalls).toEqual([])
    })
  })
})
