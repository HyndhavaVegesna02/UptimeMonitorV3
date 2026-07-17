import { describe, expect, it } from 'vitest'
import { CONFIRM_LABEL, confirmPrompt } from './decisionState'

describe('confirmPrompt', () => {
  it('states the consequence for an approve: component + target status + "public status page" (STORY-100 AC3)', () => {
    const prompt = confirmPrompt('approve', {
      componentLabel: 'Sock Shop — frontend',
      targetStatusLabel: 'Degraded',
    })
    expect(prompt).toBe(
      "Publishes 'Sock Shop — frontend: Degraded' to the public status page.",
    )
  })

  it('leaves the reject prompt unchanged in behavior (STORY-100 AC3 — reject confirm unchanged)', () => {
    const prompt = confirmPrompt('reject', {
      componentLabel: 'Sock Shop — frontend',
      targetStatusLabel: 'Degraded',
    })
    expect(prompt).toBe('Reject this proposal?')
  })
})

describe('CONFIRM_LABEL', () => {
  it('keeps the same confirm-button labels as before', () => {
    expect(CONFIRM_LABEL.approve).toBe('Confirm approve')
    expect(CONFIRM_LABEL.reject).toBe('Confirm reject')
  })
})

