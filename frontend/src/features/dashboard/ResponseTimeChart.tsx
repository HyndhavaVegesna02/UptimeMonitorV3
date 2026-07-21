import { EmptyState } from '../../components/EmptyState/EmptyState'
import type { ObservationDTO } from '../../api/types'
import { deriveChartData } from './deriveChartData'
import { locationLabel } from './locationLabel'
import './ResponseTimeChart.css'

export interface ResponseTimeChartProps {
  observations: ObservationDTO[]
  windowLabel: string
}

const CHART_WIDTH = 720
const CHART_HEIGHT = 218

/**
 * Inline-SVG response-time line/area chart (STORY-122 AC2) — a
 * periodic-refresh visual (ui-ux-pro-max chart domain: "Line Chart with
 * Highlights" for spike call-outs), never a real-time streaming ticker. No
 * chart library. The spike is marked with a shape (a distinct circle
 * element) AND a text legend — never colour alone.
 */
export function ResponseTimeChart({ observations, windowLabel }: ResponseTimeChartProps) {
  const chart = deriveChartData(observations, { windowLabel, width: CHART_WIDTH, height: CHART_HEIGHT })

  if (chart.points.length === 0) {
    return <EmptyState message="No response-time data available" detail={`for the ${windowLabel}`} />
  }

  return (
    <div className="response-time-chart">
      <svg
        className="response-time-chart__svg"
        viewBox={`0 0 ${CHART_WIDTH} ${CHART_HEIGHT}`}
        preserveAspectRatio="none"
        role="img"
        aria-label={chart.ariaLabel}
      >
        <g className="response-time-chart__gridlines">
          {chart.gridlines.map((gridline) => (
            <line key={gridline.y} x1={0} y1={gridline.y} x2={CHART_WIDTH} y2={gridline.y} />
          ))}
        </g>
        <g className="response-time-chart__axis-labels" aria-hidden="true">
          {chart.gridlines.map((gridline) => (
            <text key={gridline.y} x={4} y={gridline.y - 4}>
              {gridline.label}
            </text>
          ))}
        </g>
        <path className="response-time-chart__area" d={chart.areaPath} />
        <path className="response-time-chart__line" d={chart.linePath} />
        {chart.spike ? (
          <circle
            className="response-time-chart__spike"
            cx={chart.spike.x}
            cy={chart.spike.y}
            r={4}
          />
        ) : null}
      </svg>
      {chart.spike ? (
        <div className="response-time-chart__legend">
          <span className="response-time-chart__legend-item response-time-chart__legend-item--series">
            Response time
          </span>
          <span className="response-time-chart__legend-item response-time-chart__legend-item--spike">
            Spike at {locationLabel(chart.spike.location)} · {chart.spike.latencyMs.toLocaleString('en-US')}
            &nbsp;ms
          </span>
        </div>
      ) : null}
    </div>
  )
}
