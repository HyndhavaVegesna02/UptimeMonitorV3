export type WindowState = 'upcoming' | 'active' | 'past'

/**
 * Derives a maintenance window's display state CLIENT-SIDE (STORY-036/
 * STORY-015f AC1) — there is NO `state` field on the
 * `GET /api/v1/maintenance` wire shape. Mirrors the backend's HALF-OPEN
 * rule exactly (`core/ports/maintenance_repository.py::is_under_maintenance`;
 * the `DynamoMaintenanceRepository` adapter's `starts_at <= at AND ends_at > at`
 * agrees): a
 * window is active iff `starts_at <= now < ends_at`. At exactly `starts_at`
 * the window IS active; at exactly `ends_at` it is no longer active (past) —
 * both boundary instants are pinned by tests per the sprint-34 plan's
 * non-aligned-boundary agreement, since a naive `<`/`>` swap at either edge
 * would silently misclassify a window at the instant it starts or ends.
 *
 * `now` defaults to `new Date()` but is accepted as a parameter so tests can
 * pin an exact instant rather than racing the real clock.
 */
export function deriveWindowState(
  startsAt: string,
  endsAt: string,
  now: Date = new Date(),
): WindowState {
  const start = new Date(startsAt).getTime()
  const end = new Date(endsAt).getTime()
  const t = now.getTime()

  if (t < start) {
    return 'upcoming'
  }
  if (t < end) {
    return 'active'
  }
  return 'past'
}
