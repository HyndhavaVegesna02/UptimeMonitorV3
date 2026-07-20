import { ArrowUp, ArrowDown } from '@phosphor-icons/react'
import type { Icon as PhosphorIcon } from '@phosphor-icons/react'
import type { ReactNode } from 'react'
import { cx } from '../../lib/cx'
import { Icon } from '../Icon/Icon'
import './SummaryCard.css'

export interface SummaryCardDelta {
  text: string
  /** Color, not direction — a latency DECREASE is `positive` even though its
   * arrow points down (prototype: "latency down = good -> green"). */
  sentiment: 'positive' | 'negative'
  /** Arrow direction; defaults to matching `sentiment` (up = positive). */
  direction?: 'up' | 'down'
}

export interface SummaryCardProps {
  icon: PhosphorIcon
  label: string
  value: ReactNode
  unit?: string
  sub?: ReactNode
  delta?: SummaryCardDelta
  /** Visual "needs attention" treatment (sky-tinted, e.g. pending approvals). */
  attention?: boolean
  /** When given, the whole card renders as a link (STORY-120 AC5: the
   * "Pending approvals" KPI is a single clickable card, not a card + a
   * separate link). */
  href?: string
  /** Extra content below the value — a Sparkline, a mini-segment bar, etc. */
  children?: ReactNode
}

/**
 * KPI summary card (STORY-120 AC5): icon chip, label, big tabular-nums
 * value (+ optional unit/delta/sub line), and an extra slot for a
 * sparkline or mini-segment strip. Hover-lift, `:active` press (when a
 * link), and `:focus-visible` all live in SummaryCard.css, guarded by
 * `prefers-reduced-motion`.
 */
export function SummaryCard({
  icon,
  label,
  value,
  unit,
  sub,
  delta,
  attention = false,
  href,
  children,
}: SummaryCardProps) {
  const deltaDirection = delta?.direction ?? (delta?.sentiment === 'positive' ? 'up' : 'down')
  const deltaIcon = deltaDirection === 'up' ? ArrowUp : ArrowDown
  const className = cx('panel', 'summary-card', attention && 'summary-card--attention')

  const content = (
    <>
      <div className="summary-card__head">
        <span className="summary-card__chip" aria-hidden="true">
          <Icon icon={icon} aria-hidden size={17} />
        </span>
        {delta ? (
          <span className={cx('summary-card__delta', `summary-card__delta--${delta.sentiment}`)}>
            <Icon icon={deltaIcon} aria-hidden size={12} />
            {delta.text}
          </span>
        ) : null}
      </div>
      <div className="summary-card__body">
        <div className="summary-card__label">{label}</div>
        <div className="summary-card__value-row">
          <span className="summary-card__value">
            {value}
            {unit ? <span className="summary-card__unit">{unit}</span> : null}
          </span>
        </div>
        {sub ? <div className="summary-card__sub">{sub}</div> : null}
      </div>
      {children ? <div className="summary-card__extra">{children}</div> : null}
    </>
  )

  if (href) {
    return (
      <a href={href} className={className}>
        {content}
      </a>
    )
  }

  return <article className={className}>{content}</article>
}
