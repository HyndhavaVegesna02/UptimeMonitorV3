import type { ObservationDTO } from '../../api/types'

export interface ChartPoint {
  x: number
  y: number
  observedAt: string
  latencyMs: number
  location: string
}

export interface ChartSpike {
  x: number
  y: number
  latencyMs: number
  observedAt: string
  location: string
}

export interface ChartGridline {
  y: number
  label: string
}

export interface ChartData {
  points: ChartPoint[]
  linePath: string
  areaPath: string
  avgLatencyMs: number | null
  spike: ChartSpike | null
  gridlines: ChartGridline[]
  ariaLabel: string
}

export interface DeriveChartDataOptions {
  width?: number
  height?: number
  /** Vertical padding reserved inside `height` so the line never touches
   * the plot edges. */
  padding?: number
  /** Human-readable window description used in the aria-label, e.g. "last
   * 24 hours" — never hardcoded inside this function. */
  windowLabel: string
}

const DEFAULT_WIDTH = 720
const DEFAULT_HEIGHT = 218
const DEFAULT_PADDING = 20
const GRIDLINE_COUNT = 4

/**
 * Derives the response-time chart's plot geometry + accessible description
 * from real per-signal history (STORY-122 AC2). Never fabricates a data
 * point: observations with a `null` latency are skipped rather than
 * plotted as 0, and an empty/single-point window degrades gracefully (no
 * division by zero, no crash).
 */
export function deriveChartData(
  observations: ObservationDTO[],
  { width = DEFAULT_WIDTH, height = DEFAULT_HEIGHT, padding = DEFAULT_PADDING, windowLabel }: DeriveChartDataOptions,
): ChartData {
  // `observations` is most-recent-first (ObservationDTO ordering); the
  // chart reads left (oldest) to right (newest).
  const valid = [...observations]
    .reverse()
    .filter((observation): observation is ObservationDTO & { latency_ms: number } => observation.latency_ms !== null)

  if (valid.length === 0) {
    return {
      points: [],
      linePath: '',
      areaPath: '',
      avgLatencyMs: null,
      spike: null,
      gridlines: [],
      ariaLabel: `No response-time data available for the ${windowLabel}.`,
    }
  }

  const latencies = valid.map((observation) => observation.latency_ms)
  const minLatency = Math.min(...latencies)
  const maxLatency = Math.max(...latencies)
  const avgLatencyMs = Math.round(latencies.reduce((total, value) => total + value, 0) / latencies.length)
  const range = maxLatency - minLatency
  const usableHeight = height - padding * 2
  const xStep = valid.length > 1 ? width / (valid.length - 1) : 0

  const points: ChartPoint[] = valid.map((observation, index) => {
    const x = valid.length > 1 ? xStep * index : width / 2
    const normalized = range === 0 ? 0.5 : (observation.latency_ms - minLatency) / range
    const y = padding + (1 - normalized) * usableHeight
    return {
      x,
      y,
      observedAt: observation.observed_at,
      latencyMs: observation.latency_ms,
      location: observation.location,
    }
  })

  const linePath = points
    .map((point, index) => `${index === 0 ? 'M' : 'L'}${point.x.toFixed(1)},${point.y.toFixed(1)}`)
    .join(' ')

  const areaPath = `${linePath} L${points[points.length - 1].x.toFixed(1)},${height} L${points[0].x.toFixed(1)},${height} Z`

  const spikePoint = points.reduce((worst, point) => (point.latencyMs > worst.latencyMs ? point : worst))
  const spike: ChartSpike = {
    x: spikePoint.x,
    y: spikePoint.y,
    latencyMs: spikePoint.latencyMs,
    observedAt: spikePoint.observedAt,
    location: spikePoint.location,
  }

  const gridlines: ChartGridline[] = Array.from({ length: GRIDLINE_COUNT }, (_, index) => {
    const fraction = index / (GRIDLINE_COUNT - 1)
    const y = padding + fraction * usableHeight
    const value = Math.round(maxLatency - fraction * range)
    return { y, label: `${value.toLocaleString('en-US')} ms` }
  })

  const ariaLabel = `Response time over the ${windowLabel}, averaging ${avgLatencyMs} milliseconds, with a spike to ${spike.latencyMs} milliseconds.`

  return { points, linePath, areaPath, avgLatencyMs, spike, gridlines, ariaLabel }
}
