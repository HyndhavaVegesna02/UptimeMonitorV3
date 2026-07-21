import { useState, useCallback } from 'react'
import { CaretRight } from '@phosphor-icons/react'
import { getApprovals, getComponents, postDecision, ApiError } from '../../api/client'
import { toHealthStatus } from '../../api/statusMapping'
import type { ProposalDTO } from '../../api/types'
import { Button } from '../../components/Button/Button'
import { EmptyState } from '../../components/EmptyState/EmptyState'
import { ErrorState } from '../../components/ErrorState/ErrorState'
import { Icon } from '../../components/Icon/Icon'
import { LoadingState } from '../../components/LoadingState/LoadingState'
import { Panel } from '../../components/Panel/Panel'
import { StatusBadge } from '../../components/StatusBadge/StatusBadge'
import { useFetch } from '../../lib/useFetch'

const ACTOR_CONSTANT = 'dashboard-operator'

type ProposalCardState =
  | { mode: 'idle' }
  | { mode: 'confirming'; action: 'approve' | 'reject' }
  | { mode: 'submitting'; action: 'approve' | 'reject' }
  | { mode: 'error'; message: string; is409?: boolean }

interface ProposalCardProps {
  proposal: ProposalDTO
  componentName: string
  onRefreshNeeded: () => void
}

function ProposalCard({ proposal, componentName, onRefreshNeeded }: ProposalCardProps) {
  const [state, setState] = useState<ProposalCardState>({ mode: 'idle' })

  const handleDecision = async (action: 'approve' | 'reject') => {
    setState({ mode: 'submitting', action })
    try {
      await postDecision(proposal.id, {
        action,
        actor: ACTOR_CONSTANT,
      })
      onRefreshNeeded()
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 409) {
          setState({
            mode: 'error',
            message: 'This proposal has already been resolved or closed.',
            is409: true,
          })
          return
        }
        if (err.status === 404) {
          setState({
            mode: 'error',
            message: 'This proposal no longer exists.',
            is409: false,
          })
          return
        }
        setState({
          mode: 'error',
          message: err.detail ?? err.message,
        })
      } else {
        setState({
          mode: 'error',
          message: (err as Error).message ?? 'An error occurred while submitting decision.',
        })
      }
    }
  }

  const fromHealth = proposal.from_status ? toHealthStatus(proposal.from_status) : null
  const toHealth = toHealthStatus(proposal.to_status)

  return (
    <Panel title={componentName}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-md)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: 'var(--font-xs)',
              color: 'var(--color-text-secondary)',
              backgroundColor: 'var(--color-bg-subtle)',
              padding: '2px 6px',
              borderRadius: 'var(--radius-sm)',
            }}
          >
            #{proposal.id}
          </span>
          <span
            style={{
              fontSize: 'var(--font-xs)',
              color: 'var(--color-text-secondary)',
              fontFamily: 'var(--font-mono)',
            }}
          >
            Proposed {new Date(proposal.proposed_at).toLocaleString()}
          </span>
        </div>

        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--space-md)',
            padding: 'var(--space-md)',
            backgroundColor: 'var(--color-bg-subtle)',
            borderRadius: 'var(--radius-md)',
          }}
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <span style={{ fontSize: 'var(--font-xs)', color: 'var(--color-text-secondary)' }}>
              Current Status
            </span>
            {fromHealth ? (
              <StatusBadge status={fromHealth} />
            ) : (
              <span
                style={{
                  fontSize: 'var(--font-xs)',
                  color: 'var(--color-text-secondary)',
                  fontStyle: 'italic',
                }}
              >
                New (None)
              </span>
            )}
          </div>

          <Icon icon={CaretRight} label="transitions to" />

          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <span style={{ fontSize: 'var(--font-xs)', color: 'var(--color-text-secondary)' }}>
              Proposed Status
            </span>
            <StatusBadge status={toHealth} />
          </div>
        </div>

        {state.mode === 'error' && (
          <div
            role="alert"
            style={{
              padding: 'var(--space-sm) var(--space-md)',
              backgroundColor: 'var(--color-health-down-bg)',
              color: 'var(--color-health-down-text)',
              borderRadius: 'var(--radius-sm)',
              fontSize: 'var(--font-sm)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: 'var(--space-sm)',
            }}
          >
            <span>{state.message}</span>
            <Button
              variant="ghost"
              onClick={() => {
                setState({ mode: 'idle' })
                onRefreshNeeded()
              }}
            >
              Refresh List
            </Button>
          </div>
        )}

        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-sm)', justifyContent: 'flex-end' }}>
          {state.mode === 'idle' && (
            <>
              <Button
                variant="primary"
                onClick={() => setState({ mode: 'confirming', action: 'approve' })}
              >
                Approve
              </Button>
              <Button
                variant="ghost"
                onClick={() => setState({ mode: 'confirming', action: 'reject' })}
              >
                Reject
              </Button>
            </>
          )}

          {state.mode === 'confirming' && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-sm)' }}>
              <span style={{ fontSize: 'var(--font-sm)', color: 'var(--color-text-secondary)' }}>
                {state.action === 'approve'
                  ? 'Confirm approving this status transition?'
                  : 'Confirm rejecting this proposal?'}
              </span>
              <Button
                variant={state.action === 'approve' ? 'primary' : 'secondary'}
                onClick={() => handleDecision(state.action)}
              >
                Confirm {state.action === 'approve' ? 'Approve' : 'Reject'}
              </Button>
              <Button
                variant="ghost"
                onClick={() => setState({ mode: 'idle' })}
              >
                Cancel
              </Button>
            </div>
          )}

          {state.mode === 'submitting' && (
            <span style={{ fontSize: 'var(--font-sm)', color: 'var(--color-text-secondary)' }}>
              Submitting decision…
            </span>
          )}
        </div>
      </div>
    </Panel>
  )
}

export function ApprovalsView() {
  const fetcher = useCallback(async () => {
    const [proposals, components] = await Promise.all([
      getApprovals(),
      getComponents(),
    ])
    const compMap = new Map(components.map((c) => [c.id, c.name]))
    return { proposals, compMap }
  }, [])

  const { state, retry } = useFetch(fetcher)

  const loading = state.phase === 'loading'
  const error = state.phase === 'error' ? state : null
  const proposals = state.phase === 'success' ? state.data.proposals : undefined
  const compMap = state.phase === 'success' ? state.data.compMap : undefined

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-lg)' }}>
      <p
        style={{
          fontSize: 'var(--font-sm)',
          color: 'var(--color-text-secondary)',
          margin: 0,
        }}
      >
        Human-in-the-loop review queue for status degradation and recovery proposals.
      </p>

      {loading && <LoadingState label="Loading pending approval requests…" />}

      {error && (
        <ErrorState
          message={error.message ?? 'Failed to load approvals queue'}
          onRetry={retry}
        />
      )}

      {!loading && !error && proposals && proposals.length === 0 && (
        <EmptyState message="No pending approval requests." />
      )}

      {!loading && !error && proposals && proposals.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-md)' }}>
          {proposals.map((proposal) => (
            <ProposalCard
              key={proposal.id}
              proposal={proposal}
              componentName={compMap?.get(proposal.component_id) ?? proposal.component_id}
              onRefreshNeeded={retry}
            />
          ))}
        </div>
      )}
    </div>
  )
}
