import { Link } from 'react-router-dom'
import { toHealthStatus } from '../../api/statusMapping'
import type { ComponentTopologyDTO, ProposalDTO } from '../../api/types'
import {
  Button,
  defaultStatusLabel,
  ErrorState,
  Icon,
  RelativeTime,
  StatusBadge,
} from '../../components'
import { cx } from '../../lib/cx'
import { formatLocationLabel } from '../../lib/formatLocation'
import { ACTION_LABEL, CONFIRM_LABEL, confirmPrompt } from './decisionState'
import type { CardDecisionState, DecisionAction } from './decisionState'
import { deriveSeverity } from './severity'
import { useProposalEvidence } from './useProposalEvidence'
import './ApprovalCard.css'

export interface ApprovalCardProps {
  proposal: ProposalDTO
  /** The proposal's component topology entry (name + signals), resolved by
   * `ApprovalsPage` from `useApprovalsTopology()` joined on `component_id` —
   * `undefined` while topology is loading/failed/absent for this component
   * (STORY-100 AC4 graceful degradation: the card falls back to the raw
   * `component_id` slug and renders no evidence/"View checks" link, but
   * stays fully actionable). */
  component: ComponentTopologyDTO | undefined
  /** This card's slice of the page-level decision state machine — already
   * narrowed to `'idle'` unless this proposal is the active row (see
   * `toCardDecisionState`). */
  decision: CardDecisionState
  onRequestConfirm: (action: DecisionAction) => void
  onCancelConfirm: () => void
  onConfirmDecision: (action: DecisionAction) => void
}

/** `latency_ms` renders as integer milliseconds; `null` (no measurement)
 * renders as an em-dash — the same convention every latency-rendering
 * surface in this app uses (kept as this file's own copy per the sprint-38
 * Wave-2 file-scope isolation rule — see `CheckHistoryPage.tsx::formatLatency`). */
function formatLatencyMs(latencyMs: number | null): string {
  return latencyMs === null ? '—' : `${latencyMs} ms`
}

/**
 * One pending proposal rendered as an evidence-first card (STORY-100,
 * journal finding #4/#14, decision D5) with a left severity-accent stripe
 * (STORY-059 AC1). Severity is DERIVED from `to_status` via `deriveSeverity`,
 * never a fake field. The from -> to transition reuses the shared
 * `StatusBadge` (dot + text, never color alone); `from_status === null`
 * renders "New" instead of a badge (a component's first-ever proposal has no
 * prior status).
 *
 * `component` (resolved by `ApprovalsPage` from topology) supplies the
 * friendly name (`proposal.component_id` stays visible as a secondary slug)
 * and the primary signal fed to `useProposalEvidence` (STORY-100 AC1): a
 * per-location "latest result" list (status/latency/relative time), a
 * compact skeleton while loading, and a quiet "Evidence unavailable" note on
 * a fetch failure — the card NEVER blocks Approve/Reject on evidence (AC4).
 * A resolved primary signal also renders a "View checks" deep link to Check
 * History, pre-filtered to that signal (AC2).
 *
 * Approve/Reject preserve the idle -> confirming -> submitting -> failed
 * state machine from STORY-015c exactly (AC2) — only the markup changed;
 * the 409/404 notice banner lives one level up, in `ApprovalsPage`, since
 * it is not scoped to a single card. The approve confirm step states the
 * publish consequence (component + target status, STORY-100 AC3, via
 * `confirmPrompt`); the reject prompt is unchanged.
 *
 * "Proposed …" (STORY-098) renders via the shared `RelativeTime` primitive —
 * relative text ticking at least once a minute, the raw `proposed_at`
 * instant on `dateTime`, and an absolute-local + raw-UTC tooltip — never the
 * bare ISO string as primary text.
 */
export function ApprovalCard({
  proposal,
  component,
  decision,
  onRequestConfirm,
  onCancelConfirm,
  onConfirmDecision,
}: ApprovalCardProps) {
  const severity = deriveSeverity(proposal.to_status)
  const componentName = component?.name ?? proposal.component_id
  const primarySignal = component?.signals[0]
  const evidence = useProposalEvidence(primarySignal?.signal_key)
  const targetStatusLabel = defaultStatusLabel(toHealthStatus(proposal.to_status))

  return (
    <li className={cx('approval-card', `approval-card--${severity.tone}`)}>
      <div className="approval-card__stripe" aria-hidden="true" />
      <div className="approval-card__body">
        <div className="approval-card__main">
          <div className="approval-card__header">
            <div className="approval-card__identity">
              <span className="approval-card__component">{componentName}</span>
              <span className="approval-card__slug text-mono">{proposal.component_id}</span>
            </div>
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
            Proposed <RelativeTime iso={proposal.proposed_at} className="text-mono" />
          </p>

          <div className="approval-card__evidence">
            {evidence.state.phase === 'loading' && (
              <ul className="approval-card__evidence-skeleton" aria-hidden="true">
                <li />
                <li />
              </ul>
            )}

            {evidence.state.phase === 'error' && (
              <p className="approval-card__evidence-note">Evidence unavailable</p>
            )}

            {evidence.state.phase === 'success' && evidence.state.data.length === 0 && (
              <p className="approval-card__evidence-note">No recent checks recorded</p>
            )}

            {evidence.state.phase === 'success' && evidence.state.data.length > 0 && (
              <ul className="approval-card__locations">
                {evidence.state.data.map((row) => (
                  <li key={row.location} className="approval-card__location-row">
                    <span className="text-mono" title={row.location}>
                      {formatLocationLabel(row.location)}
                    </span>
                    <StatusBadge status={row.status} />
                    <span className="text-mono">{formatLatencyMs(row.latencyMs)}</span>
                    <RelativeTime iso={row.observedAt} className="text-mono" />
                  </li>
                ))}
              </ul>
            )}
          </div>

          {primarySignal ? (
            <Link
              to={`/check-history?signal=${encodeURIComponent(primarySignal.signal_key)}`}
              className="approval-card__view-checks"
            >
              View checks
            </Link>
          ) : null}
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
                {confirmPrompt(decision.action, {
                  componentLabel: componentName,
                  targetStatusLabel,
                })}
              </p>
              <Button variant="primary" onClick={() => onConfirmDecision(decision.action)}>
                {CONFIRM_LABEL[decision.action]}
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
