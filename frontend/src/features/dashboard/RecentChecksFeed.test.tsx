import { render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { ComponentDTO } from '../../api/types'
import { deriveRecentChecks } from './deriveRecentChecks'
import type { RecentCheckRow } from './deriveRecentChecks'
import { RecentChecksFeed } from './RecentChecksFeed'
import type { SignalsMap } from './types'

const ROWS: RecentCheckRow[] = [
  { key: '1', componentName: 'HTTP Check', locationLabel: '…0047', relativeTime: '28s ago', latencyMs: 294, health: 'up' },
  { key: '2', componentName: 'HTTP Check', locationLabel: '…0060', relativeTime: '1 min ago', latencyMs: null, health: 'down' },
]

describe('RecentChecksFeed', () => {
  it('renders one row per recent check with component, location, relative time, latency, and health tag', () => {
    render(<RecentChecksFeed rows={ROWS} />)
    expect(screen.getAllByText('HTTP Check')).toHaveLength(2)
    expect(screen.getByText(/…0047/)).toBeInTheDocument()
    expect(screen.getByText(/28s ago/)).toBeInTheDocument()
    expect(screen.getByText('294')).toBeInTheDocument()
    expect(screen.getByText('Up')).toBeInTheDocument()
    expect(screen.getByText('Down')).toBeInTheDocument()
  })

  it('renders an em dash for a null latency rather than a fabricated 0', () => {
    render(<RecentChecksFeed rows={ROWS} />)
    expect(screen.getByText('—')).toBeInTheDocument()
  })

  it('renders an EmptyState when there are no recent checks', () => {
    render(<RecentChecksFeed rows={[]} />)
    expect(screen.getByText(/No recent checks/)).toBeInTheDocument()
  })

  describe('a confirmed live wire collision (STORY-136 AC1, same class STORY-130 fixed on History)', () => {
    let consoleErrorSpy: ReturnType<typeof vi.spyOn>

    beforeEach(() => {
      consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => undefined)
    })

    afterEach(() => {
      consoleErrorSpy.mockRestore()
    })

    it('renders exactly one row per observation, in sorted order, with no React duplicate-key warning, when two observations share an identical (signal_key, observed_at, location) triple', () => {
      const components: ComponentDTO[] = [{ id: 'http-check', name: 'HTTP Check', status: 'operational' }]
      const duplicateTriple = {
        signal_key: 'http-check',
        observed_at: '2026-07-21T20:24:41.129000Z',
        health: 'up' as const,
        location: 'SYNTHETIC_LOCATION-0000000000000060',
        latency_ms: 400,
        response_status_code: 200,
        check_type: 'http',
      }
      const older = { ...duplicateTriple, observed_at: '2026-07-21T20:20:00.000000Z', latency_ms: 100 }
      const signals: SignalsMap = {
        'http-check': {
          availability: {
            availability_pct: 1,
            completeness_pct: 1,
            total_verdicts: 3,
            passing_verdicts: 3,
            maintenance_verdicts: 0,
            gap_verdicts: 0,
            distinct_locations: 1,
            window: '24h',
            computed_at: '2026-07-21T20:24:41.129000Z',
          },
          history: [duplicateTriple, { ...duplicateTriple }, older],
        },
      }

      const rows = deriveRecentChecks(components, signals, new Date('2026-07-21T20:25:00Z'), 10)
      render(<RecentChecksFeed rows={rows} />)

      expect(screen.getAllByRole('listitem')).toHaveLength(3)
      // The two duplicate-triple rows (both 400ms) sort ahead of the older
      // (100ms) row — order is preserved despite the collision.
      const latencies = screen.getAllByRole('listitem').map((item) => item.textContent)
      expect(latencies[0]).toContain('400')
      expect(latencies[1]).toContain('400')
      expect(latencies[2]).toContain('100')

      const keyCollisionCalls = consoleErrorSpy.mock.calls.filter((call: unknown[]) =>
        call.some((arg) => typeof arg === 'string' && /same key|non-unique/i.test(arg)),
      )
      expect(keyCollisionCalls).toEqual([])
    })
  })
})
