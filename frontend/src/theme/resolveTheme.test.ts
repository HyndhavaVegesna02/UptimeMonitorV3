import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  THEME_STORAGE_KEY,
  getStoredTheme,
  getSystemTheme,
  persistTheme,
  resolveInitialTheme,
} from './resolveTheme'

/**
 * STORY-103 (Mission Teal, dark-first): the system-preference query is now
 * explicit on BOTH queries rather than "dark ? dark : light" — a browser
 * that reports neither `(prefers-color-scheme: dark)` NOR
 * `(prefers-color-scheme: light)` as matching (no stated preference,
 * matchMedia unsupported, etc.) falls back to DARK, never light.
 */
type SystemPreference = 'dark' | 'light' | 'no-preference'

function mockMatchMedia(preference: SystemPreference) {
  vi.stubGlobal(
    'matchMedia',
    vi.fn().mockImplementation((query: string) => ({
      matches:
        (query === '(prefers-color-scheme: dark)' && preference === 'dark') ||
        (query === '(prefers-color-scheme: light)' && preference === 'light'),
      media: query,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    })),
  )
}

describe('getSystemTheme', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('resolves dark when the dark media query matches', () => {
    mockMatchMedia('dark')
    expect(getSystemTheme()).toBe('dark')
  })

  it('resolves light when the light media query explicitly matches', () => {
    mockMatchMedia('light')
    expect(getSystemTheme()).toBe('light')
  })

  it('defaults to dark when NEITHER media query matches (dark-first)', () => {
    mockMatchMedia('no-preference')
    expect(getSystemTheme()).toBe('dark')
  })
})

describe('resolveTheme', () => {
  beforeEach(() => {
    window.localStorage.clear()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('resolves to the system-preferred theme when nothing is stored (dark)', () => {
    mockMatchMedia('dark')
    expect(resolveInitialTheme()).toBe('dark')
  })

  it('resolves to the system-preferred theme when nothing is stored (light)', () => {
    mockMatchMedia('light')
    expect(resolveInitialTheme()).toBe('light')
  })

  it('resolves to dark when nothing is stored AND no explicit system preference is reported', () => {
    mockMatchMedia('no-preference')
    expect(resolveInitialTheme()).toBe('dark')
  })

  it('prefers a stored override over the system preference', () => {
    mockMatchMedia('dark')
    window.localStorage.setItem(THEME_STORAGE_KEY, 'light')
    expect(resolveInitialTheme()).toBe('light')
  })

  it('ignores a corrupt stored value and falls back to system preference', () => {
    mockMatchMedia('light')
    window.localStorage.setItem(THEME_STORAGE_KEY, 'not-a-theme')
    expect(resolveInitialTheme()).toBe('light')
    expect(getStoredTheme()).toBeNull()
  })

  it('persistTheme writes a valid theme to storage under the shared key', () => {
    persistTheme('dark')
    expect(window.localStorage.getItem(THEME_STORAGE_KEY)).toBe('dark')
  })
})
