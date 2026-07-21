import type { AvailabilityDTO, ObservationDTO } from '../../api/types'

/** One component's fetched signal data (STORY-122) — in the current
 * topology a component id IS its signal_key 1:1 (see
 * `useSignalsData.ts`), so this is keyed by that shared id. */
export interface SignalData {
  history: ObservationDTO[]
  availability: AvailabilityDTO
}

/** Keyed by signal_key (== component id). */
export type SignalsMap = Record<string, SignalData>
