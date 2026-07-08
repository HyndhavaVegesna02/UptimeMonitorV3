import { toHealthStatus } from '../api/statusMapping'
import type { PublicationDTO } from '../api/types'
import {
  EmptyState,
  ErrorState,
  Icon,
  LoadingState,
  Panel,
  StatusBadge,
  Timeline,
  TimelineItem,
} from '../components'
import { usePublications } from '../features/publications/usePublications'
import './PublicationsPage.css'

/** `proposal_id` renders as a mono id; `null` (no originating proposal)
 * renders as an em-dash — NEVER a sentinel `0` (carried forward unchanged
 * from STORY-015g into the STORY-062 timeline redesign). */
function formatProposalId(proposalId: number | null): string {
  return proposalId === null ? '—' : String(proposalId)
}

/** Renders `PublicationDTO.outcome` (STORY-072 AC4) as a dot+text chip,
 * reusing `StatusBadge` so the outcome NEVER relies on color alone: `up`
 * (green) for `succeeded`, `down` (red) for `failed`, token-only colors
 * throughout. `outcome` is DISTINCT from `status` (the health status
 * attempted) — this is whether the Statuspage call itself succeeded. */
function OutcomeChip({ outcome }: { outcome: PublicationDTO['outcome'] }) {
  return (
    <StatusBadge
      status={outcome === 'succeeded' ? 'up' : 'down'}
      label={outcome === 'succeeded' ? 'Succeeded' : 'Failed'}
    />
  )
}

/**
 * The Publications tab (STORY-062, sprint-38 Operator Dashboard redesign;
 * STORY-072 added the outcome chip): a vertical timeline audit trail of
 * every approve publish ATTEMPT — "what did customers see, and when"
 * (dossier §17; reference mock's `isPublications` section), now including
 * attempts where the Statuspage call itself failed (STORY-072: publications
 * are recorded independent of Statuspage success). Fetches
 * `GET /api/v1/publications` via `usePublications` (a plain
 * `useFetch(getPublications)` wrapper) and renders one `TimelineItem` per
 * publication, newest-first exactly as the API returns them — there is no
 * from-status on `PublicationDTO`, so unlike a changelog diff this shows
 * only the single published status per row. The mock's author/incident
 * fields are still OMITTED: `PublicationDTO` carries neither — see
 * STORY-066 for the follow-up that would add that metadata. The endpoint
 * caps at the repository's most-recent 50 (`list_recent`, no pagination) —
 * stated in the header copy so the cap is visible, never silent (AC2).
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
        <Timeline aria-label="Publication log">
          {state.data.map((publication, index) => (
            <TimelineItem
              key={publication.id}
              tone={toHealthStatus(publication.status)}
              isLast={index === state.data.length - 1}
            >
              <div className="publications-page__row-head">
                <span className="text-mono publications-page__scope">
                  {publication.component_id}
                </span>
                <Icon name="arrow-right" className="publications-page__arrow" />
                <StatusBadge status={toHealthStatus(publication.status)} />
                <OutcomeChip outcome={publication.outcome} />
              </div>
              <div className="publications-page__meta text-mono text-caption">
                <span>{publication.published_at}</span>
                <span aria-hidden="true"> · </span>
                <span>Proposal {formatProposalId(publication.proposal_id)}</span>
              </div>
            </TimelineItem>
          ))}
        </Timeline>
      )}
    </Panel>
  )
}
