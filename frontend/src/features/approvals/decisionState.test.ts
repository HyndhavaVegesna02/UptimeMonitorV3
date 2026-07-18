import { describe, expect, it } from 'vitest'
import { confirmPrompt, toCardDecisionState } from './decisionState'
import type { DecisionUiState } from './decisionState'

describe('confirmPrompt', () => {
  it('states the publish consequence naming the component and target status on approve (STORY-107 AC3)', () => {
    expect(
      confirmPrompt('approve', {
        componentLabel: 'Sock Shop — frontend',
        targetStatusLabel: 'Degraded',
      }),
    ).toBe("Publishes 'Sock Shop — frontend: Degraded' to the public status page.")
  })

  it('leaves the reject prompt unchanged (no publish consequence — a reject never touches the public status page)', () => {
    expect(
      confirmPrompt('reject', {
        componentLabel: 'Sock Shop — frontend',
        targetStatusLabel: 'Degraded',
      }),
    ).toBe('Reject this proposal?')
  })
})

describe('toCardDecisionState', () => {
  it('narrows to idle for a proposal that is not the active row', () => {
    const state: DecisionUiState = { phase: 'confirming', proposalId: 1, action: 'approve' }
    expect(toCardDecisionState(state, 2)).toEqual({ phase: 'idle' })
  })

  it('passes through the active row unchanged', () => {
    const state: DecisionUiState = { phase: 'confirming', proposalId: 1, action: 'approve' }
    expect(toCardDecisionState(state, 1)).toEqual(state)
  })
})
