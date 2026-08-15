import { useCallback, useState } from 'react'
import { ApiError, getMaintenance, postMaintenance, deleteMaintenance } from '../../api/client'
import type { CreateMaintenanceRequest, MaintenanceWindowDTO } from '../../api/types'
import { useFetch } from '../../lib/useFetch'
import type { FetchState } from '../../lib/useFetch'

export interface UseMaintenanceResult {
  /** The list GET's read state (loading | error | success). */
  state: FetchState<MaintenanceWindowDTO[]>
  /** Re-attempts the initial GET (from the shared `useFetch`); also clears
   * any prior mutation error so a fresh load starts clean. */
  retry: () => void
  /**
   * POSTs a new window (STORY-036/STORY-015f AC2). On success, clears
   * `mutationError` and refreshes the list via the underlying `useFetch`'s
   * `retry()` (015c Approvals precedent: always reconcile the list with the
   * server after a resolved mutation) — the caller does not need to call
   * `retry()` itself. On failure, `mutationError` is set (the list is left
   * as-is) and the promise still resolves rather than rejecting — callers
   * read `mutationError` rather than catching.
   * Resolves to `true` on success / `false` on failure so a caller (e.g.
   * the schedule form) can reset its own local field state exactly once,
   * without racing this hook's own state update.
   */
  schedule: (request: CreateMaintenanceRequest) => Promise<boolean>
  /** True for the duration of an in-flight POST — the form disables submit
   * while this is true. */
  scheduling: boolean
  /**
   * The most recent failed POST's `ApiError`, preserved (not just its
   * message) so a caller can read `.status`/`.detail` — `.detail` is what
   * `features/maintenance/fieldError.ts::fieldErrorFromDetail` maps onto a
   * specific form field for AC3's inline rendering. `null` once a schedule
   * attempt has not yet failed, or after a successful one / a `retry()`.
   */
  mutationError: ApiError | null
  /** DELETEs a maintenance window (STORY-065 AC5). */
  deleteWindow: (id: number) => Promise<boolean>
  /** The ID of the maintenance window currently being deleted, if any. */
  deletingId: number | null
  /** The most recent failed DELETE's `ApiError`, if any. */
  deleteError: ApiError | null
}

/**
 * Feature hook for the Maintenance tab (STORY-015f): loads the window list
 * via the shared `useFetch(getMaintenance)`, then exposes `schedule` to POST
 * a new window — a "load+mutate in one hook" shape, adapted here for a
 * growing LIST rather than a single flag: a successful POST calls the
 * list's own `retry()` to reconcile with the server, instead of locally
 * overriding a value.
 */
export function useMaintenance(): UseMaintenanceResult {
  const { state, retry } = useFetch(getMaintenance)
  const [scheduling, setScheduling] = useState(false)
  const [mutationError, setMutationError] = useState<ApiError | null>(null)
  const [deletingId, setDeletingId] = useState<number | null>(null)
  const [deleteError, setDeleteError] = useState<ApiError | null>(null)

  const schedule = useCallback(
    async (request: CreateMaintenanceRequest): Promise<boolean> => {
      setScheduling(true)
      setMutationError(null)
      try {
        await postMaintenance(request)
        retry()
        return true
      } catch (err) {
        setMutationError(
          err instanceof ApiError
            ? err
            : new ApiError('Could not schedule the maintenance window'),
        )
        return false
      } finally {
        setScheduling(false)
      }
    },
    [retry],
  )

  const deleteWindow = useCallback(
    async (id: number): Promise<boolean> => {
      setDeletingId(id)
      setDeleteError(null)
      try {
        await deleteMaintenance(id)
        retry()
        return true
      } catch (err) {
        setDeleteError(
          err instanceof ApiError
            ? err
            : new ApiError('Could not delete the maintenance window'),
        )
        return false
      } finally {
        setDeletingId(null)
      }
    },
    [retry],
  )

  const retryFromScratch = useCallback(() => {
    setMutationError(null)
    setDeleteError(null)
    retry()
  }, [retry])

  return {
    state,
    retry: retryFromScratch,
    schedule,
    scheduling,
    mutationError,
    deleteWindow,
    deletingId,
    deleteError,
  }
}
