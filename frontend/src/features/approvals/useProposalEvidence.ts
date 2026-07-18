import { useCallback } from 'react'
import { getHistory } from '../../api/client'
import type { ObservationDTO } from '../../api/types'
import type { HealthStatus } from '../../components'
import { windowToRange } from '../availability/windowRange'
import { observationHealth } from '../history/observationHealth'
import { useFetch } from '../../lib/useFetch'
import type { UseFetchResult } from '../../lib/useFetch'

/** Small server-side cap (STORY-094's `limit` param) — evidence only needs
 * enough of the newest-first observations to find each distinct location's
 * latest reading, never the full window Check History renders. */
const EVIDENCE_HISTORY_LIMIT = 20

/** One "latest result at this location" row for a proposal card (STORY-107
 * AC1, ported from the parked `ui-redesign` STORY-100): status + latency +
 * the raw observed-at instant (rendered via the shared `RelativeTime`). */
export interface EvidenceRow {
  location: string
  status: HealthStatus
  /** Integer ms, or `null` — same "never fabricate 0 ms" convention as Check
   * History. */
  latencyMs: number | null
  observedAt: string
}

/**
 * Collapses newest-first observations to one row per distinct location — the
 * FIRST observation seen for a location IS its latest (the same convention
 * `features/dashboard/useComponentSignals.ts::buildSignalRows` uses).
 */
export function latestPerLocation(observations: ObservationDTO[]): EvidenceRow[] {
  const rows: EvidenceRow[] = []
  const seenLocations = new Set<string>()

  for (const observation of observations) {
    if (seenLocations.has(observation.location)) {
      continue
    }
    seenLocations.add(observation.location)
    rows.push({
      location: observation.location,
      status: observationHealth(observation.health),
      latencyMs: observation.latency_ms,
      observedAt: observation.observed_at,
    })
  }

  return rows
}

async function fetchProposalEvidence(signalKey: string | undefined): Promise<EvidenceRow[]> {
  if (!signalKey) {
    return []
  }
  const range = windowToRange('24h')
  const observations = await getHistory({
    signal_key: signalKey,
    since: range.since,
    until: range.until,
    limit: EVIDENCE_HISTORY_LIMIT,
  })
  return latestPerLocation(observations)
}

export type UseProposalEvidenceResult = UseFetchResult<EvidenceRow[]>

/**
 * Per-proposal evidence hook (STORY-107 AC1, AC4 — ported from the parked
 * `ui-redesign` branch's STORY-100 work, review-approved there): "latest
 * result per location" for the proposal's PRIMARY topology signal, on the
 * EXISTING `GET /api/v1/history`. `ProposalDTO`/`StatusProposal` carry no
 * `signal_key` on the wire — a proposal is per-COMPONENT
 * (`backend/src/core/domain/proposal.py::StatusProposal`) — so the caller
 * resolves `signalKey` from the component's topology (its FIRST signal, the
 * same single-signal adaptation `features/dashboard/useComponentUptime.ts`
 * already uses for the same reason: no dedicated per-proposal signal API).
 * `signalKey === undefined` (topology not yet resolved, or a genuinely
 * zero-signal component) short-circuits to an always-successful empty
 * result — never blocks the card. A REAL history-fetch failure surfaces as
 * this hook's OWN `'error'` state; the caller degrades to a quiet notice and
 * keeps the card fully actionable (AC4) rather than propagating the failure.
 */
export function useProposalEvidence(signalKey: string | undefined): UseProposalEvidenceResult {
  const fetcher = useCallback(() => fetchProposalEvidence(signalKey), [signalKey])
  return useFetch(fetcher)
}
