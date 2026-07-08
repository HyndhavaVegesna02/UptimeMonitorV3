import { getApprovals } from '../../api/client'
import { useFetch } from '../../lib/useFetch'

/**
 * The Approvals sidebar badge count (STORY-056 AC4): the number of open
 * proposals from `GET /api/v1/approvals` (every returned `ProposalDTO` is
 * open — there is no separate "pending" filter on the wire, per the
 * sprint-38 plan's pinned API contracts). Returns `undefined` while the
 * initial fetch is in flight AND on a fetch failure — both render as "no
 * badge" in `Sidebar`, the graceful-degradation case AC4 requires (never a
 * stale or fabricated count).
 */
export function useApprovalsBadge(): number | undefined {
  const { state } = useFetch(getApprovals)
  return state.phase === 'success' ? state.data.length : undefined
}
