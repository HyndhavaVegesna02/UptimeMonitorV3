export type WindowPreset = '24h' | '7d' | '30d'

/** A tz-aware ISO `since`/`until` pair ready to hand to
 * `getComponentAvailability` (STORY-015d AC2). */
export interface AvailabilityRange {
  since: string
  until: string
}

const PRESET_DURATION_MS: Record<WindowPreset, number> = {
  '24h': 24 * 60 * 60 * 1000,
  '7d': 7 * 24 * 60 * 60 * 1000,
  '30d': 30 * 24 * 60 * 60 * 1000,
}

/**
 * Pure window-preset -> tz-aware UTC ISO range helper (STORY-015d AC2) — the
 * SINGLE seam that turns a selector value into the `since`/`until` strings
 * sent to `getComponentAvailability`. `until` = `now`; `since` = `now` minus
 * the preset's duration. `Date#toISOString()` always emits UTC with a
 * trailing `Z`, so every string this returns is tz-aware by construction —
 * this is the seam the tz-discipline working agreement pins tests to, since
 * the backend 422s a naive datetime.
 */
export function windowToRange(preset: WindowPreset, now: Date = new Date()): AvailabilityRange {
  const until = now.toISOString()
  const since = new Date(now.getTime() - PRESET_DURATION_MS[preset]).toISOString()
  return { since, until }
}
