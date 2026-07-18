import { cx } from '../../lib/cx'
import './LatencySpark.css'

export interface LatencySparkProps {
  /** Oldest -> newest latency values (ms), e.g.
   * `features/dashboard/latencyPoints.ts::buildLatencyPoints`'s output.
   * Renders an explicit "No data" state (never a fabricated flat line) when
   * empty. */
  points: number[]
  /** Accessible label prefix — combined with "no data" or "latest N ms"
   * into the SVG's `aria-label`/`<title>` (STORY-105, ui-ux-pro-max chart
   * guidance: a sparkline is a "tiny data volume, no chart library" inline
   * SVG, but still needs a text-equivalent accessible name). */
  label: string
  className?: string
}

const VIEWBOX_WIDTH = 100
const VIEWBOX_HEIGHT = 24
/** Keeps a flat/near-flat series off the very top/bottom edge of the
 * viewBox so the line is never clipped by the stroke width. */
const VERTICAL_PADDING = 3

/**
 * Inline-SVG latency sparkline (STORY-105, design brief §IA — the
 * per-component tile's "latency spark"; ui-ux-pro-max chart-domain guidance:
 * data refreshes ~1/min so this is a static periodic-refresh visual, never a
 * streaming/ticker chart, and the data volume is small enough that a
 * hand-rolled inline `<svg>` is correct — no chart library, no new
 * dependency). Axis-less (mono, dense bento tile), always paired with a
 * visible text-equivalent: the `aria-label`/`<title>` states the latest
 * value in words, never color/shape alone.
 */
export function LatencySpark({ points, label, className }: LatencySparkProps) {
  if (points.length === 0) {
    return (
      <div
        className={cx('latency-spark', 'latency-spark--empty', className)}
        role="img"
        aria-label={`${label}: no data`}
      >
        <span className="latency-spark__no-data">No data</span>
      </div>
    )
  }

  const latest = points[points.length - 1]
  const accessibleName = `${label}: latest ${latest} ms`

  const min = Math.min(...points)
  const max = Math.max(...points)
  const range = max - min

  const usableHeight = VIEWBOX_HEIGHT - VERTICAL_PADDING * 2
  const stepX = points.length > 1 ? VIEWBOX_WIDTH / (points.length - 1) : 0

  const coordinates = points.map((point, index) => {
    const x = points.length > 1 ? index * stepX : VIEWBOX_WIDTH / 2
    // A flat (or single-point) series draws a horizontal mid-line rather
    // than dividing by a zero range.
    const y =
      range === 0
        ? VIEWBOX_HEIGHT / 2
        : VERTICAL_PADDING + usableHeight - ((point - min) / range) * usableHeight
    return `${x},${y}`
  })

  return (
    <svg
      className={cx('latency-spark', className)}
      viewBox={`0 0 ${VIEWBOX_WIDTH} ${VIEWBOX_HEIGHT}`}
      preserveAspectRatio="none"
      role="img"
      aria-label={accessibleName}
    >
      <title>{accessibleName}</title>
      <polyline
        className="latency-spark__line"
        points={coordinates.join(' ')}
        fill="none"
      />
    </svg>
  )
}
