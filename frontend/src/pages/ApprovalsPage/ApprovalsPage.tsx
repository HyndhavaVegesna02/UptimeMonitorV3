import { getApprovals } from '../../api/client'
import { EmptyState } from '../../components/EmptyState/EmptyState'
import { ErrorState } from '../../components/ErrorState/ErrorState'
import { LoadingState } from '../../components/LoadingState/LoadingState'
import { ProposalCard } from '../../features/approvals/ProposalCard'
import { useApprovalsDecisions } from '../../features/approvals/useApprovalsDecisions'
import { useFetch } from '../../lib/useFetch'
import './ApprovalsPage.css'

/**
 * The Approvals page (STORY-131) — the sprint's first mutating page. Every
 * open proposal from `GET /api/v1/approvals`, each with a two-step
 * Approve/Reject -> Confirm/Cancel flow (`useApprovalsDecisions` owns that
 * state machine so "only one proposal mid-decision at a time" is
 * structural, not per-card discipline). A decision success/409/404
 * refreshes the list from the server (`approvalsFetch.retry`) rather than
 * mutating local state optimistically — AC5's "no optimistic-only state".
 * No `<h1>` here — `ShellLayout`'s `Topbar` already owns the page's one
 * top-level heading; each proposal is its own level-three heading via
 * `Panel`'s `headingLevel="h3"`.
 */
export function ApprovalsPage() {
  const approvalsFetch = useFetch(getApprovals)
  const decisions = useApprovalsDecisions(approvalsFetch.retry)

  // Fresh each render, like `DashboardPage`'s `now={new Date()}` — a "what
  // time is it right now" reference for the relative proposed-at label,
  // never a captured success timestamp.
  const now = new Date()

  return (
    <div className="approvals-page">
      <p className="approvals-page__description">
        Pending status-change proposals awaiting a human decision — approve or reject each before it
        reaches Statuspage.
      </p>

      {approvalsFetch.state.phase === 'loading' ? <LoadingState label="Loading proposals…" /> : null}
      {approvalsFetch.state.phase === 'error' ? (
        <ErrorState message={approvalsFetch.state.message} onRetry={approvalsFetch.retry} />
      ) : null}
      {approvalsFetch.state.phase === 'success' ? (
        approvalsFetch.state.data.length === 0 ? (
          <EmptyState
            message="Queue clear"
            detail="No pending proposals right now — nothing needs your review."
          />
        ) : (
          <div className="approvals-page__list">
            {approvalsFetch.state.data.map((proposal) => (
              <ProposalCard
                key={proposal.id}
                proposal={proposal}
                now={now}
                isConfirming={decisions.isConfirming(proposal.id)}
                isSubmitting={decisions.isSubmitting(proposal.id)}
                isBlocked={decisions.isBlocked(proposal.id)}
                action={decisions.actionFor(proposal.id)}
                notice={decisions.noticeFor(proposal.id)}
                onRequestConfirm={(action) => decisions.requestConfirm(proposal.id, action)}
                onCancelConfirm={decisions.cancelConfirm}
                onConfirmDecision={(action) => {
                  void decisions.confirmDecision(proposal.id, action)
                }}
              />
            ))}
          </div>
        )
      ) : null}
    </div>
  )
}
