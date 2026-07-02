import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  THEME_STORAGE_KEY,
  getStoredTheme,
  persistTheme,
  resolveInitialTheme,
} from './resolveTheme'

function mockMatchMedia(prefersDark: boolean) {
  vi.stubGlobal(
    'matchMedia',
    vi.fn().mockImplementation((query: string) => ({
      matches: query === '(prefers-color-scheme: dark)' && prefersDark,
      media: query,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    })),
  )
}

describe('resolveTheme', () => {
  beforeEach(() => {
    window.localStorage.clear()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('resolves to the system-preferred theme when nothing is stored (dark)', () => {
    mockMatchMedia(true)
    expect(resolveInitialTheme()).toBe('dark')
  })

  it('resolves to the system-preferred theme when nothing is stored (light)', () => {
    mockMatchMedia(false)
    expect(resolveInitialTheme()).toBe('light')
  })

  it('prefers a stored override over the system preference', () => {
    mockMatchMedia(true)
    window.localStorage.setItem(THEME_STORAGE_KEY, 'light')
    expect(resolveInitialTheme()).toBe('light')
  })

  it('ignores a corrupt stored value and falls back to system preference', () => {
    mockMatchMedia(false)
    window.localStorage.setItem(THEME_STORAGE_KEY, 'not-a-theme')
    expect(resolveInitialTheme()).toBe('light')
    expect(getStoredTheme()).toBeNull()
  })

  it('persistTheme writes a valid theme to storage under the shared key', () => {
    persistTheme('dark')
    expect(window.localStorage.getItem(THEME_STORAGE_KEY)).toBe('dark')
  })
})
