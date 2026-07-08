export type DecisionAction = 'approve' | 'reject'

export const CONFIRM_COPY: Record<DecisionAction, { prompt: string; confirmLabel: string }> = {
  approve: { prompt: 'Approve this proposal?', confirmLabel: 'Confirm approve' },
  reject: { prompt: 'Reject this proposal?', confirmLabel: 'Confirm reject' },
}

export const ACTION_LABEL: Record<DecisionAction, string> = {
  approve: 'Approve',
  reject: 'Reject',
}

/**
 * The page-level decision state machine (STORY-015c AC2/AC3/AC4 — carried
 * over unchanged by STORY-059's card-layout rebuild, per AC2). Only one
 * proposal can be mid-decision at a time; `proposalId` names which one.
 */
export type DecisionUiState =
  | { phase: 'idle' }
  | { phase: 'confirming'; proposalId: number; action: DecisionAction }
  | { phase: 'submitting'; proposalId: number; action: DecisionAction }
  | { phase: 'failed'; proposalId: number; action: DecisionAction; message: string }

/**
 * The subset of `DecisionUiState` a single `ApprovalCard` needs to render
 * its own actions column. `proposalId` is dropped: the page has already
 * decided which card (if any) is the active one before handing this down,
 * so the card itself never needs to compare ids.
 */
export type CardDecisionState =
  | { phase: 'idle' }
  | { phase: 'confirming'; action: DecisionAction }
  | { phase: 'submitting'; action: DecisionAction }
  | { phase: 'failed'; action: DecisionAction; message: string }

/** Narrows the page-level state to one card's view: `'idle'` unless this
 * proposal is the currently active row. */
export function toCardDecisionState(
  state: DecisionUiState,
  proposalId: number,
): CardDecisionState {
  if (state.phase !== 'idle' && state.proposalId === proposalId) {
    return state
  }
  return { phase: 'idle' }
}
