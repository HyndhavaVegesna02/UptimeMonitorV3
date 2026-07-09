import type { ReactNode } from 'react'
import { cx } from '../../lib/cx'
import './SummaryCard.css'

export type SummaryCardTone = 'ok' | 'up' | 'degraded' | 'partial' | 'down' | 'accent' | 'neutral'

export interface SummaryCardProps {
  label: string
  value: ReactNode
  sub?: ReactNode
  /** Which token-driven color paints the dot + value (STORY-055 AC5). Both 'ok' and 'up' are supported and map to the same token-driven up status color. */
  tone?: SummaryCardTone
  className?: string
}

/**
 * Labeled stat card (STORY-055 AC5) — dot + uppercase label + big mono
 * value + sub line, per the sprint-38 Dashboard summary-card row. The dot
 * is decorative (`aria-hidden`); the label and value are always visible
 * text, so the tone is never the sole carrier of meaning.
 */
export function SummaryCard({
  label,
  value,
  sub,
  tone = 'neutral',
  className,
}: SummaryCardProps) {
  return (
    <div className={cx('summary-card', `summary-card--${tone}`, className)}>
      <div className="summary-card__heading">
        <span className="summary-card__dot" aria-hidden="true" />
        <span className="summary-card__label">{label}</span>
      </div>
      <div className="summary-card__value">{value}</div>
      {sub ? <div className="summary-card__sub">{sub}</div> : null}
    </div>
  )
}
