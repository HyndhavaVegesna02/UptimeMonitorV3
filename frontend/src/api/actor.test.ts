import { describe, expect, it } from 'vitest'
import { getActor } from './actor'

describe('getActor', () => {
  it('returns a non-empty actor string', () => {
    const actor = getActor()
    expect(typeof actor).toBe('string')
    expect(actor.length).toBeGreaterThan(0)
  })
})
