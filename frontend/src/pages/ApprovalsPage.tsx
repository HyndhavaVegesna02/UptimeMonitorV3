import { useMemo, useState } from 'react'
import { getActor } from '../api/actor'
import { ApiError, postDecision } from '../api/client'
import type { ComponentTopologyDTO } from '../api/types'
import { EmptyState, ErrorState, LoadingState, Tile } from '../components'
import { ApprovalCard } from '../features/approvals/ApprovalCard'
import { toCardDecisionState } from '../features/approvals/decisionState'
import type { DecisionAction, DecisionUiState } from '../features/approvals/decisionState'
import { useApprovals } from '../features/approvals/useApprovals'
import { useApprovalsTopology } from '../features/approvals/useApprovalsTopology'
import './ApprovalsPage.css'

/**
 * The Approvals tab (STORY-107, design brief §Salvage — the evidence-first
 * concept was review-APPROVED on the parked `ui-redesign` branch's
 * STORY-100 work; re-skinned onto Mission Teal here): the human approval
 * gate — a degradation reaches the public Statuspage only after an operator
 * approves it here. Fetches `GET /api/v1/approvals` via `useApprovals`,
 * joins each proposal's `component_id` against `useApprovalsTopology()`
 * (`GET /api/v1/topology`) for a friendly name + primary signal, and renders
 * one evidence-first `Tile` card per open proposal (`ApprovalCard`): a
 * severity accent edge derived from `to_status`, the `from_status ->
 * to_status` transition, real `proposed_at`, per-location evidence, a "View
 * checks" deep link, and Approve/Reject actions.
 *
 * Fields the API does not expose (reason/source/detected-ago/triggering-
 * signals — not on `ProposalDTO`) are OMITTED, never faked. A topology fetch
 * failure/loading tick degrades every card to its raw `component_id` slug
 * and no evidence — never blocks the queue (AC4) — rather than surfacing
 * its own error state on this page.
 *
 * The idle -> confirming -> submitting -> failed decision state machine and
 * the 409/404 notice banner live here (not scoped to a single card): only
 * one proposal can be mid-decision at a time.
 */
export function ApprovalsPage() {
  const { state, retry } = useApprovals()
  const topology = useApprovalsTopology()
  const [decisionState, setDecisionState] = useState<DecisionUiState>({ phase: 'idle' })
  const [notice, setNotice] = useState<string | null>(null)

  // Joins each proposal's `component_id` against the topology for the
  // friendly name + primary signal a card needs. A topology fetch failure/
  // loading tick degrades every card to its raw component_id slug and no
  // evidence — never blocks the queue (AC4) — by staying `{}` rather than
  // surfacing its own error state here.
  const componentById = useMemo<Record<string, ComponentTopologyDTO>>(() => {
    if (topology.state.phase !== 'success') {
      return {}
    }
    return Object.fromEntries(topology.state.data.map((component) => [component.id, component]))
  }, [topology.state])

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
    <div className="approvals-page">
      <div className="approvals-page__header">
        <h1 className="text-h1 approvals-page__title">Approvals</h1>
        <p className="text-caption approvals-page__subtitle">
          Approving publishes the change to the public status page. Every decision requires
          confirmation before it submits.
        </p>
      </div>

      {notice ? (
        <p className="approvals-page__notice" role="status">
          {notice}
        </p>
      ) : null}

      {state.phase === 'loading' && (
        <Tile elevation="md">
          <LoadingState label="Loading proposals…" />
        </Tile>
      )}

      {state.phase === 'error' && (
        <Tile elevation="md">
          <ErrorState message="Could not load proposals" onRetry={retry} />
        </Tile>
      )}

      {state.phase === 'success' && state.data.length === 0 && (
        <Tile elevation="md">
          <EmptyState message="Queue clear" detail="No proposals awaiting review." />
        </Tile>
      )}

      {state.phase === 'success' && state.data.length > 0 && (
        <ul className="approvals-list">
          {state.data.map((proposal) => (
            <li key={proposal.id}>
              <ApprovalCard
                proposal={proposal}
                component={componentById[proposal.component_id]}
                decision={toCardDecisionState(decisionState, proposal.id)}
                onRequestConfirm={(action) => requestConfirm(proposal.id, action)}
                onCancelConfirm={cancelConfirm}
                onConfirmDecision={(action) => confirmDecision(proposal.id, action)}
              />
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
