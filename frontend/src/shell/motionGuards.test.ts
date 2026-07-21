import { readFileSync, readdirSync } from 'node:fs'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'

const shellDir = resolve(dirname(fileURLToPath(import.meta.url)))

function collectCssFiles(dir: string): string[] {
  const entries = readdirSync(dir, { withFileTypes: true })
  const files: string[] = []
  for (const entry of entries) {
    const fullPath = join(dir, entry.name)
    if (entry.isDirectory()) {
      files.push(...collectCssFiles(fullPath))
    } else if (entry.name.endsWith('.css')) {
      files.push(fullPath)
    }
  }
  return files
}

const cssFiles = collectCssFiles(shellDir)

/**
 * STORY-121 AC7 (motion is first-class): none of the shell's animated CSS
 * ever uses the blanket `transition: all` — emil-design-eng requires every
 * transitioned property to be named explicitly.
 */
describe('shell motion — never `transition: all`', () => {
  it('found the shell CSS files to check (sanity check)', () => {
    expect(cssFiles.length).toBeGreaterThan(0)
  })

  it.each(cssFiles)('%s never declares `transition: all`', (filePath) => {
    const contents = readFileSync(filePath, 'utf-8')
    expect(contents).not.toMatch(/transition:\s*all\b/)
  })
})

/**
 * The three signature motions this story adds (AC7) — the desktop rail
 * width/label collapse and the mobile sheet's transform — must each be
 * guarded by `prefers-reduced-motion: no-preference`, so reduced-motion
 * users still get the state change, just without the animated movement.
 */
describe('shell motion — reduced-motion guards on transform/width transitions', () => {
  it('Sidebar.css guards the rail width transition', () => {
    const css = readFileSync(join(shellDir, 'Sidebar/Sidebar.css'), 'utf-8')
    expect(css).toMatch(/@media \(prefers-reduced-motion: no-preference\)[\s\S]*width var\(--duration-drawer\)/)
  })

  it('Sidebar.css guards the mobile sheet transform transition', () => {
    const css = readFileSync(join(shellDir, 'Sidebar/Sidebar.css'), 'utf-8')
    expect(css).toMatch(
      /@media \(prefers-reduced-motion: no-preference\)[\s\S]*transition:\s*transform var\(--duration-drawer\)/,
    )
  })

  it('Sidebar.css hides the closed mobile sheet from Tab order (visibility, not just off-screen transform)', () => {
    const css = readFileSync(join(shellDir, 'Sidebar/Sidebar.css'), 'utf-8')
    expect(css).toMatch(/visibility:\s*hidden/)
    expect(css).toMatch(/\.shell-sidebar--mobile-open\s*\{[^}]*visibility:\s*visible/)
  })

  it('Sidebar.css guards the group-label opacity+transform collapse', () => {
    const css = readFileSync(join(shellDir, 'Sidebar/Sidebar.css'), 'utf-8')
    expect(css).toMatch(/@media \(prefers-reduced-motion: no-preference\)[\s\S]*shell-sidebar__group-label/)
  })

  it('NavItem.css guards the rail label/badge opacity+transform+max-width collapse', () => {
    const css = readFileSync(join(shellDir, 'Sidebar/NavItem.css'), 'utf-8')
    expect(css).toMatch(
      /@media \(prefers-reduced-motion: no-preference\)[\s\S]*nav-item__label,\s*\n\s*\.nav-item__badge/,
    )
  })
})
