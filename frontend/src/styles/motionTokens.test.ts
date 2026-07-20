import { readFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'
import { parseTokenDeclarations, resolveToken } from './parseTokens'

const tokensPath = resolve(dirname(fileURLToPath(import.meta.url)), 'tokens.css')
const tokensCss = readFileSync(tokensPath, 'utf-8')
const tokens = parseTokenDeclarations(tokensCss)

function msValue(name: string): number {
  const raw = resolveToken(tokens, name)
  const match = raw.match(/^(\d+(?:\.\d+)?)ms$/)
  if (!match) {
    throw new Error(`--${name} is not a plain ms duration: ${raw}`)
  }
  return Number(match[1])
}

/**
 * Motion tokens (STORY-120 AC4, emil-design-eng): custom, "strong" easing
 * curves — never the built-in CSS easings — and short UI durations. Values
 * asserted directly from tokens.css so a future edit can't silently drift
 * off the agreed curves/timings.
 */
describe('motion tokens (emil-design-eng)', () => {
  it('defines the strong custom ease-out curve used for entrances/UI feedback', () => {
    expect(resolveToken(tokens, 'ease-out')).toBe('cubic-bezier(0.23, 1, 0.32, 1)')
  })

  it('defines the strong custom ease-in-out curve used for on-screen movement', () => {
    expect(resolveToken(tokens, 'ease-in-out')).toBe('cubic-bezier(0.77, 0, 0.175, 1)')
  })

  it('defines the iOS-like drawer curve for the sheet/collapse motions (STORY-121)', () => {
    expect(resolveToken(tokens, 'ease-drawer')).toBe('cubic-bezier(0.32, 0.72, 0, 1)')
  })

  it('keeps press feedback under 200ms (AC4)', () => {
    expect(msValue('duration-press')).toBeLessThanOrEqual(200)
  })

  it('keeps standard control transitions under 200ms (AC4)', () => {
    expect(msValue('duration-control')).toBeLessThanOrEqual(200)
  })

  it('allows the drawer/sheet duration up to 250ms (plan.md "Motion is first-class")', () => {
    const drawerMs = msValue('duration-drawer')
    expect(drawerMs).toBeGreaterThanOrEqual(200)
    expect(drawerMs).toBeLessThanOrEqual(250)
  })
})
