import { toHealthStatus } from '../../api/statusMapping'
import type { PublicationDTO } from '../../api/types'
import { StatusBadge } from '../../components/StatusBadge/StatusBadge'
import { formatObservedAt } from '../history/formatTimestamp'
import { OutcomeChip } from './OutcomeChip'
import './PublicationsTimeline.css'

export interface PublicationsTimelineProps {
  publications: PublicationDTO[]
}

const COLUMN_HEADERS = ['Time', 'Component', 'Status', 'Outcome', 'Proposal', 'Author']

/**
 * The publish-attempt timeline (STORY-133 AC1) — one row per
 * `PublicationDTO`, rendered in the EXACT order given (the endpoint already
 * returns most-recent-first, capped ~50 server-side; this component never
 * re-sorts). Same dense-grid shape as `HistoryGrid` (own `overflow-x`
 * scroll container so the page body never scrolls horizontally),
 * `font-variant-numeric: tabular-nums` on the whole table for the time/
 * proposal-id columns.
 *
 * `status` (the published health) and `outcome` (the Statuspage-call
 * result) are two distinct fields, rendered as two distinct visual
 * elements (`StatusBadge` vs `OutcomeChip`) — never conflated, even when a
 * `failed` outcome pairs with an ok-ish `status` (AC1 crux). Renders ONLY
 * the real wire fields — no `incident_id` or any other invented field
 * (AC2).
 */
export function PublicationsTimeline({ publications }: PublicationsTimelineProps) {
  return (
    <div className="publications-timeline__scroll">
      <table className="publications-timeline__table">
        <thead>
          <tr>
            {COLUMN_HEADERS.map((header) => (
              <th key={header} scope="col">
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {publications.map((publication) => (
            <tr key={publication.id}>
              <td>
                <time dateTime={publication.published_at}>{formatObservedAt(publication.published_at)}</time>
              </td>
              <td>{publication.component_id}</td>
              <td>
                <StatusBadge status={toHealthStatus(publication.status)} />
              </td>
              <td>
                <OutcomeChip outcome={publication.outcome} />
              </td>
              <td className="publications-timeline__proposal">{publication.proposal_id ?? '—'}</td>
              <td className="publications-timeline__author">{publication.author ?? '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
