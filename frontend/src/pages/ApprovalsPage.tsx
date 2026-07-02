import { useState } from 'react'
import { getActor } from '../api/actor'
import { ApiError, postDecision } from '../api/client'
import { toHealthStatus } from '../api/statusMapping'
import {
  Button,
  EmptyState,
  ErrorState,
  LoadingState,
  Panel,
  StatusBadge,
} from '../components'
import { useApprovals } from '../features/approvals/useApprovals'
import './ApprovalsPage.css'

type DecisionAction = 'approve' | 'reject'

const CONFIRM_COPY: Record<DecisionAction, { prompt: string; confirmLabel: string }> = {
  approve: { prompt: 'Approve this proposal?', confirmLabel: 'Confirm approve' },
  reject: { prompt: 'Reject this proposal?', confirmLabel: 'Confirm reject' },
}

const ACTION_LABEL: Record<DecisionAction, string> = {
  approve: 'Approve',
  reject: 'Reject',
}

/** Local UI state machine for the currently-focused row's decision flow
 * (STORY-015c AC2/AC3/AC4) — separate from the list's own `useApprovals`
 * fetch state. Only one row can be mid-decision at a time. */
type DecisionUiState =
  | { phase: 'idle' }
  | { phase: 'confirming'; proposalId: number; action: DecisionAction }
  | { phase: 'submitting'; proposalId: number; action: DecisionAction }
  | { phase: 'failed'; proposalId: number; action: DecisionAction; message: string }

/**
 * The Approvals tab (STORY-015c): the human approval gate — a degradation
 * reaches the public Statuspage only after an operator approves it here.
 * Fetches `GET /api/v1/approvals` via `useApprovals` and renders one row
 * per open proposal — `component_id`, the `from_status -> to_status`
 * transition (two `StatusBadge`s; `from_status` may be null for a
 * component's first-ever proposal, rendered as "New" instead of a badge),
 * and `proposed_at` (mono) — plus Approve/Reject actions (AC1, AC4).
 */
export function ApprovalsPage() {
  const { state, retry } = useApprovals()
  const [decisionState, setDecisionState] = useState<DecisionUiState>({ phase: 'idle' })
  const [notice, setNotice] = useState<string | null>(null)

  function requestConfirm(proposalId: number, action: DecisionAction) {
    setNotice(null)
    setDecisionState({ phase: 'confirming', proposalId, action })
  }

  function cancelConfirm() {
    setDecisionState({ phase: 'idle' })
  }

  async function confirmDecision(proposalId: number, action: DecisionAction) {
    setDecisionState({ phase: 'submitting', proposalId, action })
    try {
      await postDecision(proposalId, { action, actor: getActor() })
      setDecisionState({ phase: 'idle' })
      retry()
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setNotice('This proposal has already been resolved.')
        setDecisionState({ phase: 'idle' })
        retry()
        return
      }
      if (err instanceof ApiError && err.status === 404) {
        setNotice('This proposal no longer exists.')
        setDecisionState({ phase: 'idle' })
        retry()
        return
      }
      setDecisionState({
        phase: 'failed',
        proposalId,
        action,
        message: 'Could not record the decision',
      })
    }
  }

  return (
    <Panel title="Approvals" headingLevel="h1">
      {notice ? (
        <p className="approvals-page__notice" role="status">
          {notice}
        </p>
      ) : null}

      {state.phase === 'loading' && <LoadingState label="Loading proposals…" />}

      {state.phase === 'error' && (
        <ErrorState message="Could not load proposals" onRetry={retry} />
      )}

      {state.phase === 'success' && state.data.length === 0 && (
        <EmptyState message="nothing pending approval" />
      )}

      {state.phase === 'success' && state.data.length > 0 && (
        <table className="approvals-table">
          <thead>
            <tr>
              <th scope="col">Component</th>
              <th scope="col">Transition</th>
              <th scope="col">Proposed</th>
              <th scope="col">Decision</th>
            </tr>
          </thead>
          <tbody>
            {state.data.map((proposal) => {
              const isActiveRow =
                decisionState.phase !== 'idle' && decisionState.proposalId === proposal.id

              return (
                <tr key={proposal.id}>
                  <td>{proposal.component_id}</td>
                  <td>
                    <span className="approvals-table__transition">
                      {proposal.from_status ? (
                        <StatusBadge status={toHealthStatus(proposal.from_status)} />
                      ) : (
                        <span className="approvals-table__new">New</span>
                      )}
                      <span className="approvals-table__arrow" aria-hidden="true">
                        →
                      </span>
                      <span className="sr-only">to</span>
                      <StatusBadge status={toHealthStatus(proposal.to_status)} />
                    </span>
                  </td>
                  <td>
                    <time className="text-mono" dateTime={proposal.proposed_at}>
                      {proposal.proposed_at}
                    </time>
                  </td>
                  <td>
                    {isActiveRow && decisionState.phase === 'confirming' && (
                      <span className="approvals-table__confirm">
                        <span className="approvals-table__confirm-text">
                          {CONFIRM_COPY[decisionState.action].prompt}
                        </span>
                        <Button
                          variant="primary"
                          onClick={() => void confirmDecision(proposal.id, decisionState.action)}
                        >
                          {CONFIRM_COPY[decisionState.action].confirmLabel}
                        </Button>
                        <Button variant="tertiary" onClick={cancelConfirm}>
                          Cancel
                        </Button>
                      </span>
                    )}

                    {isActiveRow && decisionState.phase === 'submitting' && (
                      <span className="approvals-table__confirm-text">Submitting…</span>
                    )}

                    {isActiveRow && decisionState.phase === 'failed' && (
                      <ErrorState
                        message={decisionState.message}
                        onRetry={() => void confirmDecision(proposal.id, decisionState.action)}
                      />
                    )}

                    {!isActiveRow && (
                      <span className="approvals-table__actions">
                        <Button
                          variant="secondary"
                          onClick={() => requestConfirm(proposal.id, 'approve')}
                        >
                          {ACTION_LABEL.approve}
                        </Button>
                        <Button
                          variant="secondary"
                          onClick={() => requestConfirm(proposal.id, 'reject')}
                        >
                          {ACTION_LABEL.reject}
                        </Button>
                      </span>
                    )}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      )}
    </Panel>
  )
}
