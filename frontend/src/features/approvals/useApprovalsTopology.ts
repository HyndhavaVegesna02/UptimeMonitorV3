import { getTopology } from '../../api/client'
import type { ComponentTopologyDTO } from '../../api/types'
import { useFetch } from '../../lib/useFetch'
import type { UseFetchResult } from '../../lib/useFetch'

export type UseApprovalsTopologyResult = UseFetchResult<ComponentTopologyDTO[]>

/**
 * Fetch hook for `GET /api/v1/topology` (STORY-107 AC1 — ported from the
 * parked `ui-redesign` branch's STORY-100 work, review-approved there) —
 * feeds the Approvals tab's evidence-first card: the friendly component name
 * and the component's primary signal (`useProposalEvidence`'s input),
 * resolved by joining a proposal's `component_id` against this topology. A
 * thin `useFetch` wrapper, mirroring `features/dashboard/useTopology.ts`'s
 * pattern exactly — kept as its own file per-feature (not shared) so the
 * Approvals tab's topology usage can evolve independently of Dashboard's.
 * A fetch failure here degrades the card to its component_id slug and no
 * evidence (AC4) rather than blocking the queue.
 */
export function useApprovalsTopology(): UseApprovalsTopologyResult {
  return useFetch(getTopology)
}
