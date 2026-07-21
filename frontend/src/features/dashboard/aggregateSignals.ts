import type { ObservationDTO } from '../../api/types'
import type { SignalsMap } from './types'

/**
 * The KPI row's "overall availability · 24h" figure (STORY-122 AC1). With
 * exactly one signal (the current real topology), this returns THAT
 * signal's own `availability_pct` — the brief's explicit rule ("with one
 * signal, that signal's availability; derive, don't invent"). With more
 * than one, it averages the non-null values — a real derivation over real
 * per-signal figures, never a fabricated rollup weighting scheme.
 */
export function deriveOverallAvailability(signalsData: SignalsMap): number | null {
  const values = Object.values(signalsData)
    .map((signal) => signal.availability.availability_pct)
    .filter((value): value is number => value !== null)

  if (values.length === 0) {
    return null
  }

  return values.reduce((total, value) => total + value, 0) / values.length
}

/**
 * Combines every fetched signal's history into one most-recent-first list
 * (STORY-122) — the shape `deriveChartData`/`latencySeries`/`healthSeries`
 * expect. A single-signal system (each signal's own history is already
 * most-recent-first) is unaffected by the re-sort; this generalizes
 * correctly once the topology grows past one signal.
 */
export function flattenHistory(signalsData: SignalsMap): ObservationDTO[] {
  return Object.values(signalsData)
    .flatMap((signal) => signal.history)
    .sort((a, b) => new Date(b.observed_at).getTime() - new Date(a.observed_at).getTime())
}
