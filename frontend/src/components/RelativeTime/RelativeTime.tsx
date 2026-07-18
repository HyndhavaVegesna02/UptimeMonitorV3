import { useRelativeTime } from '../../lib/formatTime'

export interface RelativeTimeProps {
  /** The raw ISO-8601 UTC instant (e.g. `observed_at`/`proposed_at`/
   * `published_at`) — placed verbatim on the rendered `<time dateTime>`
   * attribute regardless of display formatting. */
  iso: string
  className?: string
  /** Injectable clock (test-hermeticity) — defaults to the real current
   * time. */
  now?: () => Date
}

/**
 * Shared relative-time rendering primitive (ported from `ui-redesign`
 * STORY-098, journal D3 — salvage list): a `<time dateTime>` element whose
 * visible text is `formatRelativeTime` ("4m ago" / "in 2h", ticking
 * forward at least once a minute via `useRelativeTime`) and whose `title`
 * carries the absolute-local time plus the raw ISO-UTC instant, so the
 * exact original value is always one hover away. Used by every
 * recency-oriented surface (Check History, the Dashboard signal
 * drill-down, Approvals, Publications) so none of them re-implement the
 * ticking/tooltip mechanics themselves.
 */
export function RelativeTime({ iso, className, now }: RelativeTimeProps) {
  const { text, title } = useRelativeTime(iso, now)

  return (
    <time dateTime={iso} title={title} className={className}>
      {text}
    </time>
  )
}
