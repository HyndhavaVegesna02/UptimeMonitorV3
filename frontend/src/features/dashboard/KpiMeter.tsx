import { cx } from '../../lib/cx'
import type { KpiTone } from './deriveKpiTone'
import './KpiMeter.css'

export interface KpiMeterProps {
  /** Filled proportion, 0-1 (clamped). `1` renders a solid flat bar — used
   * when there is no ratio to show, only a tone (e.g. "Pending approvals",
   * which has no denominator). */
  ratio: number
  tone: KpiTone
}

/**
 * A compact filled-bar meter (STORY-138 AC3/AC4) — the KPI card footer
 * visual for the two cards with no real time series to plot as a
 * `Sparkline` ("Components healthy" / "Pending approvals"). Rendered inside
 * `SummaryCard`'s `.summary-card__extra` slot, which reserves the SAME
 * footprint height a `Sparkline` occupies (`SummaryCard.css`), so every KPI
 * card now carries a footer visual — none left visibly empty relative to
 * the others (AC3) — colored by the same rule-driven tone vocabulary the
 * Sparkline cards use (`deriveKpiTone.ts`, AC4). Purely decorative: the
 * card's own number/sub-line already carry the accessible meaning.
 */
export function KpiMeter({ ratio, tone }: KpiMeterProps) {
  const clamped = Math.min(1, Math.max(0, ratio))
  return (
    <div className="kpi-meter" aria-hidden="true">
      <div className={cx('kpi-meter__fill', `kpi-meter__fill--${tone}`)} style={{ width: `${clamped * 100}%` }} />
    </div>
  )
}
