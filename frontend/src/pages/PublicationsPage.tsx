import { toHealthStatus } from '../api/statusMapping'
import { EmptyState, ErrorState, LoadingState, Panel, StatusBadge } from '../components'
import { usePublications } from '../features/publications/usePublications'
import './PublicationsPage.css'

/** `proposal_id` renders as a mono id; `null` (no originating proposal)
 * renders as an em-dash — NEVER a sentinel `0` (STORY-015g AC1). */
function formatProposalId(proposalId: number | null): string {
  return proposalId === null ? '—' : String(proposalId)
}

/**
 * The Publications tab (STORY-015g): a read-only audit trail of what was
 * actually pushed to the public Statuspage, and when — "what did customers
 * see, and when" (dossier §17). Fetches `GET /api/v1/publications` via
 * `usePublications` (a plain `useFetch(getPublications)` wrapper — no
 * selector/params, matching the Dashboard read-tab shape) and renders one row
 * per publication, newest-first exactly as the API returns them. There is no
 * from-status on `PublicationDTO`, so unlike a changelog diff this shows only
 * the single published status per row (AC1). The endpoint caps at the
 * repository's most-recent 50 (`list_recent`, no pagination) — stated in the
 * header copy so the cap is visible, never silent (AC3).
 */
export function PublicationsPage() {
  const { state, retry } = usePublications()

  return (
    <Panel title="Publications" headingLevel="h1">
      <p className="publications-page__cap-note text-caption">
        Showing the latest 50 publications
      </p>

      {state.phase === 'loading' && <LoadingState label="Loading publications…" />}

      {state.phase === 'error' && (
        <ErrorState message="Could not load publications" onRetry={retry} />
      )}

      {state.phase === 'success' && state.data.length === 0 && (
        <EmptyState message="Nothing published yet" />
      )}

      {state.phase === 'success' && state.data.length > 0 && (
        <table className="publications-table">
          <thead>
            <tr>
              <th scope="col">Published at</th>
              <th scope="col">Component</th>
              <th scope="col">Status</th>
              <th scope="col">Proposal</th>
            </tr>
          </thead>
          <tbody>
            {state.data.map((publication) => (
              <tr key={publication.id}>
                <td>
                  <span className="text-mono">{publication.published_at}</span>
                </td>
                <td>{publication.component_id}</td>
                <td>
                  <StatusBadge status={toHealthStatus(publication.status)} />
                </td>
                <td>
                  <span className="text-mono">
                    {formatProposalId(publication.proposal_id)}
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
