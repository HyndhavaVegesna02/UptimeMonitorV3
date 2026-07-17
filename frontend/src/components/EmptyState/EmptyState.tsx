import type { IconName } from '../Icon/Icon'
import { Icon } from '../Icon/Icon'
import { cx } from '../../lib/cx'
import './EmptyState.css'

export type EmptyStateTone = 'neutral' | 'positive'

export interface EmptyStateProps {
  message: string
  detail?: string
  /** Optional decorative icon (STORY-097 AC3 — the designed icon+title+body
   * shape Approvals originated inline, now the shared primitive every
   * list-rendering surface can opt into). Omitted entirely renders the
   * original bare message/detail shape — a purely additive change. */
  icon?: IconName
  /** `'neutral'` (default) for an informational empty state; `'positive'`
   * for a "nothing to do" good-news state (e.g. Approvals' "Queue clear"). */
  tone?: EmptyStateTone
}

/** Explicit empty state for list-rendering surfaces (STORY-015a AC4; the
 * "every list-rendering surface has a tested empty state" working
 * agreement, frontend edition). STORY-097 AC3 added the optional icon/tone
 * so every adopting page renders the same designed shape instead of bare
 * text. */
export function EmptyState({ message, detail, icon, tone = 'neutral' }: EmptyStateProps) {
  return (
    <div className="empty-state">
      {icon ? (
        <span
          className={cx('empty-state__icon', `empty-state__icon--${tone}`)}
          aria-hidden="true"
        >
          <Icon name={icon} size={20} />
        </span>
      ) : null}
      <p className="empty-state__message">{message}</p>
      {detail ? <p className="empty-state__detail">{detail}</p> : null}
    </div>
  )
}
