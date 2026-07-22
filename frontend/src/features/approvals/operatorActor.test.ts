import { describe, expect, it } from 'vitest'
import { OPERATOR_ACTOR } from './operatorActor'

describe('OPERATOR_ACTOR', () => {
  it('is a non-blank fixed actor string (the single swap-point for future auth)', () => {
    expect(typeof OPERATOR_ACTOR).toBe('string')
    expect(OPERATOR_ACTOR.trim().length).toBeGreaterThan(0)
  })
})
