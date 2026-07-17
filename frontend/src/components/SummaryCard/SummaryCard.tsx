import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { cx } from '../../lib/cx'
import './SummaryCard.css'

export type SummaryCardTone = 'ok' | 'up' | 'degraded' | 'partial' | 'down' | 'accent' | 'neutral'

export interface SummaryCardProps {
  label: string
  value: ReactNode
  sub?: ReactNode
  /** Which token-driven color paints the dot + value (STORY-055 AC5). Both 'ok' and 'up' are supported and map to the same token-driven up status color. */
  tone?: SummaryCardTone
  /**
   * When true, a numeric `value` of exactly 0 overrides `tone` to
   * `'neutral'` (STORY-099 AC1, journal D4 — color carries state only when
   * non-nominal: a "bad" bucket sitting at 0 is good news, not an alert).
   * `value` above 0 restores the given `tone` unchanged. A non-numeric
   * `value` (e.g. a pre-formatted percentage string) is never neutralized —
   * this only inspects a REAL `0`, never a string that merely looks like
   * one. Call sites that always want their tone (e.g. Operational/"up")
   * simply omit this prop; it defaults to off.
   */
  neutralAtZero?: boolean
  /**
   * When given, the whole card renders as a single routed `Link` (STORY-099
   * AC2 — cross-tab awareness action cards): one focusable/clickable
   * element for the entire card, never a nested control. Omit for the
   * plain, non-interactive card (unchanged default).
   */
  href?: string
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
  neutralAtZero = false,
  href,
  className,
}: SummaryCardProps) {
  const isZero = neutralAtZero && typeof value === 'number' && value === 0
  const effectiveTone = isZero ? 'neutral' : tone

  const content = (
    <>
      <div className="summary-card__heading">
        <span className="summary-card__dot" aria-hidden="true" />
        <span className="summary-card__label">{label}</span>
      </div>
      <div className="summary-card__value">{value}</div>
      {sub ? <div className="summary-card__sub">{sub}</div> : null}
    </>
  )

  const cardClassName = cx(
    'summary-card',
    `summary-card--${effectiveTone}`,
    href && 'summary-card--interactive',
    className,
  )

  if (href) {
    return (
      <Link to={href} className={cardClassName}>
        {content}
      </Link>
    )
  }

  return <div className={cardClassName}>{content}</div>
}
