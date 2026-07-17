import { act, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { RelativeTime } from './RelativeTime'

const ISO = '2026-07-17T11:56:00.000Z'

describe('RelativeTime', () => {
  afterEach(() => {
    vi.useRealTimers()
  })

  it('renders a <time dateTime> carrying the raw ISO instant, with the relative text as content (AC1, AC2)', () => {
    const now = () => new Date('2026-07-17T12:00:00.000Z')
    render(<RelativeTime iso={ISO} now={now} />)

    const time = screen.getByText('4m ago')
    expect(time.tagName).toBe('TIME')
    expect(time).toHaveAttribute('dateTime', ISO)
  })

  it('carries the absolute-local + raw-UTC tooltip in `title` (AC1)', () => {
    const now = () => new Date('2026-07-17T12:00:00.000Z')
    render(<RelativeTime iso={ISO} now={now} />)

    const time = screen.getByText('4m ago')
    expect(time.getAttribute('title')).toContain(new Date(ISO).toISOString())
  })

  it('passes through a className (e.g. the shared mono token) (D3 — tabular figures)', () => {
    const now = () => new Date('2026-07-17T12:00:00.000Z')
    render(<RelativeTime iso={ISO} now={now} className="text-mono" />)

    expect(screen.getByText('4m ago')).toHaveClass('text-mono')
  })

  it('updates at least once a minute while mounted (AC2)', () => {
    vi.useFakeTimers()
    let current = new Date('2026-07-17T12:00:00.000Z')
    render(<RelativeTime iso={ISO} now={() => current} />)

    expect(screen.getByText('4m ago')).toBeInTheDocument()

    // Advance both the injected clock and real time together, then let the
    // minute-tick interval fire.
    current = new Date(current.getTime() + 60_000)
    act(() => {
      vi.advanceTimersByTime(60_000)
    })

    expect(screen.getByText('5m ago')).toBeInTheDocument()
  })

  it('never crashes on invalid input — renders the raw string as the time content', () => {
    const now = () => new Date('2026-07-17T12:00:00.000Z')
    render(<RelativeTime iso="not-a-date" now={now} />)

    expect(screen.getByText('not-a-date')).toBeInTheDocument()
  })
})
