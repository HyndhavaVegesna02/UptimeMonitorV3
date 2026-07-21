import { readFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'
import { SIDEBAR_COLLAPSE_STORAGE_KEY } from './useSidebarCollapse'

const indexHtmlPath = resolve(dirname(fileURLToPath(import.meta.url)), '../../index.html')

/**
 * `index.html`'s pre-paint inline script (STORY-121 AC5 — restoring the
 * collapsed choice with no flash) reads the SAME localStorage key
 * `useSidebarCollapse` does. The key is a plain string literal in
 * `index.html` (it isn't processed by the TS build), so this test is what
 * catches the two ever drifting apart.
 */
describe('index.html pre-paint sidebar-collapse script', () => {
  const html = readFileSync(indexHtmlPath, 'utf-8')

  it('reads the exact SIDEBAR_COLLAPSE_STORAGE_KEY used by useSidebarCollapse', () => {
    expect(html).toContain(`localStorage.getItem('${SIDEBAR_COLLAPSE_STORAGE_KEY}')`)
  })

  it('runs before the app module script mounts React', () => {
    const prepaintIndex = html.indexOf('sidebar-collapsed-preload')
    const moduleScriptIndex = html.indexOf('/src/main.tsx')
    expect(prepaintIndex).toBeGreaterThan(-1)
    expect(moduleScriptIndex).toBeGreaterThan(-1)
    expect(prepaintIndex).toBeLessThan(moduleScriptIndex)
  })
})
