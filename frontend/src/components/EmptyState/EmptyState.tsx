import { cx } from '../../lib/cx'
import './EmptyState.css'

export interface EmptyStateProps {
  message: string
  detail?: string
  /** Renders the compact modifier (no block padding, left-aligned) for
   * embedding inside a tight grain that already has its own padding — e.g.
   * a `SummaryCard`'s KPI value area (STORY-140 AC1). The default (full,
   * centered, padded block) stays the standard for whole-panel
   * list-rendering surfaces. */
  compact?: boolean
}

/**
 * Explicit empty state for list-rendering surfaces (STORY-120 AC5 — "every
 * list-rendering surface has a tested empty state") — and, via `compact`
 * (STORY-140 AC1), for a smaller grain like a single KPI card that has no
 * data yet, so that grain gets the SAME idiom rather than a one-off string.
 */
export function EmptyState({ message, detail, compact = false }: EmptyStateProps) {
  return (
    <div className={cx('empty-state', compact && 'empty-state--compact')}>
      <p className="empty-state__message">{message}</p>
      {detail ? <p className="empty-state__detail">{detail}</p> : null}
    </div>
  )
}
