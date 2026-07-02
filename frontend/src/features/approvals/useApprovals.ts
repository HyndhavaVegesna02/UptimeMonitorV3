import { getApprovals } from '../../api/client'
import type { ProposalDTO } from '../../api/types'
import { useFetch } from '../../lib/useFetch'
import type { UseFetchResult } from '../../lib/useFetch'

export type UseApprovalsResult = UseFetchResult<ProposalDTO[]>

/**
 * Fetch hook for `GET /api/v1/approvals` (STORY-015c AC1, AC5) — built on
 * the shared `useFetch<T>` (the 2nd fetch hook to sit on it, alongside
 * `useComponents`). `retry()` doubles as the post-decision list refresh:
 * the Approvals page calls it after a successful/409/404 decision outcome.
 */
export function useApprovals(): UseApprovalsResult {
  return useFetch(getApprovals)
}
