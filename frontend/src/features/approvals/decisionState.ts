export type DecisionAction = 'approve' | 'reject'

/** What `confirmPrompt` needs to name the consequence (STORY-100 AC3): the
 * component's friendly name and the human word for the proposal's target
 * status — the SAME text the transition `StatusBadge` already shows
 * (`defaultStatusLabel`), so the confirm step never invents a second
 * vocabulary for the same status. */
export interface ConfirmContext {
  componentLabel: string
  targetStatusLabel: string
}

/**
 * The confirm-step prompt text (STORY-100 AC3 — journal finding #14, D5):
 * approve now states the CONSEQUENCE explicitly — "Publishes '<component>:
 * <target status>' to the public status page." — instead of the old bare
 * "Approve this proposal?"; reject's prompt is UNCHANGED in behavior (its
 * own text carries no publish consequence, since a reject never touches the
 * public status page).
 */
export function confirmPrompt(action: DecisionAction, context: ConfirmContext): string {
  if (action === 'reject') {
    return 'Reject this proposal?'
  }
  return `Publishes '${context.componentLabel}: ${context.targetStatusLabel}' to the public status page.`
}

/** The confirm button's own label — UNCHANGED from pre-STORY-100 (only the
 * prompt text above gained the consequence copy). */
export const CONFIRM_LABEL: Record<DecisionAction, string> = {
  approve: 'Confirm approve',
  reject: 'Confirm reject',
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
