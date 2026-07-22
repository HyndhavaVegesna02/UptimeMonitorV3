const MONTHS = [
  'Jan',
  'Feb',
  'Mar',
  'Apr',
  'May',
  'Jun',
  'Jul',
  'Aug',
  'Sep',
  'Oct',
  'Nov',
  'Dec',
]

function pad2(n: number): string {
  return String(n).padStart(2, '0')
}

/**
 * Formats an `ObservationDTO.observed_at` ISO string as an absolute UTC
 * timestamp for the dense grid (STORY-130 AC3/AC6 — the grid's timestamp
 * column). Deliberately hand-formats the UTC fields rather than
 * `toLocaleString` (whose output depends on the host's locale/timezone,
 * which would make this non-deterministic in CI and mismatch the reality
 * gate's live-captured UTC values). No year: this is a recent-history
 * window, not a long-term archive.
 *
 * Carries an explicit trailing `" UTC"` label (STORY-140 AC2) — the same
 * convention `formatWindowRange` (Maintenance card) already established for
 * its own hand-formatted UTC fields, so History-row timestamps are no
 * longer the one place on the Dashboard/History surfaces with an
 * unlabelled, ambiguous absolute time.
 */
export function formatObservedAt(observedAt: string): string {
  const date = new Date(observedAt)
  const month = MONTHS[date.getUTCMonth()]
  const day = pad2(date.getUTCDate())
  const time = `${pad2(date.getUTCHours())}:${pad2(date.getUTCMinutes())}:${pad2(date.getUTCSeconds())}`
  return `${month} ${day}, ${time} UTC`
}
