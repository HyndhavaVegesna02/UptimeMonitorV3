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

  return (
    <Panel title="Approvals" headingLevel="h1">
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
            {state.data.map((proposal) => (
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
                  <span className="approvals-table__actions">
                    <Button variant="secondary">Approve</Button>
                    <Button variant="secondary">Reject</Button>
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </Panel>
  )
}
