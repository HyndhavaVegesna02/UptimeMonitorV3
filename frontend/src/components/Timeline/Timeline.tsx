import type { HTMLAttributes, LiHTMLAttributes, ReactNode } from 'react'
import type { HealthStatus } from '../StatusBadge/StatusBadge'
import { cx } from '../../lib/cx'
import './Timeline.css'

export type TimelineProps = HTMLAttributes<HTMLUListElement>

/** Vertical line + dot list primitive (STORY-055 AC5) — used by Publications
 * for the publication log. A plain semantic `<ul>`; each `TimelineItem` is a
 * `<li>` so assistive tech reports the list length/position naturally. */
export function Timeline({ className, children, ...rest }: TimelineProps) {
  return (
    <ul className={cx('timeline', className)} {...rest}>
      {children}
    </ul>
  )
}

export interface TimelineItemProps extends LiHTMLAttributes<HTMLLIElement> {
  /** Which token-driven color paints this item's dot. Defaults to neutral —
   * the dot is always decorative, never the sole carrier of the item's
   * meaning (that lives in the visible `children` content). */
  tone?: HealthStatus | 'neutral'
  /** Hides the connector line below this item — pass for the last entry in
   * the list so the rail doesn't trail off past the final dot. */
  isLast?: boolean
  children?: ReactNode
}

export function TimelineItem({
  tone = 'neutral',
  isLast = false,
  className,
  children,
  ...rest
}: TimelineItemProps) {
  return (
    <li className={cx('timeline__item', className)} {...rest}>
      <span className="timeline__rail" aria-hidden="true">
        <span
          className={cx('timeline__dot', `timeline__dot--${tone}`)}
          aria-hidden="true"
        />
        {!isLast ? <span className="timeline__line" /> : null}
      </span>
      <div className="timeline__content">{children}</div>
    </li>
  )
}
