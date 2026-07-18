import { beforeEach, describe, expect, it } from 'vitest'
import {
  THEME_STORAGE_KEY,
  getStoredTheme,
  persistTheme,
  resolveInitialTheme,
} from './resolveTheme'

/**
 * STORY-103 reality-gate correction (2026-07-18): the precedence is now
 * STORED CHOICE > DARK, period. The OS `prefers-color-scheme` is NEVER
 * consulted for the initial theme — most headless/desktop systems report
 * `light` by default, which would make the common first impression light
 * and defeat the brief's dark-first mission-control identity; the user's
 * own explicit toggle (persisted) is the only thing that can ever move the
 * app to light. These tests deliberately do NOT stub `matchMedia` at all
 * (no `getSystemTheme` export remains) to prove the resolution never reads
 * it.
 */
describe('resolveTheme', () => {
  beforeEach(() => {
    window.localStorage.clear()
  })

  it('resolves to dark when nothing is stored', () => {
    expect(resolveInitialTheme()).toBe('dark')
  })

  it('a stored "light" choice resolves to light', () => {
    window.localStorage.setItem(THEME_STORAGE_KEY, 'light')
    expect(resolveInitialTheme()).toBe('light')
  })

  it('a stored "dark" choice resolves to dark', () => {
    window.localStorage.setItem(THEME_STORAGE_KEY, 'dark')
    expect(resolveInitialTheme()).toBe('dark')
  })

  it('ignores a corrupt stored value and falls back to dark', () => {
    window.localStorage.setItem(THEME_STORAGE_KEY, 'not-a-theme')
    expect(resolveInitialTheme()).toBe('dark')
    expect(getStoredTheme()).toBeNull()
  })

  it('persistTheme writes a valid theme to storage under the shared key', () => {
    persistTheme('dark')
    expect(window.localStorage.getItem(THEME_STORAGE_KEY)).toBe('dark')
  })

  it('persistTheme(light) then resolveInitialTheme reflects it', () => {
    persistTheme('light')
    expect(resolveInitialTheme()).toBe('light')
  })
})
