import { getPublications } from '../../api/client'
import { EmptyState } from '../../components/EmptyState/EmptyState'
import { ErrorState } from '../../components/ErrorState/ErrorState'
import { LoadingState } from '../../components/LoadingState/LoadingState'
import { Panel } from '../../components/Panel/Panel'
import { PublicationsTimeline } from '../../features/publications/PublicationsTimeline'
import { useFetch } from '../../lib/useFetch'
import './PublicationsPage.css'

/**
 * The Publications page (STORY-133) — the sprint's final page, and the
 * simplest: a read-only timeline of `GET /api/v1/publications`, rendered in
 * the EXACT order the endpoint returns it (most-recent-first, capped ~50
 * server-side, no pagination — noted in the description below). No `<h1>`
 * here — `ShellLayout`'s `Topbar` already owns the page's one top-level
 * heading (same convention as `ApprovalsPage`/`MaintenancePage`).
 */
export function PublicationsPage() {
  const publicationsFetch = useFetch(getPublications)

  return (
    <div className="publications-page">
      <p className="publications-page__description">
        Recorded Statuspage publish attempts, newest first — showing up to the 50 most recent
        attempts (server-capped, no pagination).
      </p>

      {publicationsFetch.state.phase === 'loading' ? (
        <LoadingState label="Loading publish history…" />
      ) : null}
      {publicationsFetch.state.phase === 'error' ? (
        <ErrorState message={publicationsFetch.state.message} onRetry={publicationsFetch.retry} />
      ) : null}
      {publicationsFetch.state.phase === 'success' ? (
        publicationsFetch.state.data.length === 0 ? (
          <EmptyState
            message="Nothing published yet"
            detail="Statuspage publish attempts will show up here as they happen."
          />
        ) : (
          <Panel title="Publish timeline" headingLevel="h2" className="publications-page__panel">
            <PublicationsTimeline publications={publicationsFetch.state.data} />
          </Panel>
        )
      ) : null}
    </div>
  )
}
