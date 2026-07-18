import type { MaintenanceWindowDTO } from '../../api/types'
import { deriveWindowState } from '../maintenance/windowState'

/**
 * Counts maintenance windows that are currently ACTIVE or still UPCOMING
 * (ported verbatim from `ui-redesign` STORY-099 AC2, design-brief §Salvage —
 * STORY-105's "Maintenance" action tile count): an operator cares about a
 * window that's live right now or scheduled to start, not one that's
 * already finished. Mirrors
 * `features/maintenance/windowState.ts::deriveWindowState`'s half-open rule
 * exactly rather than re-deriving it — a window at its own `starts_at`
 * instant counts, one at its own `ends_at` instant does not (STORY-046's
 * pinned boundary agreement). An empty list returns `0`, never a leaked
 * stdlib message. `now` defaults to the real current time but is accepted
 * as a parameter so tests can pin an exact instant.
 */
export function countActiveOrUpcomingWindows(
  windows: MaintenanceWindowDTO[],
  now: Date = new Date(),
): number {
  return windows.filter((window) => {
    const state = deriveWindowState(window.starts_at, window.ends_at, now)
    return state === 'active' || state === 'upcoming'
  }).length
}
