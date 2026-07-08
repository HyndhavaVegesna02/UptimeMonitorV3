import type { HealthStatus } from '../../components'

/**
 * A proposal card's severity presentation: which health tone paints the
 * accent stripe/chip, and the short uppercase label shown alongside it.
 */
export interface ApprovalSeverity {
  tone: HealthStatus
  label: string
}

const SEVERITY_BY_TO_STATUS: Record<string, ApprovalSeverity> = {
  major_outage: { tone: 'down', label: 'Major' },
  partial_outage: { tone: 'partial', label: 'Partial' },
  degraded: { tone: 'degraded', label: 'Degraded' },
}

const UNKNOWN_SEVERITY: ApprovalSeverity = { tone: 'unknown', label: 'Unknown' }

/**
 * Derives a card's severity from `to_status` ALONE (STORY-059 AC1) — the
 * `ProposalDTO` wire shape has no severity/reason field, so this is never a
 * fake value, only a presentation decision computed from a real field:
 * `major_outage` -> major, `partial_outage` -> partial, `degraded` ->
 * degraded, anything else (in practice: unreachable, since an open proposal
 * is always a degradation per `core/services/decide.py` — a recovery to
 * `operational` auto-publishes and never opens a proposal — but handled
 * defensively rather than assumed) -> unknown.
 *
 * Reuses the shell's existing 7-status health palette (`down` stands in for
 * "major") instead of inventing a parallel severity color scale — the
 * accent stripe/chip share tokens with every other status indicator in the
 * app (STORY-055).
 */
export function deriveSeverity(toStatus: string): ApprovalSeverity {
  return SEVERITY_BY_TO_STATUS[toStatus] ?? UNKNOWN_SEVERITY
}
