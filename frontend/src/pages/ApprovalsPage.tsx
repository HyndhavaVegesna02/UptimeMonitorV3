import { useMemo, useState } from 'react'
import { getActor } from '../api/actor'
import { ApiError, postDecision } from '../api/client'
import type { ComponentTopologyDTO } from '../api/types'
import { EmptyState, ErrorState, LoadingState, PageHeader, Panel } from '../components'
import { ApprovalCard } from '../features/approvals/ApprovalCard'
import { toCardDecisionState } from '../features/approvals/decisionState'
import type { DecisionAction, DecisionUiState } from '../features/approvals/decisionState'
import { useApprovals } from '../features/approvals/useApprovals'
import { useApprovalsTopology } from '../features/approvals/useApprovalsTopology'
import './ApprovalsPage.css'

/**
 * The Approvals tab (STORY-015c; card layout per STORY-059): the human
 * approval gate — a degradation reaches the public Statuspage only after an
 * operator approves it here. Fetches `GET /api/v1/approvals` via
 * `useApprovals` and renders one card per open proposal (STORY-059 AC1):
 * `component_id`, a severity accent stripe DERIVED from `to_status`
 * (`features/approvals/severity.ts`), the `from_status -> to_status`
 * transition (two `StatusBadge`s; "New" when `from_status` is null), and
 * real `proposed_at` — plus Approve/Reject actions.
 *
 * Fields the API does not expose (reason/source/detected-ago/checks/
 * triggering-signals — not on `ProposalDTO`) are OMITTED, never faked
 * (AC3) — deferred to STORY-063 proposal enrichment.
 *
 * The idle -> confirming -> submitting -> failed decision state machine and
 * the 409/404 notice banner are carried over from STORY-015c UNCHANGED
 * (AC2) — only the row markup became a card (`ApprovalCard`).
 */
export function ApprovalsPage() {
  const { state, retry } = useApprovals()
  const topology = useApprovalsTopology()
  const [decisionState, setDecisionState] = useState<DecisionUiState>({ phase: 'idle' })
  const [notice, setNotice] = useState<string | null>(null)

  // Joins each proposal's `component_id` against the topology (STORY-100
  // AC1) for the friendly name + primary signal a card needs. A topology
  // fetch failure/loading tick degrades every card to its raw component_id
  // slug and no evidence — never blocks the queue (AC4) — by staying `{}`
  // rather than surfacing its own error state here.
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
    <div className="approvals-page page">
      <PageHeader
        title="Approvals"
        subtitle="Approving publishes the change to the public status page. Every decision requires confirmation before it submits."
      />

      {notice ? (
        <p className="approvals-page__notice" role="status">
          {notice}
        </p>
      ) : null}

      <Panel>
        {state.phase === 'loading' && <LoadingState label="Loading proposals…" />}

        {state.phase === 'error' && (
          <ErrorState message="Could not load proposals" onRetry={retry} />
        )}

        {state.phase === 'success' && state.data.length === 0 && (
          <EmptyState
            icon="check"
            tone="positive"
            message="Queue clear"
            detail="No proposals awaiting review."
          />
        )}

        {state.phase === 'success' && state.data.length > 0 && (
          <ul className="approval-list">
            {state.data.map((proposal) => (
              <ApprovalCard
                key={proposal.id}
                proposal={proposal}
                component={componentById[proposal.component_id]}
                decision={toCardDecisionState(decisionState, proposal.id)}
                onRequestConfirm={(action) => requestConfirm(proposal.id, action)}
                onCancelConfirm={cancelConfirm}
                onConfirmDecision={(action) => confirmDecision(proposal.id, action)}
              />
            ))}
          </ul>
        )}
      </Panel>
    </div>
  )
}
