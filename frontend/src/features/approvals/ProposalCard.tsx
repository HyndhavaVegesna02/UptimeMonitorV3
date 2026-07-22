import { ArrowRight } from '@phosphor-icons/react'
import type { KeyboardEvent } from 'react'
import { useEffect, useRef } from 'react'
import { toHealthStatus } from '../../api/statusMapping'
import type { ProposalDTO } from '../../api/types'
import { Button } from '../../components/Button/Button'
import { Icon } from '../../components/Icon/Icon'
import { Panel } from '../../components/Panel/Panel'
import { StatusBadge } from '../../components/StatusBadge/StatusBadge'
import { cx } from '../../lib/cx'
import { formatRelativeTime } from '../../lib/relativeTime'
import type { DecisionAction, DecisionNotice } from './useApprovalsDecisions'
import './ProposalCard.css'

export interface ProposalCardProps {
  proposal: ProposalDTO
  /** "What time is it right now" for the relative proposed-at label — a
   * fresh `new Date()` read at the page level each render (same discipline
   * as `DashboardPage`), never captured once and gone stale. */
  now: Date
  isConfirming: boolean
  isSubmitting: boolean
  /** True while a DIFFERENT proposal is mid-decision (AC3). */
  isBlocked: boolean
  action?: DecisionAction
  notice?: DecisionNotice
  onRequestConfirm: (action: DecisionAction) => void
  onCancelConfirm: () => void
  onConfirmDecision: (action: DecisionAction) => void
}

const ACTION_VERB: Record<DecisionAction, string> = {
  approve: 'approve',
  reject: 'reject',
}

/**
 * One pending proposal (STORY-131 AC1/AC2/AC3/AC4/AC7) — the from -> to
 * health-badge transition (a null `from_status` renders as a neutral "New"
 * chip, never a fabricated status), the proposed-at relative time, and the
 * two-step Approve/Reject -> Confirm/Cancel flow. Deliberately renders ONLY
 * wire fields (`component_id`, `from_status`/`to_status`, `proposed_at`) —
 * the wire has no severity/reason (plan §Approvals edge behavior), so none
 * is fabricated here.
 *
 * Confirm/submit/notice state is lifted to the page's `useApprovalsDecisions`
 * (so "only one proposal mid-decision at a time" is structural, not a
 * per-card convention) — this component is a controlled, presentational
 * consumer of that state (ui-ux-pro-max: confirm before an irreversible
 * action; web-design-guidelines: every control keeps an accessible name,
 * the confirm prompt stays keyboard-reachable and dismissable).
 */
export function ProposalCard({
  proposal,
  now,
  isConfirming,
  isSubmitting,
  isBlocked,
  action,
  notice,
  onRequestConfirm,
  onCancelConfirm,
  onConfirmDecision,
}: ProposalCardProps) {
  const confirmButtonRef = useRef<HTMLButtonElement>(null)
  const lastTriggerRef = useRef<HTMLButtonElement | null>(null)
  const pendingRefocus = useRef(false)

  // Focus moves TO the Confirm button the instant the two-step prompt opens
  // (AC7: focus managed sensibly across the state transitions) — a
  // keyboard operator lands exactly where the next action is.
  useEffect(() => {
    if (isConfirming) {
      confirmButtonRef.current?.focus()
    }
  }, [isConfirming])

  // Focus returns to whichever trigger (Approve/Reject) opened the prompt,
  // but ONLY after an explicit cancel (Escape/Cancel button) — a resolved
  // decision removes the proposal from the list on refresh, so there is
  // nothing sensible left to refocus.
  useEffect(() => {
    if (!isConfirming && !isSubmitting && pendingRefocus.current) {
      pendingRefocus.current = false
      lastTriggerRef.current?.focus()
    }
  }, [isConfirming, isSubmitting])

  function handleCancel() {
    pendingRefocus.current = true
    onCancelConfirm()
  }

  function handleKeyDown(event: KeyboardEvent) {
    if (event.key === 'Escape') {
      handleCancel()
    }
  }

  function handleRequestConfirm(nextAction: DecisionAction, trigger: HTMLButtonElement | null) {
    lastTriggerRef.current = trigger
    onRequestConfirm(nextAction)
  }

  const showConflictOrGoneNotice =
    notice && (notice.kind === 'conflict' || notice.kind === 'gone') ? notice : undefined
  const showErrorNotice = notice && notice.kind === 'error' ? notice : undefined
  // AC3: the confirm/cancel affordance stays mounted through submitting
  // (disabled, not gone) — only `isConfirming` alone would flip back to
  // idle Approve/Reject while a request is genuinely in flight.
  const showConfirmBlock = isConfirming || isSubmitting

  return (
    <Panel headingLevel="h3" className="proposal-card">
      <div className="proposal-card__header">
        <span className="proposal-card__component">{proposal.component_id}</span>
        <time className="proposal-card__time" dateTime={proposal.proposed_at}>
          {formatRelativeTime(new Date(proposal.proposed_at), now)}
        </time>
      </div>

      <div className="proposal-card__transition">
        {proposal.from_status === null ? (
          <StatusBadge status="unknown" label="New" />
        ) : (
          <StatusBadge status={toHealthStatus(proposal.from_status)} />
        )}
        <Icon icon={ArrowRight} aria-hidden size={14} className="proposal-card__arrow" />
        <StatusBadge status={toHealthStatus(proposal.to_status)} />
      </div>

      {showConflictOrGoneNotice ? (
        <p className="proposal-card__notice proposal-card__notice--info" role="status">
          {showConflictOrGoneNotice.message}
        </p>
      ) : null}

      {showConfirmBlock ? (
        <div className="proposal-card__confirm" onKeyDown={handleKeyDown}>
          {showErrorNotice ? (
            <p className="proposal-card__notice proposal-card__notice--error" role="alert">
              {showErrorNotice.message}
            </p>
          ) : (
            <p className="proposal-card__confirm-prompt">
              {`Confirm ${action ? ACTION_VERB[action] : ''} for ${proposal.component_id}?`}
            </p>
          )}
          <div className="proposal-card__actions">
            {/* A plain native button (not the shared `Button` primitive,
               which doesn't forward refs) so this is the one imperative
               focus target the state machine needs — same visual classes
               `Button` itself applies. */}
            <button
              ref={confirmButtonRef}
              type="button"
              className="button button--primary"
              disabled={isSubmitting || !action}
              onClick={() => action && onConfirmDecision(action)}
            >
              {isSubmitting
                ? 'Submitting…'
                : showErrorNotice
                  ? 'Retry'
                  : `Confirm ${action ? ACTION_VERB[action] : ''}`}
            </button>
            <Button variant="ghost" disabled={isSubmitting} onClick={handleCancel}>
              Cancel
            </Button>
          </div>
        </div>
      ) : (
        <div className="proposal-card__actions">
          <Button
            disabled={isBlocked}
            variant="secondary"
            aria-label={`Approve ${proposal.component_id}`}
            onClick={(event) => handleRequestConfirm('approve', event.currentTarget)}
          >
            Approve
          </Button>
          <Button
            disabled={isBlocked}
            variant="secondary"
            className={cx('proposal-card__reject-button')}
            aria-label={`Reject ${proposal.component_id}`}
            onClick={(event) => handleRequestConfirm('reject', event.currentTarget)}
          >
            Reject
          </Button>
        </div>
      )}
    </Panel>
  )
}
