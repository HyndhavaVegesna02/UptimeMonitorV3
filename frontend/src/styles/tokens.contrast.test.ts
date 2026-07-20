import { readFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'
import { contrastRatio } from './contrastRatio'
import { parseTokenDeclarations, resolveToken } from './parseTokens'

const WCAG_AA_TEXT = 4.5

const tokensPath = resolve(dirname(fileURLToPath(import.meta.url)), 'tokens.css')
const tokensCss = readFileSync(tokensPath, 'utf-8')
const tokens = parseTokenDeclarations(tokensCss)

function resolvedHex(name: string): string {
  return resolveToken(tokens, name)
}

/**
 * Every text-on-surface semantic pair actually used by a component (STORY-120
 * AC3) — computed via WCAG relative luminance directly from the values
 * declared in tokens.css, never eyeballed. Bright brand fills (--color-accent,
 * --color-up, etc.) are excluded on purpose: they are fill/stroke-only tokens,
 * never used for text (round-2-refimg-system.md).
 */
const TEXT_ON_SURFACE_PAIRS: Array<[text: string, surface: string, label: string]> = [
  ['color-text', 'color-surface', 'body text on surface'],
  ['color-text', 'color-canvas', 'body text on canvas'],
  ['color-text-secondary', 'color-surface', 'secondary text on surface'],
  ['color-text-muted', 'color-surface', 'muted text on surface'],
  ['color-accent-text', 'color-surface', 'accent text on surface'],
  ['color-accent-text', 'color-accent-tint', 'accent text on accent tint'],
  ['color-pos-text', 'color-pos-tint', 'positive text on positive tint'],
  ['color-neg-text', 'color-neg-tint', 'negative text on negative tint'],
  ['color-up-text', 'color-up-tint', 'up-health text on up tint'],
  ['color-degraded-text', 'color-degraded-tint', 'degraded-health text on degraded tint'],
  ['color-partial-text', 'color-partial-tint', 'partial-health text on partial tint'],
  ['color-down-text', 'color-down-tint', 'down-health text on down tint'],
  [
    'color-maintenance-text',
    'color-maintenance-tint',
    'maintenance-health text on maintenance tint',
  ],
  ['color-unknown-text', 'color-unknown-tint', 'unknown-health text on unknown tint'],
  ['color-missing-text', 'color-missing-tint', 'missing-health text on missing tint'],
]

describe('tokens.css contrast (WCAG AA, >=4.5:1)', () => {
  it.each(TEXT_ON_SURFACE_PAIRS)('%s on %s (%s) meets AA', (textToken, surfaceToken) => {
    const ratio = contrastRatio(resolvedHex(textToken), resolvedHex(surfaceToken))
    expect(ratio).toBeGreaterThanOrEqual(WCAG_AA_TEXT)
  })
})
