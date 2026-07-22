import { useCallback, useState } from 'react'
import { ApiError, postDecision } from '../../api/client'
import type { DecisionRequest } from '../../api/types'
import { OPERATOR_ACTOR } from './operatorActor'

export type DecisionAction = DecisionRequest['action']

type Phase = 'idle' | 'confirming' | 'submitting'

interface DecisionState {
  proposalId: number | null
  action: DecisionAction | null
  phase: Phase
}

const IDLE_STATE: DecisionState = { proposalId: null, action: null, phase: 'idle' }

export interface DecisionNotice {
  proposalId: number
  /** `conflict` (409 — already resolved/lost race/double-submit) and `gone`
   * (404 — no longer exists) are BOTH non-destructive: the list has already
   * been asked to refresh by the time the notice renders. `error` is any
   * other failure — the card shows an inline retry instead. */
  kind: 'conflict' | 'gone' | 'error'
  message: string
}

export interface UseApprovalsDecisionsResult {
  isConfirming: (proposalId: number) => boolean
  isSubmitting: (proposalId: number) => boolean
  /** True while a DIFFERENT proposal is mid-decision (AC3: only one
   * proposal is mid-decision at a time — every other card's actions
   * disable). Always `false` for the proposal that is itself active. */
  isBlocked: (proposalId: number) => boolean
  actionFor: (proposalId: number) => DecisionAction | undefined
  noticeFor: (proposalId: number) => DecisionNotice | undefined
  /** idle -> confirming (AC3's two-step: this is step one). */
  requestConfirm: (proposalId: number, action: DecisionAction) => void
  /** confirming -> idle — the keyboard-dismissable cancel/Escape path. */
  cancelConfirm: () => void
  /** confirming -> submitting -> (idle on success/409/404, back to
   * confirming with an inline notice on any other error). Never throws —
   * every rejection is caught and turned into `noticeFor` state (AC4). */
  confirmDecision: (proposalId: number, action: DecisionAction) => Promise<void>
}

/**
 * The Approvals confirm/submit state machine (STORY-131 AC2/AC3/AC4/AC5) —
 * lifted OUT of any single card component so "only one proposal mid-decision
 * at a time" (AC3) is a structural property of one shared state slice, not
 * a convention every card has to individually respect. `onResolved` is
 * called after a genuinely settled outcome (success, 409, or 404) so the
 * caller re-fetches the list from the server (AC5 — never optimistic-only
 * local removal); a generic error does NOT call it — nothing changed on the
 * server, so there's nothing to refresh, and the card offers a retry
 * instead (ui-ux-pro-max: confirm before destructive/irreversible actions;
 * distinct non-destructive vs. inline-retry error affordances).
 */
export function useApprovalsDecisions(onResolved: () => void): UseApprovalsDecisionsResult {
  const [decision, setDecision] = useState<DecisionState>(IDLE_STATE)
  const [notice, setNotice] = useState<DecisionNotice | null>(null)

  const requestConfirm = useCallback((proposalId: number, action: DecisionAction) => {
    setNotice(null)
    setDecision({ proposalId, action, phase: 'confirming' })
  }, [])

  const cancelConfirm = useCallback(() => {
    setDecision(IDLE_STATE)
  }, [])

  const confirmDecision = useCallback(
    async (proposalId: number, action: DecisionAction) => {
      setNotice(null)
      setDecision({ proposalId, action, phase: 'submitting' })

      try {
        await postDecision(proposalId, { action, actor: OPERATOR_ACTOR })
        setDecision(IDLE_STATE)
        onResolved()
      } catch (err) {
        const apiErr = err instanceof ApiError ? err : undefined

        if (apiErr?.status === 409) {
          setNotice({
            proposalId,
            kind: 'conflict',
            message: 'This proposal was already resolved — refreshing the list.',
          })
          setDecision(IDLE_STATE)
          onResolved()
          return
        }

        if (apiErr?.status === 404) {
          setNotice({
            proposalId,
            kind: 'gone',
            message: 'This proposal no longer exists — refreshing the list.',
          })
          setDecision(IDLE_STATE)
          onResolved()
          return
        }

        setNotice({
          proposalId,
          kind: 'error',
          message: err instanceof Error ? err.message : 'Something went wrong',
        })
        // Back to confirming (not idle) so the card still shows a
        // Confirm/Retry affordance for the same action, per AC4.
        setDecision({ proposalId, action, phase: 'confirming' })
      }
    },
    [onResolved],
  )

  const isConfirming = useCallback(
    (proposalId: number) => decision.phase === 'confirming' && decision.proposalId === proposalId,
    [decision],
  )
  const isSubmitting = useCallback(
    (proposalId: number) => decision.phase === 'submitting' && decision.proposalId === proposalId,
    [decision],
  )
  const isBlocked = useCallback(
    (proposalId: number) => decision.phase !== 'idle' && decision.proposalId !== proposalId,
    [decision],
  )
  const actionFor = useCallback(
    (proposalId: number) => (decision.proposalId === proposalId ? (decision.action ?? undefined) : undefined),
    [decision],
  )
  const noticeFor = useCallback(
    (proposalId: number) => (notice?.proposalId === proposalId ? notice : undefined),
    [notice],
  )

  return {
    isConfirming,
    isSubmitting,
    isBlocked,
    actionFor,
    noticeFor,
    requestConfirm,
    cancelConfirm,
    confirmDecision,
  }
}
