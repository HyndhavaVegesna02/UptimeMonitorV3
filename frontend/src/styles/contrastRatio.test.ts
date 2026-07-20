import { describe, expect, it } from 'vitest'
import { contrastRatio } from './contrastRatio'

describe('contrastRatio', () => {
  it('is 21:1 for black on white (the maximum possible ratio)', () => {
    expect(contrastRatio('#000000', '#ffffff')).toBeCloseTo(21, 1)
  })

  it('is 1:1 for identical colors', () => {
    expect(contrastRatio('#2e9fd6', '#2e9fd6')).toBeCloseTo(1, 5)
  })

  it('is symmetric — order of the two colors does not matter', () => {
    const a = contrastRatio('#17191e', '#ffffff')
    const b = contrastRatio('#ffffff', '#17191e')
    expect(a).toBeCloseTo(b, 10)
  })

  it('matches a known WCAG reference ratio (#767676 on #ffffff ~= 4.54:1)', () => {
    expect(contrastRatio('#767676', '#ffffff')).toBeCloseTo(4.54, 1)
  })

  it('accepts 3-digit shorthand hex', () => {
    expect(contrastRatio('#000', '#fff')).toBeCloseTo(21, 1)
  })
})
