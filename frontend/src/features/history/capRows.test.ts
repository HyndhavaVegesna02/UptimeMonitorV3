import { describe, expect, it } from 'vitest'
import { capRows, DEFAULT_RENDER_CAP } from './capRows'

describe('DEFAULT_RENDER_CAP', () => {
  it('defaults to 1000', () => {
    expect(DEFAULT_RENDER_CAP).toBe(1000)
  })
})

describe('capRows', () => {
  it('returns every row untruncated when the total is at or under the cap', () => {
    const rows = Array.from({ length: 5 }, (_, i) => i)
    const result = capRows(rows, 5)
    expect(result).toEqual({ rows, total: 5, truncated: false })
  })

  it('truncates to the cap and reports the real total when over the cap', () => {
    const rows = Array.from({ length: 10 }, (_, i) => i)
    const result = capRows(rows, 3)
    expect(result.rows).toEqual([0, 1, 2])
    expect(result.total).toBe(10)
    expect(result.truncated).toBe(true)
  })

  it('is injectable — a smaller cap can be passed for tests, not hardcoded at 1000', () => {
    const rows = [1, 2, 3]
    expect(capRows(rows, 2).truncated).toBe(true)
  })

  it('handles zero rows without crashing (a real empty-input behavior)', () => {
    expect(capRows([], 1000)).toEqual({ rows: [], total: 0, truncated: false })
  })
})
