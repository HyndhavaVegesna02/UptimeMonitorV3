import { act, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { stubMatchMedia } from '../test/matchMedia'
import { useMediaQuery } from './useMediaQuery'

const QUERY = '(max-width: 768px)'

function Harness({ query }: { query: string }) {
  const matches = useMediaQuery(query)
  return <p>matches: {String(matches)}</p>
}

describe('useMediaQuery', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('reflects the initial matchMedia() result for the given query', () => {
    stubMatchMedia({ [QUERY]: true })
    render(<Harness query={QUERY} />)
    expect(screen.getByText('matches: true')).toBeInTheDocument()
  })

  it('defaults to false when the query does not currently match', () => {
    stubMatchMedia({ [QUERY]: false })
    render(<Harness query={QUERY} />)
    expect(screen.getByText('matches: false')).toBeInTheDocument()
  })

  it('updates live when the query transitions via a change event', () => {
    const media = stubMatchMedia({ [QUERY]: false })
    render(<Harness query={QUERY} />)
    expect(screen.getByText('matches: false')).toBeInTheDocument()

    act(() => {
      media.setMatches(QUERY, true)
    })

    expect(screen.getByText('matches: true')).toBeInTheDocument()
  })

  it('re-subscribes when the query string itself changes', () => {
    const media = stubMatchMedia({
      '(max-width: 768px)': false,
      '(max-width: 1024px)': true,
    })
    const { rerender } = render(<Harness query="(max-width: 768px)" />)
    expect(screen.getByText('matches: false')).toBeInTheDocument()

    rerender(<Harness query="(max-width: 1024px)" />)
    expect(screen.getByText('matches: true')).toBeInTheDocument()

    act(() => {
      media.setMatches('(max-width: 1024px)', false)
    })
    expect(screen.getByText('matches: false')).toBeInTheDocument()
  })
})
