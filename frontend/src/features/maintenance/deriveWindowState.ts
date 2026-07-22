export type MaintenanceWindowState = 'upcoming' | 'active' | 'past'

export interface MaintenanceWindowInstants {
  starts_at: string
  ends_at: string
}

/**
 * Derives the display state of a maintenance window (STORY-132 AC1) — the
 * DTO carries no state field, so upcoming/active/past is computed
 * client-side from `starts_at`/`ends_at` against `now`. The half-open rule
 * `[starts_at, ends_at)`: `now < starts_at` -> upcoming; `now < ends_at` ->
 * active (this INCLUDES the `now === starts_at` boundary instant); anything
 * else (including `now === ends_at`) -> past.
 *
 * `now` is an explicit parameter, never `new Date()` read internally — a
 * pure, deterministic function so the boundary instants are directly
 * testable (checklist: range/window boundary math tests exact edges, not
 * just clean inputs).
 */
export function deriveMaintenanceWindowState(
  window: MaintenanceWindowInstants,
  now: Date,
): MaintenanceWindowState {
  const nowMs = now.getTime()
  const startsMs = new Date(window.starts_at).getTime()
  const endsMs = new Date(window.ends_at).getTime()

  if (nowMs < startsMs) {
    return 'upcoming'
  }
  if (nowMs < endsMs) {
    return 'active'
  }
  return 'past'
}
