import { cx } from '../../lib/cx'
import './OutcomeChip.css'

export interface OutcomeChipProps {
  outcome: 'succeeded' | 'failed'
}

const LABELS: Record<OutcomeChipProps['outcome'], string> = {
  succeeded: 'Succeeded',
  failed: 'Failed',
}

/**
 * The Statuspage-call outcome pill (STORY-133 AC1) — dot + text label, never
 * colour alone (same shape as `WindowStateBadge`). Deliberately its own
 * component rather than reusing `StatusBadge`: `outcome` is a distinct
 * concept from the published health status (`PublicationDTO.status`) — a
 * `succeeded` publish of a `degraded` status is a normal, valid combination,
 * so the two badges must never look like the same vocabulary.
 */
export function OutcomeChip({ outcome }: OutcomeChipProps) {
  return (
    <span className={cx('outcome-chip', `outcome-chip--${outcome}`)}>
      <span className="outcome-chip__dot" aria-hidden="true" />
      <span className="outcome-chip__label">{LABELS[outcome]}</span>
    </span>
  )
}
