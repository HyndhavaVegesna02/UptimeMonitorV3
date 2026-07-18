import { describe, expect, it } from 'vitest'
import { latencyTone } from './latencyTone'

describe('latencyTone (STORY-108 AC2 — named-token latency threshold tint)', () => {
  it('renders no tone for a null latency (no measurement) — never a fabricated tint', () => {
    expect(latencyTone(null)).toBeNull()
  })

  it('classifies a fast reading (< 500ms) as muted', () => {
    expect(latencyTone(0)).toBe('muted')
    expect(latencyTone(499)).toBe('muted')
  })

  it('classifies exactly the 500ms boundary as warn (the 500-1000ms band is inclusive of its lower edge)', () => {
    expect(latencyTone(500)).toBe('warn')
  })

  it('classifies a mid-band reading as warn', () => {
    expect(latencyTone(750)).toBe('warn')
  })

  it('classifies exactly the 1000ms boundary as warn (the 500-1000ms band is inclusive of its upper edge)', () => {
    expect(latencyTone(1000)).toBe('warn')
  })

  it('classifies anything over 1000ms as high', () => {
    expect(latencyTone(1001)).toBe('high')
    expect(latencyTone(5000)).toBe('high')
  })
})
