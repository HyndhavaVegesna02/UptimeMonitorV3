import { readFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { LoadingState } from './LoadingState'

const loadingCss = readFileSync(
  resolve(dirname(fileURLToPath(import.meta.url)), 'LoadingState.css'),
  'utf-8',
)

describe('LoadingState', () => {
  it('announces via role="status" with a default label', () => {
    render(<LoadingState />)
    expect(screen.getByRole('status')).toHaveTextContent('Loading…')
  })

  it('accepts a custom label', () => {
    render(<LoadingState label="Loading components…" />)
    expect(screen.getByRole('status')).toHaveTextContent('Loading components…')
  })

  it('the spinner is decorative', () => {
    const { container } = render(<LoadingState />)
    expect(container.querySelector('.loading-state__spinner')).toHaveAttribute(
      'aria-hidden',
      'true',
    )
  })

  it('the spin animation is guarded by prefers-reduced-motion and rotates transform only', () => {
    expect(loadingCss).toMatch(/@media \(prefers-reduced-motion: no-preference\)/)
    expect(loadingCss).toMatch(/transform:\s*rotate/)
  })
})
