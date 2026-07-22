import { describe, expect, it } from 'vitest'
import type { ObservationDTO } from '../../api/types'
import { AXIS_GUTTER, deriveChartData } from './deriveChartData'

// Real-shaped sample (live-api-samples.md), most-recent first.
const OBSERVATIONS: ObservationDTO[] = [
  { signal_key: 'http-check', observed_at: '2026-07-21T07:58:41.133000Z', health: 'up', location: 'SYNTHETIC_LOCATION-0000000000000060', latency_ms: 588, response_status_code: 200, check_type: 'http' },
  { signal_key: 'http-check', observed_at: '2026-07-21T07:57:41.375000Z', health: 'up', location: 'SYNTHETIC_LOCATION-0000000000000047', latency_ms: 951, response_status_code: 200, check_type: 'http' },
  { signal_key: 'http-check', observed_at: '2026-07-21T07:56:41.164000Z', health: 'up', location: 'SYNTHETIC_LOCATION-0000000000000047', latency_ms: 293, response_status_code: 200, check_type: 'http' },
  { signal_key: 'http-check', observed_at: '2026-07-21T07:56:41.164000Z', health: 'up', location: 'SYNTHETIC_LOCATION-0000000000000060', latency_ms: 561, response_status_code: 200, check_type: 'http' },
  { signal_key: 'http-check', observed_at: '2026-07-21T07:54:41.274000Z', health: 'up', location: 'SYNTHETIC_LOCATION-0000000000000060', latency_ms: 570, response_status_code: 200, check_type: 'http' },
  { signal_key: 'http-check', observed_at: '2026-07-21T07:53:41.570000Z', health: 'up', location: 'SYNTHETIC_LOCATION-0000000000000047', latency_ms: 331, response_status_code: 200, check_type: 'http' },
  { signal_key: 'http-check', observed_at: '2026-07-21T07:52:41.508000Z', health: 'up', location: 'SYNTHETIC_LOCATION-0000000000000060', latency_ms: 904, response_status_code: 200, check_type: 'http' },
  { signal_key: 'http-check', observed_at: '2026-07-21T07:51:41.147000Z', health: 'up', location: 'SYNTHETIC_LOCATION-0000000000000047', latency_ms: 356, response_status_code: 200, check_type: 'http' },
]

