import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

/**
 * Token-level contract tests for the Mission Teal design system v2
 * (STORY-103 AC1/AC2/AC3). Reads the raw CSS text (not jsdom computed
 * style — jsdom's CSS engine does not reliably cascade custom properties
 * through attribute-selector scoping) so these assertions are exact and
 * deterministic regardless of the test DOM environment.
 */

const TOKENS_CSS = readFileSync(resolve(__dirname, './tokens.css'), 'utf-8')
const GLOBAL_CSS = readFileSync(resolve(__dirname, './global.css'), 'utf-8')

function extractBlock(css: string, selector: string): string {
  const escaped = selector.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  const match = css.match(new RegExp(`${escaped}\\s*\\{([^}]*)\\}`))
  if (!match) {
    throw new Error(`selector block not found: ${selector}`)
  }
  return match[1]
}

/** The bare `:root { ... }` block (the theme-independent shared tokens) —
 * distinct from `:root, :root[data-theme='dark'] { ... }` and
 * `:root[data-theme='light'] { ... }` because nothing but whitespace
 * follows `:root` before the opening brace. */
function extractSharedRootBlock(css: string): string {
  const match = css.match(/:root\s*\{([^}]*)\}/)
  if (!match) {
    throw new Error('shared :root block not found')
  }
  return match[1]
}

function extractVar(block: string, name: string): string {
  const match = block.match(new RegExp(`${name}:\\s*([^;]+);`))
  if (!match) {
    throw new Error(`variable not found in block: ${name}`)
  }
  return match[1].trim()
}

function hexToRgb(hex: string): [number, number, number] {
  const clean = hex.replace('#', '')
  const r = parseInt(clean.slice(0, 2), 16)
  const g = parseInt(clean.slice(2, 4), 16)
  const b = parseInt(clean.slice(4, 6), 16)
  return [r, g, b]
}

function linearize(channel: number): number {
  const c = channel / 255
  return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4
}

function relativeLuminance(hex: string): number {
  const [r, g, b] = hexToRgb(hex)
  return 0.2126 * linearize(r) + 0.7152 * linearize(g) + 0.0722 * linearize(b)
}

/** WCAG 2.x contrast ratio between two sRGB hex colors. */
function contrastRatio(hexA: string, hexB: string): number {
  const lumA = relativeLuminance(hexA)
  const lumB = relativeLuminance(hexB)
  const lighter = Math.max(lumA, lumB)
  const darker = Math.min(lumA, lumB)
  return (lighter + 0.05) / (darker + 0.05)
}

const DARK_ROOT = extractBlock(TOKENS_CSS, ":root,\n:root[data-theme='dark']")
const LIGHT = extractBlock(TOKENS_CSS, ":root[data-theme='light']")
const SHARED = extractSharedRootBlock(TOKENS_CSS)

describe('contrastRatio (self-test of the WCAG formula)', () => {
  it('rates pure black on pure white as the maximum 21:1', () => {
    expect(contrastRatio('#000000', '#ffffff')).toBeCloseTo(21, 0)
  })

  it('rates identical colors as 1:1', () => {
    expect(contrastRatio('#123456', '#123456')).toBeCloseTo(1, 5)
  })
})

describe('tokens.css v2 — Mission Teal identity (AC1)', () => {
  it('scopes the dark theme as the default (:root AND [data-theme="dark"]) with the deep-space canvas', () => {
    expect(extractVar(DARK_ROOT, '--color-canvas').toLowerCase()).toBe('#0a0e14')
  })

  it('scopes the light theme with the mint-tinted canvas', () => {
    expect(extractVar(LIGHT, '--color-canvas').toLowerCase()).toBe('#f0fdfa')
  })

  it('defines the teal primary accent in dark (teal-500 family)', () => {
    expect(extractVar(DARK_ROOT, '--color-accent').toLowerCase()).toBe('#14b8a6')
  })

  it('defines the teal-700 on-light-contrast accent in light', () => {
    expect(extractVar(LIGHT, '--color-accent').toLowerCase()).toBe('#0f766e')
  })

  it('defines a rounded-xl (16px) tile radius', () => {
    expect(extractVar(SHARED, '--radius-tile')).toBe('16px')
  })
})

describe('tokens.css v2 — motion tokens are 150-250ms and reduced-motion-guardable (Identity: Motion)', () => {
  it.each(['--motion-fast', '--motion-base', '--motion-slow'])(
    '%s is within the 150-250ms band',
    (name) => {
      const raw = extractVar(SHARED, name)
      const ms = Number(raw.replace('ms', ''))
      expect(ms).toBeGreaterThanOrEqual(150)
      expect(ms).toBeLessThanOrEqual(250)
    },
  )
})

