/**
 * Minimal CSS custom-property parser + `var()` chain resolver (STORY-120
 * AC3). Reads `tokens.css` as plain text — no jsdom/browser cascade — so the
 * contrast test asserts against exactly what ships, independent of any
 * runtime computed-style quirk.
 */

const DECLARATION_RE = /--([a-zA-Z0-9-]+)\s*:\s*([^;]+);/g

/** Extracts every `--name: value;` custom-property declaration in the CSS
 * text into a flat name -> raw-value map (later blocks overwrite earlier
 * ones for the same name, mirroring cascade order for a single-theme file). */
export function parseTokenDeclarations(cssText: string): Map<string, string> {
  const map = new Map<string, string>()
  for (const match of cssText.matchAll(DECLARATION_RE)) {
    map.set(match[1], match[2].trim())
  }
  return map
}

const SINGLE_VAR_RE = /^var\(--([a-zA-Z0-9-]+)\)$/

/** Resolves a token name down through any `var(--other)` chain to its
 * literal value. Throws a named error (never a leaked stdlib message) on an
 * unknown token or a circular reference. */
export function resolveToken(map: Map<string, string>, name: string): string {
  let current = name
  const seen = new Set<string>()

  while (true) {
    if (seen.has(current)) {
      throw new Error(`Circular token reference resolving --${name}`)
    }
    seen.add(current)

    const value = map.get(current)
    if (value === undefined) {
      throw new Error(`Unknown token: --${current}`)
    }

    const varMatch = value.match(SINGLE_VAR_RE)
    if (!varMatch) {
      return value
    }
    current = varMatch[1]
  }
}