describe('deriveChartData', () => {
  it('builds one point per valid observation, oldest first', () => {
    const chart = deriveChartData(OBSERVATIONS, { windowLabel: 'last 24 hours' })
    expect(chart.points).toHaveLength(8)
    expect(chart.points[0].latencyMs).toBe(356)
    expect(chart.points[chart.points.length - 1].latencyMs).toBe(588)
  })

  it('computes the average latency across the window', () => {
    const chart = deriveChartData(OBSERVATIONS, { windowLabel: 'last 24 hours' })
    expect(chart.avgLatencyMs).toBe(569)
  })

  it('calls out the highest-latency point as the spike, with its location', () => {
    const chart = deriveChartData(OBSERVATIONS, { windowLabel: 'last 24 hours' })
    expect(chart.spike).not.toBeNull()
    expect(chart.spike?.latencyMs).toBe(951)
    expect(chart.spike?.location).toContain('0047')
  })

  it('builds a descriptive aria-label including the average and the spike', () => {
    const chart = deriveChartData(OBSERVATIONS, { windowLabel: 'last 24 hours' })
    expect(chart.ariaLabel).toContain('last 24 hours')
    expect(chart.ariaLabel).toContain('569')
    expect(chart.ariaLabel).toContain('951')
  })

  it('produces an SVG line path with one segment per point', () => {
    const chart = deriveChartData(OBSERVATIONS, { windowLabel: 'last 24 hours' })
    expect(chart.linePath.startsWith('M')).toBe(true)
    // 8 points -> 1 "M" + 7 "L" commands
    expect(chart.linePath.match(/L/g)?.length).toBe(7)
  })

  it('handles an empty window without crashing (no fabricated points)', () => {
    const chart = deriveChartData([], { windowLabel: 'last 24 hours' })
    expect(chart.points).toHaveLength(0)
    expect(chart.avgLatencyMs).toBeNull()
    expect(chart.spike).toBeNull()
    expect(chart.linePath).toBe('')
    expect(chart.ariaLabel).toContain('No response-time data')
  })

  it('handles a single-point window (no division by zero)', () => {
    const chart = deriveChartData([OBSERVATIONS[0]], { windowLabel: 'last 24 hours' })
    expect(chart.points).toHaveLength(1)
    expect(chart.avgLatencyMs).toBe(588)
    expect(chart.spike?.latencyMs).toBe(588)
  })

  it('uses a 0 baseline for the bottom gridline, never the data minimum (AC1)', () => {
    const chart = deriveChartData(OBSERVATIONS, { windowLabel: 'last 24 hours' })
    const bottomGridline = chart.gridlines[chart.gridlines.length - 1]
    // The real data minimum is 293ms; the bottom tick must be 0, not 293.
    expect(bottomGridline.label).toBe('0 ms')
  })

  it('produces rounded "nice" tick values derived from a niced max, not raw data-derived values (AC2)', () => {
    const chart = deriveChartData(OBSERVATIONS, { windowLabel: 'last 24 hours' })
    // Real captured max is 951ms (live-api-samples.md) -> niced max 1500,
    // step 500 -> nice round ticks, never the old max/min-derived
    // 951/809/536/262-style values.
    expect(chart.gridlines.map((gridline) => gridline.label)).toEqual([
      '1,500 ms',
      '1,000 ms',
      '500 ms',
      '0 ms',
    ])
  })

  it('scales the plotted line against [0, nicedMax] so the 0 baseline is real, not just a label (AC1)', () => {
    const chart = deriveChartData(OBSERVATIONS, { windowLabel: 'last 24 hours' })
    const spikePoint = chart.points.find((point) => point.latencyMs === 951)!
    // niceMax=1500, padding=20, usableHeight=178 (default height 218):
    // y = 20 + (1 - 951/1500) * 178
    expect(spikePoint.y).toBeCloseTo(20 + (1 - 951 / 1500) * 178, 1)

    // The scale must be independent of the dataset's minimum: dropping the
    // lowest-latency observation must NOT move the y-position of the same
    // 951ms point (a min-based scale, the old defect, would shift it).
    const withoutMin = OBSERVATIONS.filter((observation) => observation.latency_ms !== 293)
    const chartWithoutMin = deriveChartData(withoutMin, { windowLabel: 'last 24 hours' })
    const spikePointWithoutMin = chartWithoutMin.points.find((point) => point.latencyMs === 951)!
    expect(spikePointWithoutMin.y).toBeCloseTo(spikePoint.y, 5)
  })

  it('reserves an axis gutter: labels sit left of the plot, never over the gridlines/line (AC3)', () => {
    const chart = deriveChartData(OBSERVATIONS, { windowLabel: 'last 24 hours' })
    expect(chart.gridlines.length).toBeGreaterThan(0)
    for (const gridline of chart.gridlines) {
      expect(gridline.labelX).toBeLessThan(AXIS_GUTTER)
      // Vertically centered on its own gridline, not offset above it.
      expect(gridline.labelY).toBe(gridline.y)
    }
    for (const point of chart.points) {
      expect(point.x).toBeGreaterThanOrEqual(AXIS_GUTTER)
    }
  })

  it('ignores observations with a null latency rather than plotting a fabricated 0', () => {
    const withGap: ObservationDTO[] = [
      ...OBSERVATIONS,
      { signal_key: 'http-check', observed_at: '2026-07-21T07:50:00Z', health: 'down', location: 'SYNTHETIC_LOCATION-0000000000000047', latency_ms: null, response_status_code: null, check_type: 'http' },
    ]
    const chart = deriveChartData(withGap, { windowLabel: 'last 24 hours' })
    expect(chart.points).toHaveLength(8)
  })
})
