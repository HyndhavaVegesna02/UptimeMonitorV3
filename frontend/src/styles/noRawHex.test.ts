import { readFileSync, readdirSync } from 'node:fs'
import { dirname, join, relative, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'

const HEX_RE = /#[0-9a-fA-F]{3,8}\b/

const srcDir = resolve(dirname(fileURLToPath(import.meta.url)), '..')

/** `tokens.css` IS the primitive layer — the one file allowed to declare raw
 * hex literals (STORY-120 AC2). Everything else must consume `var(--…)`. */
const ALLOWED_RAW_HEX_FILES = new Set(['styles/tokens.css'])

function isCheckedFile(fileName: string): boolean {
  const isStyleOrComponent = fileName.endsWith('.css') || fileName.endsWith('.tsx')
  const isTest = fileName.includes('.test.')
  return isStyleOrComponent && !isTest
}

function collectFiles(dir: string): string[] {
  const entries = readdirSync(dir, { withFileTypes: true })
  const files: string[] = []
  for (const entry of entries) {
    const fullPath = join(dir, entry.name)
    if (entry.isDirectory()) {
      files.push(...collectFiles(fullPath))
    } else if (isCheckedFile(entry.name)) {
      files.push(fullPath)
    }
  }
  return files
}

describe('no raw hex in component/primitive code', () => {
  const files = collectFiles(srcDir)

  it('found at least one .css/.tsx file to check (sanity check)', () => {
    expect(files.length).toBeGreaterThan(0)
  })

  it.each(files)('%s uses only var(--…) tokens, never a raw hex literal', (filePath) => {
    const relPath = relative(srcDir, filePath).replaceAll('\\', '/')
    if (ALLOWED_RAW_HEX_FILES.has(relPath)) {
      return
    }
    const contents = readFileSync(filePath, 'utf-8')
    const match = contents.match(HEX_RE)
    expect(match, `unexpected raw hex ${match?.[0]} in ${relPath}`).toBeNull()
  })
})
