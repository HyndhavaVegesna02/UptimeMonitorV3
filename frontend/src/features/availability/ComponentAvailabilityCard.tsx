import { CaretDown, CaretUp, Warning } from '@phosphor-icons/react'
import type { ReactNode } from 'react'
import { useCallback, useId, useState } from 'react'
import { getComponentAvailability } from '../../api/client'
import type { AvailabilityDTO, ComponentAvailabilityDTO, ComponentTopologyDTO } from '../../api/types'
import { Button } from '../../components/Button/Button'
import { ErrorState } from '../../components/ErrorState/ErrorState'
import { Icon } from '../../components/Icon/Icon'
import { LoadingState } from '../../components/LoadingState/LoadingState'
import { Panel } from '../../components/Panel/Panel'
import { StatusBadge } from '../../components/StatusBadge/StatusBadge'
import { useFetch } from '../../lib/useFetch'
import {
  availabilityBand,
  deriveDownCount,
  formatAvailabilityPercent,
  isLowCompleteness,
} from './format'
import { joinSignalAvailability } from './joinSignalAvailability'
import './ComponentAvailabilityCard.css'

export interface ComponentAvailabilityCardProps {
  component: ComponentTopologyDTO
  since: string
  until: string
}

const COLUMN_HEADERS = [
  'Component',
  'Availability',
  'Completeness',
  'Total',
  'Passing',
  'Maintenance',
  'Down',
  'Gap',
  'Locations',
]

/** A percentage table cell: the numeric part from `formatAvailabilityPercent`
 * plus a `%` unit rendered as a sibling JSX text node with a literal
 * `&nbsp;` (never embedded in the formatter's returned string - matches
 * `ComponentsRoster.tsx`'s `&nbsp;ms` convention). `null` renders just
 * "No data", no unit. A plain render-helper function, not a component (no
 * new component identity per render - vercel-react-best-practices). */
function renderPercentCell(fraction: number | null): ReactNode {
  const formatted = formatAvailabilityPercent(fraction)
  if (fraction === null) {
    return formatted
  }
  return (
    <>
      {formatted}&nbsp;%
    </>
  )
}

/** One `<tr>` for an `AvailabilityDTO` (rollup or a joined signal), shared by
 * both grains so their columns always stay in lockstep (checklist: N
 * same-shape variants share one assembly helper). */
function AvailabilityRow({
  nameCell,
  availability,
}: {
  nameCell: ReactNode
  availability: AvailabilityDTO
}) {
  const lowCompleteness = isLowCompleteness(availability.completeness_pct)

  return (
    <tr>
      <td className="component-availability-card__name-cell">{nameCell}</td>
      <td>{renderPercentCell(availability.availability_pct)}</td>
      <td>
        {renderPercentCell(availability.completeness_pct)}
        {lowCompleteness ? (
          <span className="component-availability-card__low-flag">
            <Icon icon={Warning} aria-hidden size={12} />
            Low data
          </span>
        ) : null}
      </td>
      <td>{availability.total_verdicts}</td>
      <td>{availability.passing_verdicts}</td>
      <td>{availability.maintenance_verdicts}</td>
      <td>{deriveDownCount(availability)}</td>
      <td>{availability.gap_verdicts}</td>
      <td>{availability.distinct_locations}</td>
    </tr>
  )
}

/**
 * One component's availability region (STORY-129 AC1/AC2/AC5) - fetches its
 * OWN `getComponentAvailability` independently of every other card (no
 * shared/bundled `Promise.all` - a slow component never blocks a fast one,
 * the STORY-122 first-paint lesson). Renders the rollup row plus, when the
 * response carries signal children, an expandable per-signal drill-down
 * joined onto their topology display names.
 */
export function ComponentAvailabilityCard({ component, since, until }: ComponentAvailabilityCardProps) {
  const [expanded, setExpanded] = useState(false)
  const signalsId = useId()

  const fetcher = useCallback(
    () => getComponentAvailability(component.id, { since, until }),
    [component.id, since, until],
  )
  const { state, retry } = useFetch(fetcher)

  return (
    <Panel title={component.name} headingLevel="h2" className="component-availability-card">
      {state.phase === 'loading' ? <LoadingState /> : null}
      {state.phase === 'error' ? <ErrorState message={state.message} onRetry={retry} /> : null}
      {state.phase === 'success' ? (
        <ComponentAvailabilityTable
          component={component}
          data={state.data}
          expanded={expanded}
          onToggleExpanded={() => setExpanded((value) => !value)}
          signalsId={signalsId}
        />
      ) : null}
    </Panel>
  )
}

function ComponentAvailabilityTable({
  component,
  data,
  expanded,
  onToggleExpanded,
  signalsId,
}: {
  component: ComponentTopologyDTO
  data: ComponentAvailabilityDTO
  expanded: boolean
  onToggleExpanded: () => void
  signalsId: string
}) {
  const joinedSignals = joinSignalAvailability(component.signals, data.signals)
  const hasSignals = joinedSignals.length > 0
  const band = availabilityBand(data.rollup.availability_pct)

  return (
    <div className="component-availability-card__scroll">
      <table className="component-availability-card__table">
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
          <AvailabilityRow
            nameCell={
              <div className="component-availability-card__name">
                <StatusBadge status={band} />
                <span>{component.name}</span>
                {hasSignals ? (
                  <Button
                    variant="ghost"
                    aria-expanded={expanded}
                    aria-controls={signalsId}
                    onClick={onToggleExpanded}
                  >
                    <Icon icon={expanded ? CaretUp : CaretDown} aria-hidden size={14} />
                    {expanded
                      ? 'Hide signals'
                      : `${joinedSignals.length} signal${joinedSignals.length === 1 ? '' : 's'}`}
                  </Button>
                ) : null}
              </div>
            }
            availability={data.rollup}
          />
        </tbody>
        {hasSignals ? (
          <tbody id={signalsId} className="component-availability-card__signals" hidden={!expanded}>
            {joinedSignals.map((signal) => (
              <AvailabilityRow key={signal.signal_key} nameCell={signal.name} availability={signal} />
            ))}
          </tbody>
        ) : null}
      </table>
    </div>
  )
}
