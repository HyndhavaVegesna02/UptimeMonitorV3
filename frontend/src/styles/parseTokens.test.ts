import { describe, expect, it } from 'vitest'
import { parseTokenDeclarations, resolveToken } from './parseTokens'

describe('parseTokenDeclarations', () => {
  it('extracts custom property name/value pairs from CSS text', () => {
    const css = `:root { --white: #ffffff; --grey-900: #17191e; }`
    const map = parseTokenDeclarations(css)
    expect(map.get('white')).toBe('#ffffff')
    expect(map.get('grey-900')).toBe('#17191e')
  })

  it('reads declarations across multiple selector blocks', () => {
    const css = `
      :root { --white: #ffffff; }
      [data-theme='light'] { --color-text: var(--grey-900); --grey-900: #17191e; }
    `
    const map = parseTokenDeclarations(css)
    expect(map.get('color-text')).toBe('var(--grey-900)')
  })
})

describe('resolveToken', () => {
  it('returns a literal value directly', () => {
    const map = new Map([['white', '#ffffff']])
    expect(resolveToken(map, 'white')).toBe('#ffffff')
  })

  it('follows a single var() reference to its literal value', () => {
    const map = new Map([
      ['color-text', 'var(--grey-900)'],
      ['grey-900', '#17191e'],
    ])
    expect(resolveToken(map, 'color-text')).toBe('#17191e')
  })

  it('follows a chain of var() references', () => {
    const map = new Map([
      ['color-accent-text', 'var(--sky-text)'],
      ['sky-text', '#10709e'],
    ])
    expect(resolveToken(map, 'color-accent-text')).toBe('#10709e')
  })

  it('throws a named error on an unknown token', () => {
    const map = new Map([['white', '#ffffff']])
    expect(() => resolveToken(map, 'nope')).toThrow(/unknown token/i)
  })

  it('throws a named error on a circular reference', () => {
    const map = new Map([
      ['a', 'var(--b)'],
      ['b', 'var(--a)'],
    ])
    expect(() => resolveToken(map, 'a')).toThrow(/circular/i)
  })
})
