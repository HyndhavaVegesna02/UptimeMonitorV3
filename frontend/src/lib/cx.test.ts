import { describe, expect, it } from 'vitest'
import { cx } from './cx'

describe('cx', () => {
  it('joins truthy classnames with a space', () => {
    expect(cx('button', 'button--primary')).toBe('button button--primary')
  })

  it('filters out falsy values', () => {
    expect(cx('button', undefined, null, false, '')).toBe('button')
  })

  it('returns an empty string when given no truthy parts', () => {
    expect(cx()).toBe('')
    expect(cx(undefined, null, false, '')).toBe('')
  })
})
