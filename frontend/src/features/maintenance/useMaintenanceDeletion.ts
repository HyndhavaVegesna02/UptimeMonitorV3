import { useCallback, useState } from 'react'
import { ApiError, deleteMaintenance } from '../../api/client'

type Phase = 'idle' | 'confirming' | 'submitting'

interface DeletionState {
  windowId: number | null
  phase: Phase
}

const IDLE_STATE: DeletionState = { windowId: null, phase: 'idle' }

export interface DeletionNotice {
  windowId: number
  /** `gone` (404 — already deleted; DELETE is NOT idempotent) is
   * non-destructive: the list has already been asked to refresh by the time
   * the notice renders. `error` is any other failure — the card shows an
   * inline retry instead. */
  kind: 'gone' | 'error'
  message: string
}

export interface UseMaintenanceDeletionResult {
  isConfirming: (windowId: number) => boolean
  isSubmitting: (windowId: number) => boolean
  /** True while a DIFFERENT window is mid-deletion — every other window's
   * delete action disables (mirrors the Approvals "one at a time" rule). */
  isBlocked: (windowId: number) => boolean
  noticeFor: (windowId: number) => DeletionNotice | undefined
  requestConfirm: (windowId: number) => void
  cancelConfirm: () => void
  /** confirming -> submitting -> (idle on 204/404 success, back to
   * confirming with an inline notice on any other error). Never throws
   * (STORY-132 AC4). */
  confirmDelete: (windowId: number) => Promise<void>
}

/**
 * The Maintenance list's delete/confirm state machine (STORY-132 AC4) — the
 * same shape as Approvals' `useApprovalsDecisions`, simplified to a single
 * action (delete, no approve/reject variant). `onResolved` is called after
 * a genuinely settled outcome (204 success OR 404 already-gone) so the
 * caller re-fetches the list from the server — a 404 is explicitly NOT a
 * silent success (plan §Maintenance: "delete is not idempotent"). A generic
 * error does NOT call it — nothing changed on the server, so the card
 * offers a retry instead.
 */
export function useMaintenanceDeletion(onResolved: () => void): UseMaintenanceDeletionResult {
  const [state, setState] = useState<DeletionState>(IDLE_STATE)
  const [notice, setNotice] = useState<DeletionNotice | null>(null)

  const requestConfirm = useCallback((windowId: number) => {
    setNotice(null)
    setState({ windowId, phase: 'confirming' })
  }, [])

  const cancelConfirm = useCallback(() => {
    setState(IDLE_STATE)
  }, [])

  const confirmDelete = useCallback(
    async (windowId: number) => {
      setNotice(null)
      setState({ windowId, phase: 'submitting' })

      try {
        await deleteMaintenance(windowId)
        setState(IDLE_STATE)
        onResolved()
      } catch (err) {
        const apiErr = err instanceof ApiError ? err : undefined

        if (apiErr?.status === 404) {
          setNotice({
            windowId,
            kind: 'gone',
            message: 'This window was already deleted — refreshing the list.',
          })
          setState(IDLE_STATE)
          onResolved()
          return
        }

        setNotice({
          windowId,
          kind: 'error',
          message: err instanceof Error ? err.message : 'Something went wrong',
        })
        // Back to confirming (not idle) so a Retry affordance stays available.
        setState({ windowId, phase: 'confirming' })
      }
    },
    [onResolved],
  )

  const isConfirming = useCallback(
    (windowId: number) => state.phase === 'confirming' && state.windowId === windowId,
    [state],
  )
  const isSubmitting = useCallback(
    (windowId: number) => state.phase === 'submitting' && state.windowId === windowId,
    [state],
  )
  const isBlocked = useCallback(
    (windowId: number) => state.phase !== 'idle' && state.windowId !== windowId,
    [state],
  )
  const noticeFor = useCallback(
    (windowId: number) => (notice?.windowId === windowId ? notice : undefined),
    [notice],
  )

  return {
    isConfirming,
    isSubmitting,
    isBlocked,
    noticeFor,
    requestConfirm,
    cancelConfirm,
    confirmDelete,
  }
}
