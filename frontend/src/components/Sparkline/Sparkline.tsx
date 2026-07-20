import { cx } from '../../lib/cx'
import './Sparkline.css'

export type SparklineTone = 'accent' | 'positive' | 'negative'

export interface SparklineProps {
  /** Ordered data points, oldest first. */
  data: number[]
  width?: number
  height?: number
  tone?: SparklineTone
  className?: string
}

const VIEWBOX_WIDTH = 120
const VIEWBOX_HEIGHT = 30
const PADDING = 2

/**
 * Minimal inline-SVG trend line (STORY-120 AC5) — a small, purely
 * decorative visual next to a KPI number; the number + delta pill already
 * carry the accessible meaning, so the sparkline itself is `aria-hidden`.
 * The one-shot entrance fade (opacity + a small translateY, `transform`/
 * `opacity` only per AC5) is `prefers-reduced-motion` guarded
 * (Sparkline.css) — no animation on data refresh.
 */
export function Sparkline({
  data,
  width = VIEWBOX_WIDTH,
  height = VIEWBOX_HEIGHT,
  tone = 'accent',
  className,
}: SparklineProps) {
  const points = toPoints(data, width, height)

  return (
    <svg
      className={cx('sparkline', `sparkline--${tone}`, className)}
      width="100%"
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      preserveAspectRatio="none"
      aria-hidden="true"
    >
      {points ? (
        <polyline
          className="sparkline__line"
          fill="none"
          strokeWidth={2}
          strokeLinecap="round"
          strokeLinejoin="round"
          points={points}
        />
      ) : null}
    </svg>
  )
}

function toPoints(data: number[], width: number, height: number): string | null {
  if (data.length === 0) {
    return null
  }

  const min = Math.min(...data)
  const max = Math.max(...data)
  const range = max - min
  const usableHeight = height - PADDING * 2
  const step = data.length > 1 ? width / (data.length - 1) : 0

  return data
    .map((value, index) => {
      const x = step * index
      // A flat series (range === 0) draws a level line at mid-height
      // instead of dividing by zero.
      const normalized = range === 0 ? 0.5 : (value - min) / range
      const y = PADDING + (1 - normalized) * usableHeight
      return `${x},${y}`
    })
    .join(' ')
}