describe('global.css — self-hosted fonts, no Google-CDN (AC2)', () => {
  it('imports Space Grotesk (headings), Inter (body), JetBrains Mono (data) via @fontsource', () => {
    expect(GLOBAL_CSS).toMatch(/@import\s+'@fontsource\/space-grotesk/)
    expect(GLOBAL_CSS).toMatch(/@import\s+'@fontsource\/inter/)
    expect(GLOBAL_CSS).toMatch(/@import\s+'@fontsource\/jetbrains-mono/)
  })

  it('never imports a runtime Google Fonts CDN link', () => {
    expect(GLOBAL_CSS).not.toMatch(/fonts\.googleapis\.com/)
    expect(GLOBAL_CSS).not.toMatch(/fonts\.gstatic\.com/)
  })

  it('guards animation/transition with prefers-reduced-motion', () => {
    expect(GLOBAL_CSS).toMatch(/prefers-reduced-motion:\s*reduce/)
  })
})

describe('tokens.css v2 — font family tokens (AC2)', () => {
  it('assigns Space Grotesk to --font-heading', () => {
    expect(extractVar(SHARED, '--font-heading')).toMatch(/Space Grotesk/)
  })

  it('assigns Inter to --font-sans (body)', () => {
    expect(extractVar(SHARED, '--font-sans')).toMatch(/Inter/)
  })

  it('assigns JetBrains Mono to --font-mono (data)', () => {
    expect(extractVar(SHARED, '--font-mono')).toMatch(/JetBrains Mono/)
  })
})

describe('tokens.css v2 — StatusBadge label contrast >= 4.5:1 in BOTH themes (AC3)', () => {
  it('dark: --color-ink-muted (the badge label color) against the two badge-hosting surfaces', () => {
    const inkMuted = extractVar(DARK_ROOT, '--color-ink-muted')
    const canvas = extractVar(DARK_ROOT, '--color-canvas')
    const surface1 = extractVar(DARK_ROOT, '--color-surface-1')
    expect(contrastRatio(inkMuted, canvas)).toBeGreaterThanOrEqual(4.5)
    expect(contrastRatio(inkMuted, surface1)).toBeGreaterThanOrEqual(4.5)
  })

  it('light: --color-ink-muted (the badge label color) against the two badge-hosting surfaces', () => {
    const inkMuted = extractVar(LIGHT, '--color-ink-muted')
    const canvas = extractVar(LIGHT, '--color-canvas')
    const surface1 = extractVar(LIGHT, '--color-surface-1')
    expect(contrastRatio(inkMuted, canvas)).toBeGreaterThanOrEqual(4.5)
    expect(contrastRatio(inkMuted, surface1)).toBeGreaterThanOrEqual(4.5)
  })

  it.each([
    'up',
    'degraded',
    'partial',
    'down',
    'maintenance',
    'unknown',
    'missing',
  ])('dark: health-%s dot color holds >= 4.5:1 against the canvas', (status) => {
    const color = extractVar(DARK_ROOT, `--color-health-${status}`)
    const canvas = extractVar(DARK_ROOT, '--color-canvas')
    expect(contrastRatio(color, canvas)).toBeGreaterThanOrEqual(4.5)
  })

  it.each([
    'up',
    'degraded',
    'partial',
    'down',
    'maintenance',
    'unknown',
    'missing',
  ])('light: health-%s dot color holds >= 4.5:1 against the canvas', (status) => {
    const color = extractVar(LIGHT, `--color-health-${status}`)
    const canvas = extractVar(LIGHT, '--color-canvas')
    expect(contrastRatio(color, canvas)).toBeGreaterThanOrEqual(4.5)
  })
})

describe('tokens.css v2 — on-accent text holds contrast against the accent background (buttons)', () => {
  it('dark: --color-on-accent against --color-accent', () => {
    const onAccent = extractVar(DARK_ROOT, '--color-on-accent')
    const accent = extractVar(DARK_ROOT, '--color-accent')
    expect(contrastRatio(onAccent, accent)).toBeGreaterThanOrEqual(4.5)
  })

  it('light: --color-on-accent against --color-accent', () => {
    const onAccent = extractVar(LIGHT, '--color-on-accent')
    const accent = extractVar(LIGHT, '--color-accent')
    expect(contrastRatio(onAccent, accent)).toBeGreaterThanOrEqual(4.5)
  })
})

describe('tokens.css v2 — every kept token name required by existing (non-rewritten) primitives is still defined', () => {
  const requiredSharedNames = [
    '--radius-control',
    '--radius-panel',
    '--radius-pill',
    '--target-min',
    '--focus-ring',
    '--fs-h1',
    '--fs-h2',
    '--fs-h3',
    '--fs-body',
    '--fs-body-lg',
    '--fs-caption',
    '--fs-button',
    '--fs-mono',
    '--fs-label',
    '--fs-stat',
    '--space-1',
    '--space-2',
    '--space-3',
    '--space-4',
    '--space-6',
  ]

  it.each(requiredSharedNames)('%s is defined in the shared :root block', (name) => {
    expect(() => extractVar(SHARED, name)).not.toThrow()
  })

  const requiredPerThemeNames = [
    '--color-surface-1',
    '--color-surface-2',
    '--color-surface-3',
    '--color-hairline',
    '--color-hairline-strong',
    '--color-ink',
    '--color-ink-muted',
    '--color-ink-subtle',
    '--color-ink-tertiary',
    '--color-accent-hover',
    '--color-accent-focus',
    '--color-accent-bg',
    '--shadow',
    '--color-health-up-subtle',
    '--color-health-degraded-subtle',
    '--color-health-partial-subtle',
    '--color-health-down-subtle',
    '--color-health-maintenance-subtle',
    '--color-health-unknown-subtle',
    '--color-health-missing-subtle',
  ]

  it.each(requiredPerThemeNames)('%s is defined in BOTH theme blocks', (name) => {
    expect(() => extractVar(DARK_ROOT, name)).not.toThrow()
    expect(() => extractVar(LIGHT, name)).not.toThrow()
  })
})
