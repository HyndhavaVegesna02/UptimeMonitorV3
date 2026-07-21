import { readFileSync, readdirSync } from 'node:fs'
import { dirname, join, relative, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'

const srcDir = resolve(dirname(fileURLToPath(import.meta.url)), '..')

/** Only `tokens.css` (the primitive layer itself) may declare/reference a
 * primitive token by name — every other stylesheet must go through a
 * semantic (or component) alias (STORY-120 AC2/AC4, "three-layer" review
 * fix). Primitive families, from tokens.css's own primitive-layer block. */
const PRIMITIVE_VAR_RE =
  /var\(--(white|grey-[a-z0-9-]+|sky-[a-z0-9-]+|green-[a-z0-9-]+|red-[a-z0-9-]+|amber-[a-z0-9-]+|violet-[a-z0-9-]+|orange-[a-z0-9-]+|indigo-[a-z0-9-]+)\)/

const ALLOWED_FILES = new Set(['styles/tokens.css'])

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

describe('no primitive-token references outside tokens.css', () => {
  const files = collectCssFiles(srcDir)

  it('found at least one .css file to check (sanity check)', () => {
    expect(files.length).toBeGreaterThan(0)
  })

  it.each(files)('%s references only semantic/component tokens, never a primitive', (filePath) => {
    const relPath = relative(srcDir, filePath).replaceAll('\\', '/')
    if (ALLOWED_FILES.has(relPath)) {
      return
    }
    const contents = readFileSync(filePath, 'utf-8')
    const match = contents.match(PRIMITIVE_VAR_RE)
    expect(match, `unexpected primitive reference var(--${match?.[1]}) in ${relPath}`).toBeNull()
  })
})
