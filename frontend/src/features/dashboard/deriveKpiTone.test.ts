import { describe, expect, it } from 'vitest'
import { approvalsTone, componentsHealthTone } from './deriveKpiTone'

describe('componentsHealthTone', () => {
  it('is positive when every component is up', () => {
    expect(componentsHealthTone(3, 3)).toBe('positive')
  })

  it('is negative when at least one component is not up', () => {
    expect(componentsHealthTone(2, 3)).toBe('negative')
  })

  it('is neutral for the explicit empty-input case (no components at all)', () => {
    expect(componentsHealthTone(0, 0)).toBe('neutral')
  })
})

describe('approvalsTone', () => {
  it('is accent when at least one approval is pending', () => {
    expect(approvalsTone(1)).toBe('accent')
  })

  it('is neutral when there is nothing pending', () => {
    expect(approvalsTone(0)).toBe('neutral')
  })
})
