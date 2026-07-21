/**
 * Formats the topbar's last-updated indicator (STORY-121 AC3) relative to
 * `now` — `now` is an explicit parameter (never `Date.now()` read inside)
 * so the formatting itself stays a pure, deterministic function to test.
 */
export function formatLastUpdated(updatedAt: Date | null, now: Date): string {
  if (!updatedAt) {
    return 'Updating…'
  }

  const elapsedMs = now.getTime() - updatedAt.getTime()
  const elapsedMinutes = Math.floor(elapsedMs / 60_000)

  if (elapsedMinutes < 1) {
    return 'Updated just now'
  }
  if (elapsedMinutes === 1) {
    return 'Updated 1m ago'
  }
  if (elapsedMinutes < 60) {
    return `Updated ${elapsedMinutes}m ago`
  }

  const elapsedHours = Math.floor(elapsedMinutes / 60)
  return elapsedHours === 1 ? 'Updated 1h ago' : `Updated ${elapsedHours}h ago`
}
