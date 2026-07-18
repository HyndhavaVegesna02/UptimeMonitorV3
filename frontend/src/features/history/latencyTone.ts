export type LatencyTone = 'muted' | 'warn' | 'high'

/** The 500-1000ms boundary values (STORY-108 AC2, ui-ux-pro-max chart/table
 * domain guidance — "latency threshold tint via NAMED TOKENS: muted <500ms /
 * warn 500-1000 / high >1000"). Named constants rather than inline magic
 * numbers so a future re-tune touches exactly one place. */
export const LATENCY_WARN_THRESHOLD_MS = 500
export const LATENCY_HIGH_THRESHOLD_MS = 1000

/**
 * Classifies a raw `latency_ms` reading into the latency-tint band the
 * Check History table's Latency column paints via `--color-latency-muted`/
 * `-warn`/`-high` (`tokens.css`) — a purely REINFORCING visual cue: the
 * Result column's `StatusBadge` carries the actual semantic (a fast
 * response can still be a `down` check), so a latency tint alone never
 * conveys meaning. `latency_ms: null` (no measurement) returns `null` — no
 * tint, never a fabricated band.
 */
export function latencyTone(latencyMs: number | null): LatencyTone | null {
  if (latencyMs === null) {
    return null
  }
  if (latencyMs > LATENCY_HIGH_THRESHOLD_MS) {
    return 'high'
  }
  if (latencyMs >= LATENCY_WARN_THRESHOLD_MS) {
    return 'warn'
  }
  return 'muted'
}
