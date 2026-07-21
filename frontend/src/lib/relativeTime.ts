const JUST_NOW_THRESHOLD_SECONDS = 5

/**
 * Formats a fine-grained relative time (STORY-122 — the recent-checks feed
 * and probe-locations panel need second-level freshness, unlike the
 * topbar's minute-granularity `formatLastUpdated`). `now` is an explicit
 * parameter, never `Date.now()` read inside, so this stays a pure,
 * deterministic function to test. A future timestamp (clock skew between
 * the browser and the observation's server clock) clamps to "just now"
 * rather than rendering a negative duration.
 */
export function formatRelativeTime(at: Date, now: Date): string {
  const elapsedMs = Math.max(0, now.getTime() - at.getTime())
  const elapsedSeconds = Math.floor(elapsedMs / 1000)

  if (elapsedSeconds < JUST_NOW_THRESHOLD_SECONDS) {
    return 'just now'
  }
  if (elapsedSeconds < 60) {
    return `${elapsedSeconds}s ago`
  }

  const elapsedMinutes = Math.floor(elapsedSeconds / 60)
  if (elapsedMinutes < 60) {
    return `${elapsedMinutes} min ago`
  }

  const elapsedHours = Math.floor(elapsedMinutes / 60)
  return `${elapsedHours}h ago`
}
