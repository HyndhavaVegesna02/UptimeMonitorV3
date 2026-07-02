import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { LoadingState } from './LoadingState'

describe('LoadingState', () => {
  it('announces loading via an accessible status region with a default label', () => {
    render(<LoadingState />)
    expect(screen.getByRole('status')).toHaveTextContent('Loading…')
  })

  it('accepts a custom label', () => {
    render(<LoadingState label="Loading components…" />)
    expect(screen.getByRole('status')).toHaveTextContent(
      'Loading components…',
    )
  })
})
