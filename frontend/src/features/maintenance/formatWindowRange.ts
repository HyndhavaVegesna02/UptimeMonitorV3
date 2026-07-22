const DATE_FORMATTER = new Intl.DateTimeFormat('en-US', {
  month: 'short',
  day: 'numeric',
  timeZone: 'UTC',
})

const TIME_FORMATTER = new Intl.DateTimeFormat('en-US', {
  hour: '2-digit',
  minute: '2-digit',
  hourCycle: 'h23',
  timeZone: 'UTC',
})

/**
 * Formats a maintenance window's `[starts_at, ends_at)` range for display
 * (STORY-132 AC1). Same-day windows collapse to one date with a time range
 * (`"Jul 22 · 00:00–02:00 UTC"`); a window spanning midnight repeats both
 * dates so neither endpoint is ambiguous (`"Jul 22, 23:00 – Jul 23, 01:00
 * UTC"`). Always UTC (the wire's own timezone — no local-time conversion,
 * unlike the schedule form's `datetime-local` inputs) so operators comparing
 * windows never have to mentally convert timezones.
 */
export function formatWindowRange(startsAt: string, endsAt: string): string {
  const starts = new Date(startsAt)
  const ends = new Date(endsAt)
  const sameDay = DATE_FORMATTER.format(starts) === DATE_FORMATTER.format(ends)

  if (sameDay) {
    return `${DATE_FORMATTER.format(starts)} · ${TIME_FORMATTER.format(starts)}–${TIME_FORMATTER.format(ends)} UTC`
  }

  return `${DATE_FORMATTER.format(starts)}, ${TIME_FORMATTER.format(starts)} – ${DATE_FORMATTER.format(ends)}, ${TIME_FORMATTER.format(ends)} UTC`
}
