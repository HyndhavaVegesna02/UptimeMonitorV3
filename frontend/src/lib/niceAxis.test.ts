import { describe, expect, it } from 'vitest'
import { computeNiceAxis } from './niceAxis'

describe('computeNiceAxis', () => {
  it('always starts at a 0 baseline, never the data minimum', () => {
    const axis = computeNiceAxis(951, 4)
    expect(axis.ticks[0]).toBe(0)
  })

  it('rounds the max up to a "nice" round step (real captured sample, max 951ms)', () => {
    // Real captured max from live-api-samples.md (STORY-122 fixture), never invented.
    const axis = computeNiceAxis(951, 4)
    expect(axis.step).toBe(500)
    expect(axis.niceMax).toBe(1500)
    expect(axis.ticks).toEqual([0, 500, 1000, 1500])
  })

  it('produces a 0/250/500/750-style axis for a value that lands on the 2.5x-step band', () => {
    const axis = computeNiceAxis(700, 4)
    expect(axis.step).toBe(250)
    expect(axis.niceMax).toBe(750)
    expect(axis.ticks).toEqual([0, 250, 500, 750])
  })

  it('the niced max always covers the real max (never clips the plotted data)', () => {
    for (const maxValue of [1, 7, 99, 317, 951, 1082, 4200, 9999]) {
      const axis = computeNiceAxis(maxValue, 4)
      expect(axis.niceMax).toBeGreaterThanOrEqual(maxValue)
    }
  })

  it('handles an all-zero / empty data max without dividing by zero', () => {
    const axis = computeNiceAxis(0, 4)
    expect(axis.niceMax).toBe(0)
    expect(axis.step).toBe(0)
    expect(axis.ticks).toEqual([0, 0, 0, 0])
  })

  it('respects an arbitrary tick count', () => {
    const axis = computeNiceAxis(951, 5)
    expect(axis.ticks).toHaveLength(5)
    expect(axis.ticks[0]).toBe(0)
    expect(axis.ticks[4]).toBe(axis.niceMax)
  })
})
