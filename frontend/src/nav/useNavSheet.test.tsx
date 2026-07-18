import { act, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { QUERY_MOBILE_DOWN } from '../lib/breakpoints'
import { stubMatchMedia } from '../test/matchMedia'
import { useNavSheet } from './useNavSheet'

function Harness() {
  const { isMobile, open, openSheet, closeSheet } = useNavSheet()
  return (
    <div>
      <p>isMobile: {String(isMobile)}</p>
      <p>open: {String(open)}</p>
      <button onClick={openSheet}>open sheet</button>
      <button onClick={closeSheet}>close sheet</button>
    </div>
  )
}

describe('useNavSheet (STORY-104 AC4)', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('reports isMobile false and starts closed at desktop widths', () => {
    stubMatchMedia({ [QUERY_MOBILE_DOWN]: false })
    render(<Harness />)
    expect(screen.getByText('isMobile: false')).toBeInTheDocument()
    expect(screen.getByText('open: false')).toBeInTheDocument()
  })

  it('reports isMobile true at <=768px, starting closed', () => {
    stubMatchMedia({ [QUERY_MOBILE_DOWN]: true })
    render(<Harness />)
    expect(screen.getByText('isMobile: true')).toBeInTheDocument()
    expect(screen.getByText('open: false')).toBeInTheDocument()
  })

  it('opens and closes via openSheet/closeSheet', async () => {
    const user = userEvent.setup()
    stubMatchMedia({ [QUERY_MOBILE_DOWN]: true })
    render(<Harness />)

    await user.click(screen.getByRole('button', { name: 'open sheet' }))
    expect(screen.getByText('open: true')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'close sheet' }))
    expect(screen.getByText('open: false')).toBeInTheDocument()
  })

  it('closes an open sheet automatically when the viewport widens past the mobile breakpoint', async () => {
    const user = userEvent.setup()
    const media = stubMatchMedia({ [QUERY_MOBILE_DOWN]: true })
    render(<Harness />)

    await user.click(screen.getByRole('button', { name: 'open sheet' }))
    expect(screen.getByText('open: true')).toBeInTheDocument()

    act(() => {
      media.setMatches(QUERY_MOBILE_DOWN, false)
    })

    expect(screen.getByText('open: false')).toBeInTheDocument()
  })
})
