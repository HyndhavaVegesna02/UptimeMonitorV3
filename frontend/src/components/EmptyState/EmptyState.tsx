import './EmptyState.css'

export interface EmptyStateProps {
  message: string
  detail?: string
}

/**
 * Explicit empty state for list-rendering surfaces (STORY-120 AC5 — "every
 * list-rendering surface has a tested empty state").
 */
export function EmptyState({ message, detail }: EmptyStateProps) {
  return (
    <div className="empty-state">
      <p className="empty-state__message">{message}</p>
      {detail ? <p className="empty-state__detail">{detail}</p> : null}
    </div>
  )
}
