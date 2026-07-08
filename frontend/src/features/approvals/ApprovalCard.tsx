import { toHealthStatus } from '../../api/statusMapping'
import type { ProposalDTO } from '../../api/types'
import { Button, ErrorState, Icon, StatusBadge } from '../../components'
import { cx } from '../../lib/cx'
import { ACTION_LABEL, CONFIRM_COPY } from './decisionState'
import type { CardDecisionState, DecisionAction } from './decisionState'
import { deriveSeverity } from './severity'
import './ApprovalCard.css'

export interface ApprovalCardProps {
  proposal: ProposalDTO
  /** This card's slice of the page-level decision state machine — already
   * narrowed to `'idle'` unless this proposal is the active row (see
   * `toCardDecisionState`). */
  decision: CardDecisionState
  onRequestConfirm: (action: DecisionAction) => void
  onCancelConfirm: () => void
  onConfirmDecision: (action: DecisionAction) => void
}

/**
 * One pending proposal rendered as a card with a left severity-accent
 * stripe (STORY-059 AC1) — replaces the STORY-015c table row. Severity is
 * DERIVED from `to_status` via `deriveSeverity`, never a fake field. The
 * from -> to transition reuses the shared `StatusBadge` (dot + text, never
 * color alone); `from_status === null` renders "New" instead of a badge
 * (a component's first-ever proposal has no prior status).
 *
 * Approve/Reject preserve the idle -> confirming -> submitting -> failed
 * state machine from STORY-015c exactly (AC2) — only the markup changed;
 * the 409/404 notice banner lives one level up, in `ApprovalsPage`, since
 * it is not scoped to a single card.
 */
export function ApprovalCard({
  proposal,
  decision,
  onRequestConfirm,
  onCancelConfirm,
  onConfirmDecision,
}: ApprovalCardProps) {
  const severity = deriveSeverity(proposal.to_status)

  return (
    <li className={cx('approval-card', `approval-card--${severity.tone}`)}>
      <div className="approval-card__stripe" aria-hidden="true" />
      <div className="approval-card__body">
        <div className="approval-card__main">
          <div className="approval-card__header">
            <span className="approval-card__component text-mono">{proposal.component_id}</span>
            <span className="approval-card__severity">{severity.label}</span>
          </div>

          <div className="approval-card__transition">
            {proposal.from_status ? (
              <StatusBadge status={toHealthStatus(proposal.from_status)} />
            ) : (
              <span className="approval-card__new">New</span>
            )}
            <Icon name="arrow-right" className="approval-card__arrow" />
            <span className="sr-only">to</span>
            <StatusBadge status={toHealthStatus(proposal.to_status)} />
          </div>

          <p className="approval-card__meta">
            Proposed{' '}
            <time className="text-mono" dateTime={proposal.proposed_at}>
              {proposal.proposed_at}
            </time>
          </p>
        </div>

        <div className="approval-card__actions">
          {decision.phase === 'idle' && (
            <>
              <Button variant="primary" onClick={() => onRequestConfirm('approve')}>
                <Icon name="check" />
                {ACTION_LABEL.approve}
              </Button>
              <Button variant="secondary" onClick={() => onRequestConfirm('reject')}>
                {ACTION_LABEL.reject}
              </Button>
            </>
          )}

          {decision.phase === 'confirming' && (
            <>
              <p className="approval-card__confirm-text">
                {CONFIRM_COPY[decision.action].prompt}
              </p>
              <Button variant="primary" onClick={() => onConfirmDecision(decision.action)}>
                {CONFIRM_COPY[decision.action].confirmLabel}
              </Button>
              <Button variant="tertiary" onClick={onCancelConfirm}>
                Cancel
              </Button>
            </>
          )}

          {decision.phase === 'submitting' && (
            <p className="approval-card__confirm-text">Submitting…</p>
          )}

          {decision.phase === 'failed' && (
            <ErrorState
              message={decision.message}
              onRetry={() => onConfirmDecision(decision.action)}
            />
          )}
        </div>
      </div>
    </li>
  )
}
